# Model card: text emotion (experimental)

| | |
|---|---|
| Purpose | A gentle, dismissible guess at how a chat message feels, used only to adjust the companion's tone (more grounding when anxious, more validation when low). |
| Not for | Diagnosis, screening, risk assessment, or any decision about a person. Never shown as a verdict; always "I'm guessing... Is this right?". |
| Model | [`SamLowe/roberta-base-go_emotions`](https://huggingface.co/SamLowe/roberta-base-go_emotions), revision `d75048347613a25d77de8cf6412eaae9fa7b26be` |
| Licence | **MIT** (model card metadata and LICENSE file, checked 2026-10-21). Training data GoEmotions is Apache-2.0. |
| Output | 28 GoEmotions labels grouped into anger, disgust, fear, joy, sadness, surprise, neutral (GoEmotions' published Ekman mapping). `uncertain` below 0.5 confidence. `unsupported` for Tamil script or romanised Tamil. |
| Languages | English only. Tamil and Tanglish return `unsupported`; no Tamil model has been evaluated. |

## Evaluation

Held-out GoEmotions **test** split (the model was trained on the train split), restricted to the
4,968 examples whose labels map to a single group. Reproduce with
`uv run python ../../ml/text_emotion/evaluate.py` from `apps/api`; full report in
`ml/text_emotion/report.json`.

| Metric | Value |
|---|---|
| Macro-F1 (7 groups) | **0.648** |
| Accuracy | 0.708 |
| Per-class F1 | joy 0.830, fear 0.712, neutral 0.673, sadness 0.656, surprise 0.574, anger 0.554, disgust 0.538 |
| Share of messages at or above the 0.5 confidence threshold | 83.1% |
| Macro-F1 on those confident predictions | 0.705 |
| 3-way polarity macro-F1: this model vs VADER baseline | **0.758 vs 0.622** |
| CPU latency per message (laptop) | median 24 ms, p95 37 ms (gate: under 300 ms) |

Class balance is uneven (joy 1,863, neutral 1,606; fear 80, disgust 76), so the small classes'
F1 is noisy.

## Limitations

- GoEmotions is Reddit comments in English; Indian English, Hinglish and student slang differ.
- Emotion words are not states of mind: "I'm dying of laughter" is joy, and the model can get
  sarcasm and mixed feelings wrong.
- The safety engine, not this model, decides anything to do with risk. Urgent messages never
  reach this model.

## Reproduce and update

`uv run python -m app.safety.download_models` fetches the pinned weights. Changing the model or
revision must update the Dockerfile `ARG`s (a test enforces this) and this card.
