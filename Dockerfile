FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    TERRAFORM_VERSION=1.8.4

# Install dependencies and Terraform
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gnupg \
    unzip \
 && curl -fsSL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -o terraform.zip \
 && unzip terraform.zip \
 && mv terraform /usr/local/bin/terraform \
 && chmod +x /usr/local/bin/terraform \
 && rm terraform.zip \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY .env .

ARG GIT_USER_NAME
ARG GIT_USER_EMAIL

ENV GIT_USER_NAME=$GIT_USER_NAME
ENV GIT_USER_EMAIL=$GIT_USER_EMAIL

RUN git config --global user.name "$GIT_USER_NAME" && \
    git config --global user.email "$GIT_USER_EMAIL"

EXPOSE 8000

CMD bash -c "uvicorn app:app --host 0.0.0.0 --port 8000"
