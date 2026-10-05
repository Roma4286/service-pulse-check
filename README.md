# Service Pulse Check

An uptime monitoring service. You add your services through the web interface or the REST API, and background workers check them at a configured interval and keep the history of every check.

## Features

- Availability checks over **HTTP** (an `http(s)://` URL; a 2xx-3xx status counts as success) and **TCP** (a `host:port` address; a successful connection counts as success).
- Per-service check interval and timeout.
- Checks are scheduled on the fly, with no scheduler restart: add a service and checks start immediately, pause it and they stop.
- History of results with the response time of each check.
- Web interface: a dashboard with the status of every service, a service page with an uptime bar for the last 100 checks, and creating, editing, pausing and deleting services.
- JWT authentication in an HttpOnly cookie with CSRF protection; every user sees only their own services.
- Automatically generated API documentation (Swagger UI and ReDoc).

## Stack

| Component | Technology |
|---|---|
| Web framework | Flask 3 |
| Web pages | Jinja2 templates, htmx |
| Validation and API documentation | Pydantic 2, flask-pydantic-spec |
| Authentication | Flask-JWT-Extended, Argon2 (argon2-cffi) |
| Database | PostgreSQL 17, SQLAlchemy 2, Alembic |
| Background tasks | Celery, RedBeat |
| Broker and schedule storage | Redis 8 |
| Testing | pytest, pytest-cov |
| Linting and formatting | Ruff, pre-commit |
| CI | GitHub Actions |

## Getting started

### Requirements

- Docker and Docker Compose
- Python 3.10 or newer - only to run the application without Docker

### 1. Clone the repository

```bash
git clone https://github.com/Roma4286/service-pulse-check.git
cd service-pulse-check
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Replace `JWT_SECRET_KEY` in `.env` with your own value, since it signs the tokens. To generate one:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Run

Choose one of the two options.

#### Option A: everything in Docker

```bash
docker compose up -d --build
```

This starts PostgreSQL, Redis, the web application, the Celery worker and Celery beat. The web container applies the migrations before starting.

Stop everything with `docker compose down`.

#### Option B: the application locally, PostgreSQL and Redis in Docker

Create a virtual environment and install the dependencies.

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

Start PostgreSQL and Redis. Name the services explicitly: a plain `docker compose up -d` would also start the application containers.

```bash
docker compose up -d db redis
```

Apply the migrations:

```bash
alembic upgrade head
```

Then start three processes, each in its own terminal with the virtual environment activated.

**Web application** - checks that PostgreSQL is reachable on startup and exits with an explicit error if it is not:
```bash
python -m app.web_app.main
```

**Celery worker** - runs the checks:
```bash
celery -A app.celery.tasks worker --loglevel=info
```

On Windows add `--pool=solo`, since the default pool does not work there.

**Celery beat** - triggers the checks on schedule:
```bash
celery -A app.celery.tasks beat --loglevel=info
```

The RedBeat scheduler is already set in the Celery configuration, so the `-S` flag is not needed.

### 4. Open the application

Go to http://localhost:5000, register and log in.

## Usage

### Web interface

- **Dashboard** (`/`) - a card for every service with its latest check result, and a tile for adding a new service.
- **Service page** (`/services/<id>`) - service details, an uptime bar with the share of successful checks among the last 100, and buttons to edit, pause or resume, and delete the service.

Pages behind the login are never cached by the browser, and when the session expires you are sent back to the login page.

### REST API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create a user |
| `POST` | `/api/auth/login` | Log in, sets the auth cookies |
| `POST` | `/api/auth/logout` | Log out, clears the auth cookies |
| `GET` | `/api/services` | List your services, optionally filtered with `?is_active=true` / `false` |
| `POST` | `/api/services` | Create a service |
| `GET` | `/api/services/<id>` | Get a service |
| `PATCH` | `/api/services/<id>` | Update the name, `is_active`, interval or timeout |
| `DELETE` | `/api/services/<id>` | Delete a service |
| `GET` | `/api/services/<id>/results` | Check history, newest first, with `?page=` and `?per_page=` (at most 100) |
| `DELETE` | `/api/services/<id>/results` | Delete the whole check history |
| `DELETE` | `/api/services/<id>/results/<result_id>` | Delete one check result |

#### Authentication

`POST /api/auth/login` sets two cookies:

- `access_token_cookie` - the JWT, `HttpOnly` and `Secure`, so JavaScript cannot read it;
- `csrf_access_token` - a CSRF token that JavaScript can read.

The browser sends the cookies with every request by itself. State-changing requests (`POST`, `PATCH`, `DELETE`) must also send the `X-CSRF-TOKEN` header with the value of the `csrf_access_token` cookie, otherwise they get `401`.

Because the cookies are `Secure`, the application must be served over HTTPS anywhere other than `localhost`.

### API documentation

- Swagger UI - http://localhost:5000/apidoc/swagger
- ReDoc - http://localhost:5000/apidoc/redoc
- OpenAPI specification - http://localhost:5000/apidoc/openapi.json

To call protected endpoints in Swagger UI:

1. Log in with `POST /api/auth/login`. The browser keeps the auth cookie and sends it with every request.
2. Copy the value of the `csrf_access_token` cookie (DevTools → Application → Cookies).
3. Click **Authorize** and paste it into the `csrfToken` field.

Every protected endpoint is marked with the `csrfToken` scheme, but the server only checks the header on state-changing requests; `GET` requests work with the cookie alone. The token changes on every login, so paste the new value after logging in again.

## Development

The commands below need the virtual environment from [Option B](#option-b-the-application-locally-postgresql-and-redis-in-docker).

### Tests

```bash
pytest
```

With a coverage report:
```bash
pytest --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database, so PostgreSQL and Redis are not needed.

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
