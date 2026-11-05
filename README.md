# TransitNotice

TransitNotice is a full-stack public transport service update tracker built for the Mini Project 2 brief. It keeps source provenance, freshness, notice history, change detection, and alert delivery logs visible in one dashboard.

## Run it locally (no Docker)

Install PostgreSQL 16+, Python 3.12+, and Node 20+.

Create a PostgreSQL database named transitnotice and a user with access to it. Then open PowerShell in this folder:

    Copy-Item .env.example .env
    $env:DATABASE_URL="postgresql+psycopg://transitnotice:your_password@localhost:5432/transitnotice"
    cd backend
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    alembic upgrade head
    uvicorn app.main:app --reload --port 8000

Open a second PowerShell window:

    cd frontend
    npm install
    npm run dev

Open http://localhost:5173.

Stop both processes with Ctrl+C.

The default configuration uses safe demo mode. HarborLink sample notices are fictional, local-only records and are labeled SAMPLE DATA in the UI. They are not presented as live transport information.

To use a permitted live source, read docs/source-approval.md, set DEMO_MODE=false, and configure only backend settings in .env. If a live source fails, TransitNotice preserves the last confirmed record and marks freshness stale; it never calls old data live.

## Pages

- Overview: status cards, activity chart, source health and recent notices.
- Notices: search and filters for route, agency, area, advisory type, date and status.
- History: immutable notice revisions and change summaries.
- Alert log: one local demo or configured email record per new/revised notice revision.
- Settings: source permissions, freshness policy and alert safety.

## Architecture

The backend is FastAPI, SQLAlchemy, Alembic and PostgreSQL. Collectors use requests with explicit timeouts, bounded retry/backoff, official-host redirect checks and source-specific normalization. APScheduler runs checks at the configured interval. The frontend is React, Vite, Tailwind CSS and Recharts.

The schema includes agencies, notices, notice revisions, collector runs and alert deliveries. A notice is unique per agency and external source ID. A source disappearance requires two complete checks before a notice is marked withdrawn.

See docs/architecture.md for data flow and docs/source-approval.md for source review.

## Validation

The frontend production build was run successfully with npm run build. Vite emits its normal large-chunk advisory because Recharts and the icon library are bundled together. Backend runtime checks require local Python dependencies and PostgreSQL to be installed; this package does not use Docker.
