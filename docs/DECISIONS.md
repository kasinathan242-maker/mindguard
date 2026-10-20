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
| 2026-10-20 | No `deleted_at` column on `users`. | Account deletion is a hard delete (brief, feature 11), so a soft-delete timestamp would never be set. The audit log keeps an anonymised record that a deletion happened. |
| 2026-10-20 | Added a `refresh_tokens` table (not in the brief's data model). | Rotating refresh tokens need durable server-side state for revocation and reuse detection. Redis runs without persistence, and losing tokens on restart would permanently lock anonymous users out of their data. Tokens are stored as SHA-256 digests. |
| 2026-10-20 | Consents are one row per user and scope (current state); history lives in `audit_log` as `consent.grant.*` / `consent.revoke.*`. | Fast "is this granted?" checks, with a complete change history for DPDP accountability. Scopes left off at sign-up are stored as a choice, not logged as revocations. |
| 2026-10-20 | Age confirmation and `core` consent are required in the same request that creates a session (`POST /auth/anonymous`, `/auth/register`). | No account can exist without a recorded 18+ confirmation and core consent. |
| 2026-10-20 | CSRF defence is `SameSite=Strict` httpOnly cookies, JSON-only request bodies and a single same-origin deployment; no separate CSRF token. | Browsers never attach Strict cookies to cross-site requests, and the API is never served cross-origin in production. Re-evaluate before allowing any cross-origin client. |
| 2026-10-20 | Auth rate limit defaults to 30 requests per minute per IP, applied to credential and session-creation endpoints only. | College campuses put many students behind one NAT address; 10 per minute would block legitimate sign-ups during a class session. `/auth/me` is not throttled. The limiter fails open if Redis is down. |
| 2026-10-20 | Tamil UI copy is a first draft written in-house and needs review by a native speaker before release. | The brief requires Tamil from day one. Questionnaire items are a separate matter (see Phase 2) and are never machine- or self-translated. |
| 2026-10-20 | Fonts are self-hosted (`@fontsource-variable/*`: Bricolage Grotesque, Plus Jakarta Sans, Noto Sans Tamil). | Works offline, needs no third-party requests (privacy, CSP `font-src 'self'`), and Noto Sans Tamil renders Tamil script in every heading and paragraph. |
| 2026-10-20 | The landing page uses a live box-breathing guide as its hero visual instead of photography. | It is a real product feature, works offline, and avoids stock imagery of distressed people. It has a pause control (WCAG 2.2.2) and stays static under reduced motion. |
| 2026-10-20 | E2E tests run with `prefers-reduced-motion: reduce`. | Entrance fades made axe-core measure contrast mid-animation. Reduced motion renders the final state, which is what users read. |
