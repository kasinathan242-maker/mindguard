# MindGuard AI: build status report (2026-10-21)

## Summary

All thirteen phases of the v1 brief (0 to 12) are built and tested, with the gaps listed below.
The app runs end to end in Docker and offline after the first build: anonymous onboarding with
consent, PHQ-9 and GAD-7, a two-layer safety engine, a safety-gated chat companion with an
experimental emotion guess, daily check-ins with a mood chart and patterns, a screening summary
with PDF, a wellness toolkit with reminders, experimental voice check-ins, wearable CSV import,
and a privacy centre with export, permanent deletion, retention and key rotation. English and
Tamil, light and dark, installable PWA.

**Most important open risk:** the safety engine meets the release gate on the red-team set
(urgent recall 0.994) but scored 0.912 on a blind holdout. It is not validated for real users
until it is tested on clinician-labelled real messages. See [SAFETY.md](SAFETY.md).

None of the v2-to-v4 upgrade tracks (A to T) have started.

## Test results (all passing at the last run)

| Suite | Result |
|---|---|
| API: pytest, ruff, mypy --strict | 197 passed, clean |
| Web: Vitest, ESLint (strict), tsc, Prettier | 26 passed, clean |
| End to end: Playwright at 360 px and desktop | 40 passed |
| Accessibility: axe-core WCAG 2.2 AA on every route, light and dark, English and Tamil | No violations |
| Migrations on PostgreSQL 16 (upgrade, check, downgrade, upgrade) | Clean |
| Dependency audits | No known vulnerabilities; pip-audit cannot check the CPU build of torch (2.14.1+cpu) |
| Safety release gate, red-team set (317) | PASS, urgent recall 0.994 |
| Safety, blind holdout C (70) | 0.912, below the 0.95 gate |
| Text emotion, GoEmotions test (4,968) | macro-F1 0.648 (VADER polarity baseline 0.622 vs model 0.758) |

CI is configured in `.github/workflows/ci.yml` but has never run on GitHub: the repository has
no remote yet.

## v1 brief: phase by phase

| Phase | Status | Notes and gaps |
|---|---|---|
| 0 Monorepo, Docker, CI | Done | CI not yet run on GitHub |
| 1 Auth, consents, age gate, landing | Done | |
| 2 PHQ-9 + GAD-7 | Done | Items shown in English under a Tamil UI until official Tamil translations are obtained |
| 3 Safety engine + red-team | Done, gate caveat | Blind recall 0.912 < 0.95 |
| 4 Chatbot | Done | Ollama and Anthropic providers implemented but not exercised against live services here |
| 5 Text emotion | Done | English only; Tamil/Tanglish return `unsupported` |
| 6 Check-ins, timeline, insights | Done | Score history shown as a list, not a chart; a gentle 7-day count replaces "streaks" (the upgrade brief bans loss-aversion streaks) |
| 7 Screening summary + PDF | Done | PDF is English only |
| 8 Wellness toolkit + reminders | Done | Reminders fire while the app is open; background push needs a push service |
| 9 Privacy centre, export, delete, retention | Done | Per-type retention is configured by environment, not in the UI |
| 10 Voice + wearable import | Done (voice flagged off) | No speech-emotion model by design; Health Connect export parsing not built (CSV only) |
| 11 Tamil, accessibility, security hardening | Done | Tamil copy needs native-speaker review; no third-party penetration test |
| 12 Demo data, deployment guide, pitch | Done | Fresh-clone build time not yet measured |

## v2 to v4 upgrade prompt (Tracks A to T)

Not started. The upgrade prompt says to begin after Phases 0 to 12 are complete and green; that
is now the case apart from the blind safety number above, which Track J (safety v2) and Track C
(Tamil models) would address first.

## Reports and documents

- [SAFETY.md](SAFETY.md) and `ml/safety_eval/reports/`: safety design and every evaluation.
- [MODEL_CARDS.md](MODEL_CARDS.md), `ml/model_cards/`, `ml/text_emotion/report.json`.
- [PRIVACY.md](PRIVACY.md): data inventory and DPDP Act mapping.
- [DECISIONS.md](DECISIONS.md): every trade-off, with reasons.
- [DEPLOYMENT.md](DEPLOYMENT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [PITCH.md](PITCH.md).

## Open risks before any real users

1. Safety engine below gate on blind data; needs a clinician-labelled real-world set.
2. Tamil UI copy, crisis wording and system prompt need native-speaker and clinician review.
3. Official Tamil PHQ-9 / GAD-7 translations not yet obtained.
4. Crisis numbers verified against secondary sources; re-check against official sites.
5. No breach runbook, grievance officer or DPIA yet; consent wording needs legal review.
6. API image is 4.25 GB; consider a smaller encoder or separate inference service at scale.
