# MindGuard AI: build status report (2026-10-20)

## Summary

The core of the v1 brief is working end to end: anonymous onboarding with consent, PHQ-9 and
GAD-7 self-checks, a two-layer safety engine, a safety-gated chat companion, daily check-ins, a
wellness toolkit, and a privacy centre with export and permanent deletion. English and Tamil UI,
light and dark themes, mobile-first. Every listed check below passes locally.

Not done: the text emotion model, mood charts and insights, the PDF summary, PWA offline
install, voice, wearable import, a full accessibility and security pass, demo data and the
deployment guide. None of the v2-to-v4 upgrade tracks (A to T) have started.

**The most important open risk:** the safety engine meets the brief's release gate on its
red-team set (urgent recall 0.994) but scored 0.912 on a blind holdout. It is not validated for
real-world use. See [SAFETY.md](SAFETY.md).

## Test results (all passing)

| Suite | Result |
|---|---|
| API: pytest (ruff, mypy --strict clean) | 164 passed |
| Web: Vitest (ESLint strict, tsc clean) | 24 passed |
| End-to-end: Playwright at 360 px and desktop, axe-core WCAG 2.2 AA on every screen visited | 26 passed |
| Dependency audits (pip-audit, npm audit) | No known vulnerabilities; pip-audit cannot check the CPU build of torch (2.14.1+cpu) |
| Migrations on PostgreSQL 16 (upgrade, check, downgrade, upgrade) | Clean |
| Safety release gate, red-team set | PASS, urgent recall 0.994 |
| Safety, blind holdout C | 0.912, below the 0.95 gate |

CI is configured in `.github/workflows/ci.yml` but has not run on GitHub: the repository has no
remote yet.

## v1 brief: phase by phase

| Phase | Status | What exists | What is missing |
|---|---|---|---|
| 0 Monorepo, Docker, CI | Done | Compose stack (web, api, db, redis, optional ollama), CI workflow, tooling | CI never run on GitHub |
| 1 Auth, consents, age gate, landing | Done | Anonymous-first sessions, upgrade, rotating refresh tokens, versioned consents, 18+ gate, landing page | |
| 2 PHQ-9 + GAD-7 | Done | Verbatim items, band boundary tests, item 9 opens crisis card, history | Official Tamil item translations |
| 3 Safety engine + red-team | Done, with a caveat | 85 multilingual rules, embedding classifier, 317-message red-team set, three holdouts, reports | Blind recall 0.912 < 0.95; needs clinician-labelled real data |
| 4 Chatbot | Done | Mock / Ollama / Anthropic providers, SSE, safety prompt, output filter; urgent never reaches the LLM (tested) | Ollama and Anthropic not exercised against live services here |
| 5 Text emotion model | Not done | | Model, evaluation, model card, emotion chip |
| 6 Check-ins, timeline, insights | Partly | Check-ins with encrypted notes, safety-screened, recent list | Charts (7/30/90 days), score history chart, streaks, correlation view |
| 7 Screening summary + PDF | Not done | | Web summary and PDF export |
| 8 Wellness toolkit + reminders | Partly | Box breathing, 5-4-3-2-1 grounding, journaling prompts, mindfulness timer | 4-7-8 breathing, haptics, reminders, PWA offline |
| 9 Privacy centre, export, delete, retention | Done | Consent toggles, JSON export, two-step hard delete (no rows remain, tested), retention job (tested), PRIVACY.md | Retention settings per data type in the UI; key rotation script |
| 10 Voice + wearable import | Not done | | |
| 11 Tamil, accessibility, security hardening | Partly | Tamil UI throughout (needs native review), axe clean on every visited screen, CSP and security headers, rate limits tested | Full route-by-route accessibility audit, OWASP review, HSTS (needs HTTPS deployment) |
| 12 Demo data, deployment guide, pitch | Not done | | Seeded 60-day demo account, deployment guide, judges' summary |

## v2 to v4 upgrade prompt (Tracks A to T)

Not started. The upgrade prompt itself says to begin only after Phases 0 to 12 are complete
and green. Track J (safety v2) also builds on pieces not yet built (programs, institutions).

## Reports in the repository

- [SAFETY.md](SAFETY.md): engine design, datasets, metrics at every stage, known failure modes.
- `ml/safety_eval/reports/`: red-team and holdout reports (Markdown and JSON).
- [MODEL_CARDS.md](MODEL_CARDS.md) and `ml/model_cards/safety_classifier.md`.
- [PRIVACY.md](PRIVACY.md): data inventory and DPDP Act mapping.
- [DECISIONS.md](DECISIONS.md): every trade-off and deviation, with reasons.
- [ARCHITECTURE.md](ARCHITECTURE.md).

## Open risks before any real users

1. Safety engine below gate on blind data; needs clinician-labelled real messages.
2. Tamil UI copy and crisis card wording need native-speaker and clinician review.
3. Official Tamil PHQ-9 / GAD-7 translations not yet obtained.
4. Crisis numbers verified against secondary sources; re-check against official sites.
5. No breach runbook, grievance officer or DPIA yet.
6. API image is 2.65 GB (PyTorch plus the sentence encoder).

## How to run it

```bash
cp .env.example .env
docker compose up -d --build --wait
# open http://localhost:8080
```
