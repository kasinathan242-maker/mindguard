# Deployment

MindGuard AI runs as five containers (web, api, db, redis, optional ollama) from
`docker-compose.yml`. The same files serve a laptop demo and a single VPS.

## Laptop demo (offline after the first build)

```bash
git clone <repo> mindguard && cd mindguard
cp .env.example .env
docker compose up -d --build --wait        # the first build downloads PyTorch and the models
docker compose exec api python -m app.demo_seed
# open http://localhost:8080 and sign in with demo@mindguard.example / demo account only
```

The first build downloads about 1.5 GB (PyTorch CPU wheels and two models), so its time depends
mostly on your connection; a full fresh-clone timing has not been measured yet. Rebuilds use the
Docker cache and take about a minute. After the first build no network is needed:
models are baked into the API image, fonts are self-hosted and the chat uses the offline mock
provider unless you choose another.

## Single VPS (for example Railway, Render or any Docker host)

1. **Secrets.** Copy `.env.example` to `.env` and set:
   - `APP_ENV=production`
   - `JWT_SECRET`: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
   - `FIELD_ENCRYPTION_KEY`: `python -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`
   - `COOKIE_SECURE=true`
   - `POSTGRES_PASSWORD`: a strong random value
   - `CORS_ORIGINS`: your public origin
   The API refuses to start in production with development secrets.
2. **HTTPS.** Put a TLS-terminating proxy (Caddy, Traefik, a platform load balancer) in front of
   the `web` container's port. HSTS is already sent.
3. **Start.** `docker compose up -d --build --wait`. Migrations run automatically on API start.
4. **Retention.** Schedule `docker compose exec api python -m app.privacy.retention` daily
   (cron or the platform scheduler).
5. **Backups.** Back up the `db-data` volume (or use managed PostgreSQL with point-in-time
   recovery). Back up `FIELD_ENCRYPTION_KEY` separately: without it, encrypted notes and chats
   cannot be read.
6. **Rotate the encryption key** when needed: stop the API, run
   `OLD_FIELD_ENCRYPTION_KEY=... NEW_FIELD_ENCRYPTION_KEY=... docker compose run --rm api python -m app.core.rotate_key`,
   set the new key, start the API.

## Choosing the chat model

| `LLM_PROVIDER` | What it does | Needs |
|---|---|---|
| `mock` (default) | Short, deterministic supportive replies; works offline | Nothing |
| `ollama` | Local model, data never leaves the server | `docker compose --profile ollama up -d`, then `docker compose exec ollama ollama pull llama3.2:3b`; set `LLM_MODEL` |
| `anthropic` | Cloud model, only for users who granted `cloud_llm`; names, emails and phone numbers are removed first | `ANTHROPIC_API_KEY`, `LLM_MODEL` |

Whichever provider is chosen, the safety engine runs first and urgent messages never reach it.

## Feature flags

| Variable | Default | Notes |
|---|---|---|
| `SAFETY_CLASSIFIER` | `embedding` | `hashed` or `none` for low-memory hosts; see docs/SAFETY.md before changing |
| `EMOTION_ENABLED` | `true` | English-only emotion guess in chat |
| `VOICE_ENABLED` | `false` | Experimental voice check-ins |

## Sizing

The API image is 4.25 GB (PyTorch CPU, librosa and two models) and used about 840 MB of RAM at
rest in testing. A 2 vCPU / 4 GB VM is a reasonable starting point for a demo or small pilot. Safety checks take about 30 ms and emotion
about 25 ms per message on CPU.

## Before real users

Read the "Before launch" lists in [SAFETY.md](SAFETY.md) and [PRIVACY.md](PRIVACY.md): clinician
review, a real-world safety evaluation set, a breach runbook, a grievance officer and a legal
review are required.
