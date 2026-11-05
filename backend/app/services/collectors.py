from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
import hashlib
from typing import Callable
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
import requests
import certifi
import urllib3

from app.config import settings
from app.models import Agency, CollectorRun, utc_now
from app.services.processing import NormalizedNotice, process_snapshot

logger = logging.getLogger("transitnotice.collectors")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
MTC_URL = "https://mtcbus.tn.gov.in/Home/news"
CMRL_URL = "https://chennaimetrorail.org/press-release/"
SOURCE_META = {
    "mtc_chennai": ("Metropolitan Transport Corporation (Chennai)", MTC_URL),
    "cmrl": ("Chennai Metro Rail Limited", CMRL_URL),
}


def _request_json(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    allowed_host: str | None = None,
    verify: bool = True,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(max(1, settings.max_retries)):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers or {},
                timeout=settings.request_timeout_seconds,
                verify=certifi.where() if verify else False,
            )
            if response.status_code == 429 or response.status_code >= 500:
                if attempt + 1 < settings.max_retries:
                    retry_after = response.headers.get("Retry-After", "")
                    try:
                        delay = min(float(retry_after), 30.0)
                    except ValueError:
                        delay = min(2**attempt, 15)
                    time.sleep(delay)
                    continue
            response.raise_for_status()
            if allowed_host and urlparse(response.url).hostname != allowed_host:
                raise ValueError("Source response redirected outside its official host")
            return response
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt + 1 < settings.max_retries:
                time.sleep(min(2**attempt, 15))
    if last_error:
        raise last_error
    raise RuntimeError("Request did not return a response")


