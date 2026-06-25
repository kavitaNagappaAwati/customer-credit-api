# Customer Credit Profile & Loan Offer Management API

> **Softlend Internship Evaluation Project**  
> A production-grade REST API built with FastAPI, SQLAlchemy, and MySQL that manages customer credit profiles, credit gap analysis, and the full loan offer lifecycle.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
  - [Requirements](#requirements)
  - [Virtual Environment](#virtual-environment)
  - [MySQL Setup](#mysql-setup)
  - [Environment Configuration](#environment-configuration)
  - [Database Migration](#database-migration)
  - [Run the Server](#run-the-server)
- [API Documentation](#api-documentation)
- [Postman Usage](#postman-usage)
- [Endpoint Reference](#endpoint-reference)
- [Example Requests & Responses](#example-requests--responses)
- [Business Logic](#business-logic)
- [Error Format](#error-format)

---

## Project Overview

This API is the backend for a fintech credit management platform. It allows operations teams and partner integrations to:

- **Register customers** and manage their credit profiles.
- **Track CIBIL scores** with timestamps for audit trails.
- **Identify and resolve credit gaps** — specific factors dragging a customer's score below its potential.
- **Manage loan offers** from multiple lenders with full score-gating and lifecycle transitions.
- **Calculate EMIs** on-the-fly without storing computed data.

---

## Features

- ✅ Customer registration with PAN and mobile validation
- ✅ CIBIL score update with `score_fetched_at` timestamping
- ✅ Credit gap creation, tracking, and resolution workflow
- ✅ Full credit profile view with potential score projection
- ✅ Loan offer creation with automatic `pending` status
- ✅ Score gating — offers locked if customer score < minimum required
- ✅ Offer status pipeline: `pending → active → disbursed`
- ✅ EMI calculator using the standard reducing-balance formula
- ✅ Filtering offers by locked / unlocked status
- ✅ [Bonus] Improvement summary — recovered score + remaining potential
- ✅ Request/response logging middleware with timestamps and latency
- ✅ Uniform error envelope `{ "error": "...", "code": "..." }`
- ✅ Full Alembic migration support
- ✅ Postman collection with success and failure cases for every endpoint

---

## Tech Stack

| Layer       | Technology                      |
|-------------|---------------------------------|
| Framework   | FastAPI 0.111                   |
| Server      | Uvicorn (ASGI)                  |
| Database    | MySQL 8.x                       |
| ORM         | SQLAlchemy 2.0                  |
| Migrations  | Alembic 1.13                    |
| Validation  | Pydantic v2                     |
| Config      | pydantic-settings + python-dotenv |
| Driver      | PyMySQL                         |

---

## Folder Structure

```
customer-credit-api/
│
├── app/
│   ├── main.py              # FastAPI app factory, middleware, exception handlers
│   ├── database.py          # Engine, SessionLocal, Base, get_db dependency
│   ├── models.py            # SQLAlchemy ORM models (Customer, CreditGap, Offer)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── crud.py              # Repository layer — all DB operations
│   ├── config.py            # Settings loaded from .env via Pydantic
│   ├── routers/
│   │   ├── customers.py     # Customer + credit profile endpoints
│   │   ├── credit.py        # Credit gap endpoints
│   │   └── offers.py        # Offer + EMI endpoints
│   ├── services/
│   │   ├── emi.py           # EMI calculation (pure function)
│   │   └── score_logic.py   # Score gating, transitions, potential score
│   ├── middleware/
│   │   └── logging.py       # Request logging middleware
│   └── utils/
│       ├── validators.py    # Pure-function field validators
│       └── responses.py     # error_response() factory function
│
├── alembic/
│   ├── env.py               # Alembic environment (reads DATABASE_URL from .env)
│   ├── script.py.mako       # Migration template
│   └── versions/
│       └── 0001_initial_schema.py  # Initial DB schema migration
│
├── postman/
│   └── customer_credit_api.postman_collection.json
│
├── .env                     # Environment variables (do not commit to VCS)
├── alembic.ini              # Alembic config
├── requirements.txt
└── README.md
```
---

## 🚀 How to Run Project (Quick Start)

```bash
git clone https://github.com/your-username/customer-credit-api.git

cd customer-credit-api

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

mysql -u root -p
USE customer_credit_db;
SHOW TABLES;
EXIT;

py -3.13 -m uvicorn app.main:app --reload
---

## Installation

### Requirements

- Python 3.11+
- MySQL 8.x running locally (or remote)
- `pip` and `virtualenv` / `venv`

### Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-org/customer-credit-api.git
cd customer-credit-api

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Linux / macOS
venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt
```

### MySQL Setup

Log in to your MySQL server and create the database:

```sql
CREATE DATABASE customer_credit_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'credit_user'@'localhost' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON customer_credit_db.* TO 'credit_user'@'localhost';
FLUSH PRIVILEGES;
```

### Environment Configuration

Copy the sample `.env` and update the values:

```bash
cp .env .env.local   # optional — or just edit .env directly
```

```dotenv
# .env
APP_NAME=Customer Credit Profile & Loan Offer Management API
APP_VERSION=1.0.0
DEBUG=False

DB_HOST=localhost
DB_PORT=3306
DB_USER=credit_user
DB_PASSWORD=yourpassword
DB_NAME=customer_credit_db

DATABASE_URL=mysql+pymysql://credit_user:yourpassword@localhost:3306/customer_credit_db

LOG_LEVEL=INFO
```

### Database Migration

Run the Alembic migration to create all tables:

```bash
# Apply migrations
alembic upgrade head

# (Optional) Generate a new autogenerated migration after model changes
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

### Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Documentation

Once the server is running, open your browser:

| Interface | URL                              |
|-----------|----------------------------------|
| Swagger UI | http://localhost:8000/docs      |
| ReDoc      | http://localhost:8000/redoc     |
| OpenAPI JSON | http://localhost:8000/openapi.json |

---

## Postman Usage

1. Open Postman → **Import** → select `postman/customer_credit_api.postman_collection.json`.
2. The collection uses collection-level variables:
   - `base_url` — default `http://localhost:8000`
   - `customer_id`, `gap_id`, `offer_id` — update these after creating records.
3. Run requests in order: **Create Customer → Update Score → Create Gap → Create Offer → Activate Offer → Get EMI**.

---

## Endpoint Reference

| Method | Endpoint                                | Description                            |
|--------|-----------------------------------------|----------------------------------------|
| GET    | `/`                                     | Health check                           |
| POST   | `/customers`                            | Register a new customer                |
| POST   | `/customers/{id}/credit-score`          | Update CIBIL score                     |
| POST   | `/customers/{id}/credit-gaps`           | Add a credit gap                       |
| PATCH  | `/credit-gaps/{id}/resolve`             | Resolve a credit gap                   |
| GET    | `/customers/{id}/credit-profile`        | Full credit profile view               |
| GET    | `/customers/{id}/improvement-summary`   | [Bonus] Score improvement summary      |
| POST   | `/customers/{id}/offers`                | Create a loan offer                    |
| GET    | `/customers/{id}/offers`                | List offers (`?locked=true/false`)     |
| PATCH  | `/offers/{id}/status`                   | Transition offer status                |
| GET    | `/offers/{id}/emi`                      | Calculate monthly EMI                  |

---

## Example Requests & Responses

### POST /customers — Create Customer

**Request:**
```json
{
  "name": "Arjun Sharma",
  "mobile": "9876543210",
  "pan": "ABCDE1234F"
}
```

**Response `201`:**
```json
{
  "id": 1,
  "name": "Arjun Sharma",
  "mobile": "9876543210",
  "pan": "ABCDE1234F",
  "cibil_score": null,
  "score_fetched_at": null,
  "created_at": "2024-01-15T10:32:01"
}
```

---

### POST /customers/1/credit-score — Update Score

**Request:**
```json
{ "cibil_score": 680 }
```

**Response `200`:**
```json
{
  "id": 1,
  "cibil_score": 680,
  "score_fetched_at": "2024-01-15T10:35:00"
}
```

---

### POST /customers/1/credit-gaps — Create Gap

**Request:**
```json
{
  "factor": "Credit Utilisation",
  "current_value": "78%",
  "ideal_value": "<30%",
  "impact": "high",
  "estimated_score_gain": 45,
  "action_description": "Pay down credit card balances to below 30% of the limit."
}
```

**Response `201`:**
```json
{
  "id": 1,
  "customer_id": 1,
  "factor": "Credit Utilisation",
  "status": "open",
  "estimated_score_gain": 45,
  "resolved_at": null
}
```

---

### GET /customers/1/credit-profile — Credit Profile

**Response `200`:**
```json
{
  "customer": { "id": 1, "name": "Arjun Sharma", "cibil_score": 680 },
  "current_score": 680,
  "potential_score": 725,
  "open_gaps": [
    {
      "factor": "Credit Utilisation",
      "estimated_score_gain": 45,
      "status": "open"
    }
  ],
  "resolved_gaps": []
}
```

---

### POST /customers/1/offers — Create Offer

**Request:**
```json
{
  "lender": "HDFC Bank",
  "amount": 500000,
  "interest_rate": 10.5,
  "tenure_months": 36,
  "min_score_required": 700
}
```

**Response `201`:**
```json
{
  "id": 1,
  "lender": "HDFC Bank",
  "amount": 500000,
  "status": "pending",
  "locked": true,
  "score_gap": 20
}
```

---

### PATCH /offers/1/status — Offer Locked Error

**Response `422`:**
```json
{
  "error": "Offer is locked. Customer score 680 is below required 700.",
  "code": "OFFER_LOCKED"
}
```

---

### GET /offers/1/emi — EMI Calculation

**Response `200`:**
```json
{
  "offer_id": 1,
  "principal": 500000.0,
  "interest_rate": 10.5,
  "tenure_months": 36,
  "monthly_emi": 16133.19
}
```

---

## Business Logic

### Score Gating
An offer is **locked** when `customer.cibil_score < offer.min_score_required` or when the customer has no score on record. A locked offer cannot be activated.

### Potential Score
`Potential Score = Current Score + Σ(estimated_score_gain for all open gaps)`, capped at 900.

### Status Transitions
```
pending  →  active  →  disbursed
```
No other transitions are permitted. Attempting an invalid transition returns `422`.

---

## Error Format

All errors follow the same envelope:

```json
{
  "error": "Human readable description of what went wrong.",
  "code": "MACHINE_READABLE_CODE"
}
```

| Code | HTTP | Meaning |
|------|------|---------|
| `DUPLICATE_MOBILE` | 409 | Mobile already registered |
| `CUSTOMER_NOT_FOUND` | 404 | No customer with given ID |
| `GAP_NOT_FOUND` | 404 | No credit gap with given ID |
| `GAP_ALREADY_RESOLVED` | 422 | Gap already in resolved state |
| `OFFER_NOT_FOUND` | 404 | No offer with given ID |
| `OFFER_LOCKED` | 422 | Customer score below minimum |
| `INVALID_STATUS_TRANSITION` | 422 | Illegal status transition |
| `VALIDATION_ERROR` | 422 | Pydantic field validation failure |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

---

*Built with ❤️ for the Softlend Internship Evaluation.*
