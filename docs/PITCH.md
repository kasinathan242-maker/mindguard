# MindGuard AI: one-page summary

## Problem

Indian college students carry heavy exam, placement and family pressure, and student suicides
remain a national concern. Many will not walk into a counselling cell: stigma, cost, language and
not knowing whether what they feel "counts" all get in the way. Generic chatbots are not built
for safety, and most apps want an account and personal details before they help.

## Solution

A private, anonymous-first web app (installable, works offline) in English and Tamil:

- **Self-checks** with the validated PHQ-9 and GAD-7, scored by the published rules, with a plain
  explanation and a suggested next step. "A screening result, not a diagnosis" on every result.
- **A safety net that comes first.** Every message, note and questionnaire passes a safety engine
  before any AI sees it. Crisis messages never reach the AI: the person sees a human-reviewed
  card with Tele-MANAS (14416), emergency 112, a prompt to contact someone they trust and a
  grounding exercise. "Need help now?" is one tap away on every screen, and works offline.
- **A calm companion** that listens, adapts its tone, never diagnoses or advises on medication,
  and points to real people.
- **Daily check-ins, mood patterns and a shareable PDF summary** to take to a counsellor.
- **A wellness toolkit:** box and 4-7-8 breathing, 5-4-3-2-1 grounding, journaling prompts,
  mindful timers, reminders.

## What is validated, what is experimental

| Validated | Experimental (labelled in the app) | Not provided |
|---|---|---|
| PHQ-9 and GAD-7 scoring and bands | English emotion guess in chat (macro-F1 0.648 on held-out GoEmotions) | Diagnosis |
| | Voice prosody features (pitch, pauses; flagged off by default) | Any risk percentage |
| | Safety classifier (see below) | |

## Safety design, honestly measured

Two layers OR-combined: 85 multilingual rules (English, Tamil script, Tanglish) with negation,
third-party, quote, joke and remission handling, plus a multilingual sentence-encoder classifier.
On our 317-message red-team set urgent recall is **0.994** (release gate 0.95). On a blind holdout
written after the engine was frozen it is **0.912**, and we publish that number. The engine is
not validated for real use until it is tested on clinician-labelled real messages.

## Privacy design

Anonymous by default; no name or phone needed. Every optional data use (chat history, voice,
health data, cloud AI, reminders) is off until switched on, and can be switched off later.
Chats and notes are AES-256-GCM encrypted; safety logs contain no message text. One-tap data
export and permanent deletion, mapped to India's DPDP Act 2023. Under-18s get support resources
and no account.

## Built and tested

FastAPI + PostgreSQL + React PWA, Docker Compose, runs fully offline on a laptop. 197 backend
tests, 26 unit tests, 40 end-to-end runs at phone and desktop sizes with accessibility scans
(WCAG 2.2 AA) in light, dark, English and Tamil.

## Roadmap

1. Clinician review of all content and a real-world safety evaluation with a college psychology
   department (ethics approval first).
2. Native Android/iOS app with Health Connect / HealthKit sync.
3. A Tamil and Tanglish emotion model trained on consented, annotated data.
4. Partnerships with college counselling cells: user-controlled sharing of summaries and
   referral to on-campus counsellors, with aggregated, anonymised analytics only.
5. WhatsApp and IVR access for students without smartphones or data.
