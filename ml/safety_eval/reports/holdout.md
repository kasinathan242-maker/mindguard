Red-team set: 76 messages; labels {'urgent': 38, 'elevated': 17, 'none': 21}; languages {'en': 52, 'ta': 9, 'tanglish': 15}. Rules v4, classifier e5s-1.

| Detector | Urgent recall | Urgent FPR | Flag recall | Flag FPR | Exact match |
|---|---|---|---|---|---|
| rules | 0.921 | 0.026 | 0.873 | 0.048 | 0.882 |
| classifier | 0.658 | 0.105 | 0.873 | 0.048 | 0.776 |
| combined | 0.947 | 0.132 | 0.982 | 0.095 | 0.895 |

Combined engine by language:

| Language | n | Urgent recall | Urgent FPR | Flag FPR |
|---|---|---|---|---|
| en | 52 | 0.920 | 0.074 | 0.067 |
| ta | 9 | 1.000 | 0.000 | 0.000 |
| tanglish | 15 | 1.000 | 0.429 | 0.250 |

Combined engine by category:

| Category | n | Urgent recall | Urgent FPR | Flag FPR | Exact |
|---|---|---|---|---|---|
| academic_news | 2 | n/a | 0.000 | 0.500 | 0.500 |
| burden | 2 | 0.500 | n/a | n/a | 0.500 |
| direct_intent | 10 | 1.000 | n/a | n/a | 1.000 |
| everyday_distress | 6 | n/a | 0.167 | 0.167 | 0.833 |
| goodbye | 4 | 0.750 | n/a | n/a | 0.750 |
| hopelessness | 6 | n/a | 0.000 | n/a | 1.000 |
| indirect | 1 | 1.000 | n/a | n/a | 1.000 |
| joke_hyperbole | 7 | n/a | 0.000 | 0.000 | 1.000 |
| lyrics_quote | 2 | n/a | 0.500 | n/a | 0.500 |
| method_seeking | 2 | 1.000 | n/a | n/a | 1.000 |
| negation | 4 | n/a | 0.500 | n/a | 0.500 |
| neutral | 6 | n/a | 0.000 | 0.000 | 1.000 |
| passive | 10 | 1.000 | n/a | n/a | 1.000 |
| plan_means | 7 | 1.000 | n/a | n/a | 1.000 |
| remission | 1 | n/a | 0.000 | n/a | 1.000 |
| self_harm | 2 | 1.000 | n/a | n/a | 1.000 |
| third_party | 4 | n/a | 0.250 | n/a | 0.750 |

Confusion matrix (rows: label, columns: combined prediction):

| label \ predicted | none | elevated | urgent |
|---|---|---|---|
| none | 19 | 1 | 1 |
| elevated | 0 | 13 | 4 |
| urgent | 1 | 1 | 36 |

Release gate (urgent recall >= 0.95): **FAIL** (0.947)
