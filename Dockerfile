FROM python:3.14-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "alembic upgrade head && flask --app app.web_app.main run --host 0.0.0.0 --port 5000"]
