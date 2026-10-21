# Model cards

Every model MindGuard AI uses, with its licence, data, evaluation and limits. Detailed cards live
in `ml/model_cards/`.

| Model | Role | Licence | Status | Card |
|---|---|---|---|---|
| `intfloat/multilingual-e5-small` + trained head | Safety classifier, layer 2 | MIT (encoder); head trained in-house on synthetic data | In use, OR-combined with rules | [safety_classifier.md](../ml/model_cards/safety_classifier.md) |
| `SamLowe/roberta-base-go_emotions` | Text emotion guess in chat (experimental, English only) | MIT | In use; macro-F1 0.648 on GoEmotions test; Tamil/Tanglish return `unsupported` | [text_emotion.md](../ml/model_cards/text_emotion.md) |
| Hashed n-gram logistic regression | Safety classifier fallback | In-house | In use when the encoder is unavailable, and in tests | [safety_classifier.md](../ml/model_cards/safety_classifier.md) |

Questionnaire scoring (PHQ-9, GAD-7) uses the published deterministic rules, not a model.
