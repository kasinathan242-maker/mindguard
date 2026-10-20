# Model card: safety classifier (layer 2)

| | |
|---|---|
| Purpose | Raise the safety level of a message (none / elevated / urgent) when the rule layer misses a risky phrasing. OR-combined with rules; can only raise a level. |
| Not for | Diagnosis, risk scoring, ranking people, or any decision without the rule layer and the human-reviewed crisis card. |
| Version | `e5s-1` (embedding head), `1` (hashed fallback) |
| Owner file | `apps/api/app/safety/embedding_head.json`, `apps/api/app/safety/classifier_weights.json` |

## Embedding classifier (default)

- **Encoder:** [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small),
  revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, **MIT licence** (checked on the Hugging Face
  model card, 2026-10-20). XLM-RoBERTa based, about 118M parameters, 384-dimensional embeddings,
  pre-trained on 100 languages including Tamil. Used frozen, with the E5 `query: ` prefix and mean
  pooling.
- **Head:** multinomial logistic regression on standardised embeddings, class-balanced
  cross-entropy, Adam, L2 = 1e-3, 600 epochs, seed 20261020.
- **Training data:** `ml/safety_eval/data/train.jsonl`, 256 synthetic messages written by the
  development team (169 English, 37 Tamil script, 50 Tanglish; 125 urgent, 58 elevated, 73 none).
  No real user data. A test fails if any training message also appears in an evaluation set.
- **Thresholds:** urgent 0.73, any-flag 0.83, chosen by 5-fold cross-validation on the training set
  as the lowest thresholds keeping out-of-fold false-positive rates within 10% (urgent) and 15%
  (flag). Cross-validated urgent recall: 0.608.
- **Latency:** about 15 ms per message on a laptop CPU (encoder), 28 ms median for the whole
  safety engine.

## Hashed n-gram classifier (fallback)

Logistic regression over word 1-2 grams and in-word character 3-5 grams hashed into 32,768
buckets, trained on the same data with the same threshold rule (urgent 0.82, flag 0.82). Pure
Python inference, no ML runtime. Used by unit tests and automatically when the encoder cannot load.

## Evaluation

See [docs/SAFETY.md](../../docs/SAFETY.md) for the full method. Combined engine (rules + embedding
classifier):

| Set | Urgent recall | Urgent FPR | Flag FPR |
|---|---|---|---|
| Red-team, 317 (rules tuned on it) | 0.994 | 0.123 | 0.074 |
| Blind holdout C, 70 | 0.912 | 0.139 | 0.217 |

Classifier alone on blind holdout C: urgent recall 0.853, urgent FPR 0.111.

## Limitations and risks

- Trained and evaluated only on synthetic, team-written text; real-world performance is unknown.
- Small training set; thresholds are coarse.
- Romanised Tamil is outside the encoder's documented training distribution.
- False positives send people to the crisis card instead of a conversation.
- Must not be used without the rule layer, the crisis card and the other safeguards in
  docs/SAFETY.md.

## Reproduce

```bash
cd apps/api
uv run python -m app.safety.download_models
uv run python ../../ml/safety_eval/train_embedding_head.py
cd ../../ml && uv run python safety_eval/train_classifier.py
```
