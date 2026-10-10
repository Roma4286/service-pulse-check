FROM python:3.14-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home app
USER app

CMD ["sh", "-c", "alembic upgrade head && gunicorn --workers 4 --bind 0.0.0.0:5000 app.web_app.main:app"]
