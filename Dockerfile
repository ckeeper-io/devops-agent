FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y \
    git \
    curl \
    gnupg \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY .env .
ARG GIT_USER_NAME
ARG GIT_USER_EMAIL
ARG GITHUB_TOKEN

ENV GIT_USER_NAME=$GIT_USER_NAME
ENV GIT_USER_EMAIL=$GIT_USER_EMAIL
ENV GITHUB_TOKEN=$GITHUB_TOKEN

RUN git config --global user.name "$GIT_USER_NAME" && \
    git config --global user.email "$GIT_USER_EMAIL"
EXPOSE 8000


CMD bash -c "uvicorn app:app --host 0.0.0.0 --port 8000"