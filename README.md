# LedgerLocket (CoinPilot)

LedgerLocket (codename CoinPilot) — Centralized non-withdrawable crypto credits platform scaffold.

This scaffold provides a development-ready Flask backend, Celery worker, Playwright receipt generation, connector stubs for Coinbase & Binance (sandbox), and a minimal React frontend. It is intended as a starting point to implement the features described in the product plan.

Key features in this scaffold:
- Flask app with SQLAlchemy models for users, wallets, transactions, notifications, audit logs and integrations
- JWT-based auth and optional Web3 wallet signature login endpoints
- Admin-only mint endpoint and transaction model
- Playwright receipt screenshot endpoint + Celery task example
- Exchange connector stubs (connectors/coinbase.py, connectors/binance.py)
- Docker Compose for dev: web, worker, db (Postgres), redis, playwright, frontend

Quickstart (development):
1. Copy .env.example to .env and edit values (POSTGRES_PASSWORD, SECRET_KEY, etc.)
2. docker-compose up --build
3. Backend available at http://localhost:5000, frontend at http://localhost:3000

See backend/README.md and frontend/README.md for more details.
