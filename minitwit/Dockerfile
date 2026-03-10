FROM python:3.11-slim

EXPOSE 5000

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install the DB
RUN apt-get update && apt-get install -y sqlite3 libsqlite3-dev

# Initialize the DB
RUN sqlite3 /tmp/minitwit.db < schema.sql
RUN sqlite3 /tmp/minitwit.db < dump.sql

ENV GUNICORN_CMD_ARGS="--workers=4 --bind=0.0.0.0:5000"
CMD ["gunicorn", "minitwit:app"]