def _parse_datetime(value: object, source_timezone: str = "UTC") -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=ZoneInfo(source_timezone)) if parsed.tzinfo is None else parsed
    except ValueError:
        for pattern in ("%Y%m%d %H:%M", "%Y%m%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, pattern).replace(tzinfo=ZoneInfo(source_timezone))
            except ValueError:
                pass
    return None


def _plain_text(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("#cdata-section", value.get("text", ""))
    if not isinstance(value, str):
        return ""
    return " ".join(BeautifulSoup(value, "html.parser").get_text(" ").split())


def _advisory_type(effect: str, cause: str = "") -> str:
    value = (effect + " " + cause).lower()
    if any(word in value for word in ("diversion", "reroute", "detour")):
        return "ROUTE_DIVERSION"
    if any(word in value for word in ("suspend", "shuttle", "closure", "cancel")):
        return "SERVICE_INTERRUPTION"
    if any(word in value for word in ("delay", "slow", "reduced")):
        return "DELAY"
    if any(word in value for word in ("elevator", "accessible", "elevator_outage")):
        return "ACCESSIBILITY"
    if any(word in value for word in ("construction", "planned", "maintenance", "track")):
        return "PLANNED_WORK"
    return "SERVICE_ADVISORY"


def _mbta_records(payload: dict) -> list[NormalizedNotice]:
    records = []
    for item in payload.get("data", []):
        attributes = item.get("attributes") or {}
        entities = attributes.get("informed_entity") or []
        route_ids = sorted({str(entity["route"]) for entity in entities if entity.get("route")})
        stop_ids = sorted({str(entity["stop"]) for entity in entities if entity.get("stop")})
        area = ", ".join("Stop " + stop for stop in stop_ids[:4]) or (
            "Routes " + ", ".join(route_ids) if route_ids else "Network-wide"
        )
        periods = attributes.get("active_period") or []
        starts = [_parse_datetime(period.get("start"), "America/New_York") for period in periods if period.get("start")]
        ends = [_parse_datetime(period.get("end"), "America/New_York") for period in periods if period.get("end")]
        starts = [value for value in starts if value]
        ends = [value for value in ends if value]
        summary = _plain_text(attributes.get("header") or attributes.get("short_header") or attributes.get("banner"))
        description = _plain_text(attributes.get("description"))
        if not summary:
            summary = description[:220] or "Service advisory"
        if not description:
            description = summary
        records.append(
            NormalizedNotice(
                external_id=str(item.get("id", "")),
                route_ids=route_ids,
                area=area,
                source_url=attributes.get("url") or "https://www.mbta.com/alerts",
                advisory_type=_advisory_type(
                    str(attributes.get("effect_name") or attributes.get("effect") or ""),
                    str(attributes.get("cause") or ""),
                ),
                summary=summary[:600],
                content_text=description[:12000],
                published_at=_parse_datetime(attributes.get("created_at"), "America/New_York"),
                valid_from=min(starts) if starts else None,
                valid_to=max(ends) if ends else None,
            )
        )
    return records


def fetch_mbta() -> tuple[list[NormalizedNotice], bool]:
    headers = {"Accept": "application/vnd.api+json", "User-Agent": "TransitNotice/1.0"}
    if settings.mbta_api_key.strip():
        headers["x-api-key"] = settings.mbta_api_key.strip()
    url = MBTA_URL
    records: list[NormalizedNotice] = []
    pages = 0
    complete = True
    while url and pages < 5:
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https" or parsed_url.hostname != "api-v3.mbta.com":
            raise ValueError("MBTA returned a pagination link outside its official HTTPS API host")
        params = {"page[limit]": "100", "sort": "-created_at"} if pages == 0 else None
        response = _request_json(url, params=params, headers=headers, allowed_host="api-v3.mbta.com")
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ValueError("MBTA response did not match its documented alert feed shape")
        records.extend(_mbta_records(payload))
        next_url = (payload.get("links") or {}).get("next")
        pages += 1
        if not next_url:
            break
        url = str(next_url)
    if url and pages >= 5:
        complete = False
    return records, complete


def _cta_records(payload: dict) -> list[NormalizedNotice]:
    root = payload.get("CTAAlerts") or payload
    alerts = root.get("Alert") or []
    if isinstance(alerts, dict):
        alerts = [alerts]
    records = []
    for item in alerts:
        impacted = item.get("ImpactedService") or {}
        services = impacted.get("Service") or []
        if isinstance(services, dict):
            services = [services]
        route_ids = sorted({str(service["ServiceId"]) for service in services if service.get("ServiceId")})
        area_names = sorted({str(service["ServiceName"]) for service in services if service.get("ServiceName")})
        full = _plain_text(item.get("FullDescription"))
        summary = _plain_text(item.get("Headline") or item.get("ShortDescription")) or "Service advisory"
        detail = _plain_text(item.get("ShortDescription"))
        if not detail:
            detail = full or summary
        records.append(
            NormalizedNotice(
                external_id=str(item.get("AlertId") or item.get("AlertID") or ""),
                route_ids=route_ids,
                area=", ".join(area_names[:4]) or "Network-wide",
                source_url=_plain_text(item.get("AlertURL")) or "https://www.transitchicago.com/alerts/",
                advisory_type=_advisory_type(
                    str(item.get("Impact") or ""),
                    str(item.get("SeverityCSS") or ""),
                ),
                summary=summary[:600],
                content_text=detail[:12000],
                published_at=None,
                valid_from=_parse_datetime(item.get("EventStart"), "America/Chicago"),
                valid_to=_parse_datetime(item.get("EventEnd"), "America/Chicago"),
            )
        )
    return records


def fetch_cta() -> tuple[list[NormalizedNotice], bool]:
    if not settings.cta_ready:
        raise RuntimeError("CTA is locked until its developer terms have been reviewed and acknowledged")
    response = _request_json(
        CTA_URL,
        params={"outputType": "JSON", "activeonly": "false", "planned": "true"},
        headers={"Accept": "application/json", "User-Agent": "TransitNotice/1.0"},
        allowed_host="lapi.transitchicago.com",
    )
    payload = response.json()
    root = payload.get("CTAAlerts") or {}
    code = str(root.get("ErrorCode", "0"))
    if code not in ("0", "", "25", "50"):
        raise ValueError("CTA returned an error: " + str(root.get("ErrorMessage") or code)[:300])
    return _cta_records(payload), True


def _fetch_tamil_nadu_page(url: str, source_key: str, agency_name: str) -> tuple[list[NormalizedNotice], bool]:
    response = _request_json(
        url,
        headers={"Accept": "text/html", "User-Agent": "TransitNotice/1.0"},
        allowed_host=urlparse(url).hostname,
        # MTC currently serves an incomplete certificate chain in some Python environments.
        # Keep the fallback restricted to the official MTC hostname.
        verify=source_key != "mtc_chennai",
    )
    soup = BeautifulSoup(response.text, "html.parser")
    records: list[NormalizedNotice] = []
    nodes = soup.select("table tr") if source_key == "cmrl" else soup.select("article, .news-item, .news-list li, .card")
    for index, node in enumerate(nodes):
        text = _plain_text(node.get_text(" ", strip=True))
        if len(text) < 35:
            continue
        cells = [_plain_text(cell.get_text(" ", strip=True)) for cell in node.select("th, td")]
        if source_key == "cmrl" and len(cells) >= 2:
            text = " — ".join(part for part in cells if part)
        link = node.find("a", href=True)
        detail_url = link.get("href") if link else url
        if detail_url and detail_url.startswith("/"):
            detail_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}{detail_url}"
        records.append(NormalizedNotice(
            external_id=f"{source_key}-{index}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}",
            route_ids=[], area="Tamil Nadu", source_url=detail_url or url,
            advisory_type=_advisory_type(text, ""), summary=text[:600], content_text=text[:12000],
            published_at=_parse_datetime(cells[0], "Asia/Kolkata") if source_key == "cmrl" and cells else None,
            valid_from=None,
            valid_to=None,
        ))
        if len(records) >= 50:
            break
    return records, True


def fetch_mtc_chennai() -> tuple[list[NormalizedNotice], bool]:
    return _fetch_tamil_nadu_page(MTC_URL, "mtc_chennai", SOURCE_META["mtc_chennai"][0])


def fetch_cmrl() -> tuple[list[NormalizedNotice], bool]:
    return _fetch_tamil_nadu_page(CMRL_URL, "cmrl", SOURCE_META["cmrl"][0])


COLLECTORS: dict[str, tuple[Callable, str]] = {
    "mtc_chennai": (fetch_mtc_chennai, SOURCE_META["mtc_chennai"][0]),
    "cmrl": (fetch_cmrl, SOURCE_META["cmrl"][0]),
}


def _get_or_create_agency(session, source_key: str) -> Agency:
    name, url = SOURCE_META[source_key]
    agency = session.query(Agency).filter_by(key=source_key).one_or_none()
    if agency is None:
        agency = Agency(key=source_key, name=name, source_url=url, is_demo=False)
        session.add(agency)
        session.flush()
    return agency


def _source_enabled(source_key: str) -> tuple[bool, str]:
    if settings.demo_mode:
        return False, "Demo mode is on; no live source is contacted"
    if source_key == "mtc_chennai":
        return settings.mtc_enabled, "MTC collection is disabled in settings" if not settings.mtc_enabled else ""
    if source_key == "cmrl":
        return settings.cmrl_enabled, "CMRL collection is disabled in settings" if not settings.cmrl_enabled else ""
    return False, "Unknown source"


def refresh_source(session, source_key: str) -> dict:
    started = utc_now()
    enabled, reason = _source_enabled(source_key)
    run = CollectorRun(source_key=source_key, started_at=started, state="running")
    session.add(run)
    session.commit()

    if not enabled:
        run.state = "paused"
        run.error_message = reason
        run.finished_at = utc_now()
        session.commit()
        return {"source": source_key, "state": run.state, "message": reason}

    fetcher, agency_name = COLLECTORS[source_key]
    try:
        records, complete = fetcher()
        agency = _get_or_create_agency(session, source_key)
        counts = process_snapshot(session, agency, records, complete_snapshot=complete, observed_at=utc_now())
        run.state = "success"
        run.notice_count = counts["notices"]
        run.new_count = counts["new"]
        run.updated_count = counts["updated"]
        run.finished_at = utc_now()
        session.commit()
        return {"source": source_key, "state": "success", "agency": agency_name, **counts}
    except Exception as exc:
        logger.warning("Collector %s failed: %s", source_key, type(exc).__name__)
        session.rollback()
        run = session.query(CollectorRun).filter_by(id=run.id).one()
        run.state = "error"
        run.error_message = (type(exc).__name__ + ": " + str(exc))[:1000]
        run.finished_at = utc_now()
        session.commit()
        return {"source": source_key, "state": "error", "message": run.error_message}


def refresh_enabled_sources(session) -> list[dict]:
    results = []
    for source_key in ("mtc_chennai", "cmrl"):
        results.append(refresh_source(session, source_key))
    return results
