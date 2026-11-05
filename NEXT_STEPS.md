 # What to do next in VS Code

1. Install PostgreSQL 16+ and Node 20+ if they are not already installed.
2. Open the TransitNotice folder in VS Code.
3. When VS Code recommends extensions, click Install All. The important ones are Python, Pylance and Tailwind CSS IntelliSense.
4. Open the SQL file sql/setup_local_database.sql in the VS Code PostgreSQL extension and run it while connected to PostgreSQL's default postgres database as an administrator.
5. Open .env.example, save a copy named .env, and update DATABASE_URL if you chose a different local password.
6. In the VS Code terminal, run:

       cd backend
       py -m venv .venv
       .\.venv\Scripts\Activate.ps1
       pip install -r requirements.txt
       alembic upgrade head

7. Open the Command Palette with Ctrl+Shift+P, choose Tasks: Run Task, and select TransitNotice: Prepare local project.
8. Choose Tasks: Run Task again and select TransitNotice: Run website.
9. Open http://localhost:5173.

The first screen is intentionally in safe demo mode. This proves the UI and local database workflow without inventing live transport results.

## Before using live data

Read docs/source-approval.md, then set DEMO_MODE=false in .env. MBTA can be enabled with its official API endpoint. CTA remains locked unless you have reviewed and acknowledged its developer terms. Never put API keys in frontend files.

## If something goes wrong

- alembic cannot connect: confirm PostgreSQL is running and that DATABASE_URL has the correct database, username and password.
- The frontend says it cannot connect: start the backend task first and check http://localhost:8000/api/health.
- A source is stale: open Settings. The last confirmed notice remains visible and is intentionally labeled stale until a successful source check.
