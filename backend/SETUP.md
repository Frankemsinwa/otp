# Backend Engine Setup & Run Guide

Phase 1 hardening is complete. The backend is now fully async, with robust security, Google OAuth support, real Yahoo IMAP, and a background Redis-backed polling scheduler.

Here are the final setup steps to get the engine humming.

## 1. Environment Configuration

1. Copy `.env.example` to `.env` inside the `backend` folder:
   ```bash
   cp .env.example .env
   ```
2. Generate your real encryption keys and paste them into `.env`:
   - For `ENCRYPTION_KEY`: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - For `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

## 2. Gmail OAuth 2.0 Credentials (Placeholder Replacement)

To monitor Gmail accounts, you need real Google OAuth credentials.
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "OTP Engine").
3. Enable the **Gmail API** under "APIs & Services".
4. Go to **OAuth consent screen** and configure it as "External". Add the scope `.../auth/gmail.readonly`.
5. Go to **Credentials**, create an **OAuth client ID** (Web application type).
6. Set the Authorized redirect URI to `http://localhost:8000/api/v1/oauth/gmail/callback` (or your production domain).
7. Copy the **Client ID** and **Client Secret** into your `.env` file for `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET`.

## 3. Database & Alembic Setup

We moved from `create_all()` to Alembic migrations for production-grade schema versioning.

1. Ensure your Postgres database is running (`docker-compose up -d db`).
2. Run the initial migration to create the tables:
   ```bash
   # From inside the backend directory:
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

## 4. Run the Stack

1. Start Redis and Postgres:
   ```bash
   docker-compose up -d db redis
   ```
2. Start the Backend API:
   ```bash
   uvicorn app.main:app --reload
   ```

The engine is now active and ready to ingest targets via the API and broadcast OTPs via WebSocket!
