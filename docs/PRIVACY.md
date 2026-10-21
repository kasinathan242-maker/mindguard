# Privacy

How MindGuard AI handles personal data, mapped to the principles of India's Digital Personal Data
Protection Act, 2023. This is an engineering summary, not legal advice; a legal review is needed
before launch.

## What is stored

| Data | Stored where | Protection | Kept for |
|---|---|---|---|
| Account (anonymous ID; email and argon2id password hash only if upgraded) | `users` | Password hashed; no name or phone collected | Until deleted |
| Consent choices and history | `consents`, `audit_log` | | Until deleted (audit entries are anonymised on deletion) |
| PHQ-9 / GAD-7 answers and scores | `assessments` | | Until deleted |
| Daily check-ins (mood, energy, sleep) | `checkins` | Notes AES-256-GCM encrypted | Notes cleared after 180 days |
| Chat messages, only with `chat_history` consent | `chat_messages` | AES-256-GCM encrypted | 30 days |
| Imported health data (daily totals only), with `wearables` consent | `wearable_samples` | Deleted when the consent is withdrawn | Until deleted |
| Voice recordings | Nowhere | Analysed in memory, never written (tested) | Not kept |
| Safety events | `safety_events` | No message content, ever | Until deleted |
| Rate-limit counters | Redis, no persistence | Keyed by a hash of the IP | 60 seconds |

Retention runs with `uv run python -m app.privacy.retention` (schedule daily). Logs are JSON with
email and phone-number scrubbing and never contain message content.

## DPDP principles

| Principle | How MindGuard meets it |
|---|---|
| Notice | The landing page and consent screen explain each data use in one plain sentence before any data is collected. |
| Consent | `core` is required; every other scope (chat history, voice, wearables, cloud AI, reminders) is off by default and needs its own yes. Consent is versioned and recorded with time stamps. |
| Purpose limitation | Each optional feature checks its scope on the server (`require_consent`). Cloud AI is used only with `cloud_llm` consent, and names, emails and phone numbers are removed first. |
| Data minimisation | Anonymous by default: no name, email or phone needed. Safety events store no content. Raw audio is never stored; voice is analysed in memory. |
| Withdrawal of consent | Any optional scope can be switched off on the Privacy page at any time; changes apply immediately and are audited. |
| Right to access | "Download my data" exports every stored record, decrypted, as one JSON file. |
| Right to erasure | "Delete my account" (two confirmations) hard-deletes the account and all linked rows; a test proves no user rows remain. Only an anonymous "account deleted" audit entry is kept. |
| Security safeguards | Field-level encryption, httpOnly `SameSite=Strict` cookies, rotating refresh tokens with reuse detection, rate limits, CSP and security headers, production refuses default secrets. |
| Children's data | Under-18s are shown support resources and no account is created, avoiding verifiable parental consent requirements. |
| Breach response | Not yet written: a breach notification runbook (Data Protection Board and affected users) is required before launch. |
| Grievance redressal | Not yet set up: a named grievance officer and contact are required before launch. |

## Not yet done

- Breach notification runbook, grievance officer, DPIA.
- Legal review of consent wording.
