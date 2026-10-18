# Backend README

This folder contains the Flask backend for LedgerLocket (CoinPilot).

Folders:
- models.py : SQLAlchemy models
- auth/routes.py : authentication endpoints (register/login/refresh)
- transactions/routes.py : mint and list transactions
- receipts/receipt_screenshot.py : Playwright screenshot endpoint (blocking)
- connectors/ : exchange connector stubs
- celery_worker.py & tasks/: Celery initialization and example task

Development:
- Use docker-compose to run Postgres, Redis, backend and worker services.
- To run migrations: inside the web container run `flask db init/migrate/upgrade`.
- Playwright: the receipt PNG endpoint uses Playwright. In dev you can call it directly (it will launch Chromium) or run Playwright container defined in docker-compose to share filesystem.
