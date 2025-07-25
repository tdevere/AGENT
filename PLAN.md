# Development Plan

This project aims to self-host the open source **bible_api** server and provide a Python command line client. The instructions in `SourceDoc.md` describe how to use Docker Compose to deploy the server and how to build a CLI.

## Server (Docker Compose)
1. Create a `Dockerfile` that clones `seven1m/bible_api`, installs dependencies and exposes port 4567.
2. Create `docker-compose.yml` with services:
   - **db**: MySQL 8 with persistent volume and healthcheck.
   - **redis**: Redis with persistent volume.
   - **api**: build from Dockerfile and depend on db and redis. Expose port `4567` and pass `DATABASE_URL` and `REDIS_URL`.
3. Run `docker compose up -d --build` to build containers.
4. Import Bible text data with `docker compose exec api bundle exec ruby import.rb`.

## API Verification
- Use `curl http://localhost:4567/John+3:16` to check the server.
- Endpoints under `/data` list translations, books, chapters and provide random verses.

## Python CLI Client
1. Create `client/client.py` using `argparse` and `requests`.
2. Support subcommands:
   - `verse <ref>`: fetch verse/passage (optional `--translation`).
   - `translations`: list translations.
   - `books --translation <id>`: list books for translation.
   - `chapters <book> --translation <id>`: list chapters for a book.
   - `random [--books IDs | --testament OT|NT]`: random verse.
3. Default server URL is `http://api:4567` when run inside compose. Use `--server` to override.
4. Print JSON responses to stdout.

## Containerizing Client (optional)
- Add `client/Dockerfile` based on `python:3.11-slim`.
- Install `requests` from `client/requirements.txt` and copy `client.py`.
- In `docker-compose.yml` add a service named `client` using this Dockerfile for on-demand commands.

## Local Development
- Install dependencies with `pip install -r requirements.txt` (and `requirements-dev.txt` for tests).
- Run tests with `python -m pytest`.

## References
- [`seven1m/bible_api`](https://github.com/seven1m/bible_api) – original Ruby API.
- `https://bible-api.com` – hosted version (network access was blocked during evaluation).

This plan outlines the components to implement based on `SourceDoc.md` and the existing README.
