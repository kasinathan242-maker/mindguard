# Decision log

Trade-offs and deviations from the build brief, newest last. Each entry: date, decision, reason.

| Date | Decision | Reason |
|---|---|---|
| 2026-10-20 | TypeScript is pinned to `~6.0`, not the newer 7.x line. | `typescript-eslint` 8.x supports TypeScript `<6.1`. Strict type-aware linting matters more than the newest compiler. |
| 2026-10-20 | Python 3.12 is supplied by `uv` (`requires-python = ">=3.12,<3.13"`). | The brief fixes Python 3.12; the dev machine's default is 3.14. uv pins the interpreter per project, so nothing depends on the system Python. |
| 2026-10-20 | npm, not pnpm, for the web app. | There is one JavaScript package. npm ships with every Node image, which keeps Dockerfiles and CI simple. |
| 2026-10-20 | Backend unit tests run on in-memory SQLite + fakeredis; PostgreSQL is exercised by the Compose smoke test and E2E runs. | Tests stay fast and runnable offline. Models use portable SQLAlchemy types with PostgreSQL variants (`JSONB`, `ARRAY`) where the brief asks for them. |
| 2026-10-20 | Uvicorn runs `create_app` in `--factory` mode. | No connections or settings are read at import time, which keeps tests and Alembic free of side effects. |
| 2026-10-20 | The browser reaches the API only through nginx on the same origin. | Auth cookies stay first-party (`SameSite=Strict` works), and the CSP can use `connect-src 'self'`. |
| 2026-10-20 | Redis runs with persistence disabled. | Redis holds only rate-limit counters and short-lived session data. Nothing in it needs to survive a restart, and nothing sensitive should land on disk. |
| 2026-10-20 | API docs (`/api/docs`, OpenAPI JSON) are disabled when `APP_ENV=production`. | Reduces attack surface; docs remain available in development. |
