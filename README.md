# YouTube Clone REST API

An asynchronous backend API for a video sharing platform built with FastAPI, PostgreSQL, Redis, Celery, and MinIO.

## Features
* Authentication: User registration and JWT-based authentication.
* Media Storage: Video and thumbnail file uploads managed via MinIO object storage.
* Async Processing: Background task execution powered by Celery and Redis.
* Database Management: Relational schemas with SQLAlchemy ORM and Alembic migrations.
* Containerization: Complete local environment orchestrated with Docker Compose.

## Tech Stack
* Language: Python 3.11+
* Framework: FastAPI
* Database: PostgreSQL & SQLAlchemy (Migrations via Alembic)
* Storage: MinIO (S3-compatible)
* Task Queue: Celery & Redis
* DevOps: Docker, Docker Compose

## Quickstart with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/doniyorbek-ibrohimov/youtube-api.git
   cd youtube-api

2. Configure Environment variables:
   ```bash
   cp .env.example .env

3. Build and Run containers:
   ```bash
   docker-compose up -d --build

4. Access API documentation:
   Open http://localhost:8000/docs in your browser for Interactive Swagger UI

