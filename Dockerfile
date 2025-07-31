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
# Install Node.js and ESLint
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && apt-get install -y nodejs && \
    npm install -g eslint && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY .env .

ARG GITHUBAPP_USER_NAME
ARG GITHUBAPP_USER_EMAIL

ENV GITHUBAPP_USER_NAME=$GITHUBAPP_USER_NAME
ENV GITHUBAPP_USER_EMAIL=$GITHUBAPP_USER_EMAIL

RUN git config --global user.name "$GITHUBAPP_USER_NAME" && \
    git config --global user.email "$GITHUBAPP_USER_EMAIL"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
