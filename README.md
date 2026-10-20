# MindGuard AI

A privacy-first mental wellness **screening and support** web app for Indian college students
and young adults. It offers validated self-screening (PHQ-9, GAD-7), a supportive chat
companion that adapts to how you're feeling, mood tracking, a wellness toolkit, and a safety net
that routes anyone at risk to real human help.

> **MindGuard AI is not a diagnostic tool, a therapist or an emergency service.**
> Screening scores describe how you've been feeling; they are not a diagnosis.
> If you are in danger right now, call **112**, or Tele-MANAS on **14416** / **1-800-891-4416**
> (24×7, free, multilingual).

## Quickstart (Docker)

Requirements: Docker with Compose v2.24+.

```bash
cp .env.example .env
docker compose up -d --build --wait
```

- Web app: <http://localhost:8080>
- API health: <http://localhost:8080/api/v1/health>
- API docs (non-production only): <http://localhost:8000/api/docs>

To also run a local LLM with Ollama: `docker compose --profile ollama up -d`.

## Local development

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 22+.

```bash
# Database and Redis only
docker compose up -d db redis

# API (http://localhost:8000)
cd apps/api
cp ../../.env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:create_app --factory --reload

# Web (http://localhost:5173, proxies /api to the API)
cd apps/web
npm install
npm run dev
```

## Checks

| Area | Command (run inside the app folder) |
|---|---|
| API lint / format | `uv run ruff check .` · `uv run ruff format --check .` |
| API types | `uv run mypy` (strict) |
| API tests | `uv run pytest` |
| Web lint / format | `npm run lint` · `npm run format:check` |
| Web types | `npm run typecheck` |
| Web tests | `npm test` |
| End-to-end (needs the Compose stack running, with `AUTH_RATE_LIMIT_PER_MINUTE=300` in `.env`) | `npx playwright install chromium` once, then `npm run e2e` |

`pre-commit install` runs the same checks before each commit. CI runs them all, plus dependency
audits and a Docker Compose smoke test.

## Repository layout

```
apps/api   FastAPI backend (Python 3.12, SQLAlchemy 2 async, Alembic)
apps/web   React 19 PWA (Vite, Tailwind v4, TanStack Query, react-i18next)
ml/        Model evaluation, safety red-team set and model cards
docs/      Architecture, decisions, privacy, safety and model documentation
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/DECISIONS.md](docs/DECISIONS.md).
