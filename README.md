# Service Pulse Check

An uptime monitoring service: you register your services through a REST API, and background workers check them at a configured interval and store the history of every check.

## Features

- Availability checks over **HTTP** (a 2xx-3xx status counts as success) and **TCP** (a successful connection counts as success).
- Per-service check interval and timeout.
- Periodic tasks are created and removed on the fly, with no scheduler restart: add a service and checks start immediately, turn `is_active` off and they stop.
- History of results with the response time of each check.
- JWT authentication stored in an HttpOnly cookie, with CSRF protection; services are scoped to the user who owns them.
- Web interface.
- Automatically generated API documentation (Swagger UI and ReDoc).

## Stack

| Component | Technology |
|---|---|
| Web framework | Flask 3 |
| Validation and documentation | Pydantic 2, flask-pydantic-spec |
| Authentication | Flask-JWT-Extended, Argon2 (argon2-cffi) |
| Database | PostgreSQL 17, SQLAlchemy 2 (ORM), Alembic (migrations) |
| Background tasks | Celery, RedBeat |
| Broker and schedule storage | Redis 8 |
| Web pages | Jinja2 templates, htmx |
| Testing | pytest, pytest-cov |
| Linting and formatting | Ruff, pre-commit |
| CI | GitHub Actions |

## Requirements

- Python 3.10 or newer
- Docker and Docker Compose, for PostgreSQL and Redis

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Roma4286/service-pulse-check.git
cd service-pulse-check
```

### 2. Create a virtual environment and install dependencies

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Make sure to replace `JWT_SECRET_KEY` with your own value, since it signs the tokens:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Start PostgreSQL and Redis

```bash
docker compose up -d
```

### 5. Apply migrations

```bash
alembic upgrade head
```

## Running

Three processes are needed. Run each one in its own terminal with the virtual environment activated.

**Web application:**
```bash
python -m app.web_app.main
```

**Celery worker**, which runs the checks themselves:
```bash
celery -A app.celery.tasks worker --loglevel=info
```

On Windows the worker needs a pool that the platform supports:
```bash
celery -A app.celery.tasks worker --loglevel=info --pool=solo
```

**Celery beat**, which triggers the checks on schedule:
```bash
celery -A app.celery.tasks beat --loglevel=info
```

The RedBeat scheduler is already set in the Celery configuration, so the `-S` flag is not needed.

## API documentation

Once the application is running:

- Swagger UI - http://localhost:5000/apidoc/swagger
- ReDoc - http://localhost:5000/apidoc/redoc
- OpenAPI specification - http://localhost:5000/apidoc/openapi.json

To call protected endpoints in Swagger UI:

1. Log in with `POST /api/auth/login`. The browser keeps the auth cookie and sends it with every request.
2. Copy the value of the `csrf_access_token` cookie (DevTools → Application → Cookies).
3. Click **Authorize** and paste it into the `csrfToken` field.

Every protected endpoint is marked with the `csrfToken` scheme, but the server only checks the header on state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`); `GET` requests work with the cookie alone. The token changes on every login, so paste the new value after logging in again.

## Development

### Tests

```bash
pytest
```

With a coverage report:
```bash
pytest --cov=app --cov-report=term-missing
```

Tests run against an in-memory SQLite database by default. 


### Linting and formatting

The project uses [Ruff](https://docs.astral.sh/ruff/):
```bash
ruff check .
ruff format .
```

To run Ruff automatically before every commit, install the pre-commit hooks once:
```bash
pre-commit install
```

### CI

GitHub Actions runs on every push to `main` and on pull requests: one job checks linting and formatting with Ruff, the other runs the tests with coverage.
