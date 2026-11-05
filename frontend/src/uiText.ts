import type { Delivery, Notice, Revision, Source } from "./types";

const indiaText = (value: string) =>
  value
    .replaceAll("HarborLink Demo Network", "Bengaluru Transit Demo")
    .replaceAll("Riverside Market", "MG Road · Indiranagar")
    .replaceAll("Central Station", "Majestic Interchange")
    .replaceAll("Museum Quarter", "Hebbal · Mekhri Circle")
    .replaceAll("North Pier", "Yelachenahalli")
    .replaceAll("Harbor Bridge", "Outer Ring Road")
    .replaceAll("Garden District", "Baiyappanahalli")
    .replaceAll("Route 14", "BMTC 500K")
    .replaceAll("Route R2", "Namma Metro Green Line")
    .replaceAll("Route R5", "Namma Metro Purple Line")
    .replaceAll("Route 31", "BMTC 201R")
    .replaceAll("Routes 7 and 14", "BMTC 335E and 500")
    .replaceAll("Route 7", "BMTC 335E")
    .replaceAll("Route 14", "BMTC 500K");

export function indiaNotice(notice: Notice): Notice {
  if (!notice.is_demo) return notice;
  return {
    ...notice,
    agency: "Bengaluru Transit Demo",
    area: indiaText(notice.area),
    route_ids: notice.route_ids.map((route) =>
      route === "14" ? "BMTC 500K" :
      route === "R2" ? "Green Line" :
      route === "R5" ? "Purple Line" :
      route === "31" ? "BMTC 201R" :
      route === "7" ? "BMTC 335E" : route,
    ),
    summary: indiaText(notice.summary),
    content_text: indiaText(notice.content_text),
  };
}

export function indiaRevision(revision: Revision): Revision {
  if (!revision.is_demo) return revision;
  return {
    ...revision,
    agency: "Bengaluru Transit Demo",
    summary: indiaText(revision.summary),
    route_ids: revision.route_ids.map((route) =>
      route === "14" ? "BMTC 500K" :
      route === "R2" ? "Green Line" :
      route === "R5" ? "Purple Line" :
      route === "31" ? "BMTC 201R" :
      route === "7" ? "BMTC 335E" : route,
    ),
  };
}

export function indiaSource(source: Source): Source {
  if (!source.is_demo) return source;
  return {
    ...source,
    agency: "Bengaluru Transit Demo",
    message: "India-focused sample data for Bengaluru; not live data",
  };
}

export function indiaDelivery(delivery: Delivery): Delivery {
  if (!delivery.subject.includes("HarborLink") && !delivery.subject.includes("Riverside")) return delivery;
  return {
    ...delivery,
    subject: indiaText(delivery.subject).replace("TransitNotice:", "Bengaluru update:"),
  };
}
