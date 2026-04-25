# 🚀 AuraGrowth – SaaS Backend

A production-ready FastAPI backend for a unified SaaS platform combining **link-in-bio pages**, **Gmail automation**, and **Instagram DM automation** powered by Meta API.

## ⚡ Tech Stack

| Component        | Technology                    |
|-----------------|-------------------------------|
| Framework       | FastAPI (Python 3.12+)        |
| Database        | PostgreSQL 16 + asyncpg       |
| ORM             | SQLAlchemy 2.0 (async)        |
| Migrations      | Alembic                       |
| Auth            | JWT (python-jose) + bcrypt    |
| Validation      | Pydantic v2                   |
| Email           | aiosmtplib (async SMTP)       |
| HTTP Client     | httpx (async)                 |

## 📁 Project Structure

```
app/
├── api/v1/          # API route handlers
├── core/            # Config, security, dependencies, exceptions
├── db/              # Database engine and base models
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic v2 request/response schemas
├── services/        # Business logic layer
└── utils/           # Logging, pagination helpers
```

## 🏃 Quick Start

### 1. Start PostgreSQL

```bash
docker-compose up -d postgres
```

### 2. Create virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
copy .env.example .env
# Edit .env with your credentials
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Open API docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 Authentication

### Email + Password
- `POST /api/v1/auth/register` – Register with name, email, password
- `POST /api/v1/auth/login` – Login and get JWT tokens

### Google OAuth
- `GET /api/v1/auth/google/login` – Redirect to Google
- `GET /api/v1/auth/google/callback` – Handle callback

## 📧 Gmail Integration
- `GET /api/v1/gmail/connect` – Connect Gmail via OAuth
- `GET /api/v1/gmail/emails` – List emails
- `POST /api/v1/gmail/emails/send` – Send email

## 📱 Instagram DM Automation
- `GET /api/v1/instagram/connect` – Connect Instagram Business account
- `POST /api/v1/instagram/webhook` – Meta webhook for comment events

### How keyword-triggered DMs work:
1. User sets up an automation with keyword "LINK"
2. Someone comments "LINK" on their Instagram post
3. Meta sends webhook to our server
4. Server matches keyword against active automation rules
5. Sends DM to commenter: "Here's your link: https://..."

## 🔗 Link-in-Bio
- `POST /api/v1/bio/pages` – Create bio page
- `GET /api/v1/bio/p/{slug}` – Public bio page view
- `POST /api/v1/bio/p/{slug}/click/{link_id}` – Track clicks

## 📊 API Endpoints

| Module          | Prefix                    | Endpoints |
|----------------|---------------------------|-----------|
| Auth           | `/api/v1/auth`            | 6         |
| Users          | `/api/v1/users`           | 3         |
| Gmail          | `/api/v1/gmail`           | 7         |
| Instagram      | `/api/v1/instagram`       | 5         |
| Automations    | `/api/v1/automations`     | 7         |
| Bio Pages      | `/api/v1/bio`             | 10        |
| Subscriptions  | `/api/v1/subscriptions`   | 5         |
| Analytics      | `/api/v1/analytics`       | 5         |
| Admin          | `/api/v1/admin`           | 8         |

## 📄 License

Private – All rights reserved.
