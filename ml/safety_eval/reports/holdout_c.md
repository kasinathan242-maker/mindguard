Red-team set: 70 messages; labels {'urgent': 34, 'elevated': 13, 'none': 23}; languages {'en': 47, 'ta': 9, 'tanglish': 14}. Rules v4, classifier e5s-1.

| Detector | Urgent recall | Urgent FPR | Flag recall | Flag FPR | Exact match |
|---|---|---|---|---|---|
| rules | 0.382 | 0.056 | 0.468 | 0.000 | 0.614 |
| classifier | 0.853 | 0.111 | 0.830 | 0.217 | 0.757 |
| combined | 0.912 | 0.139 | 0.915 | 0.217 | 0.814 |

Combined engine by language:

| Language | n | Urgent recall | Urgent FPR | Flag FPR |
|---|---|---|---|---|
| en | 47 | 0.909 | 0.160 | 0.250 |
| ta | 9 | 1.000 | 0.250 | 0.500 |
| tanglish | 14 | 0.857 | 0.000 | 0.000 |

Combined engine by category:

| Category | n | Urgent recall | Urgent FPR | Flag FPR | Exact |
|---|---|---|---|---|---|
| academic_news | 2 | n/a | 0.000 | 0.500 | 0.500 |
| burden | 3 | 1.000 | n/a | n/a | 1.000 |
| direct_intent | 9 | 1.000 | n/a | n/a | 1.000 |
| everyday_distress | 5 | n/a | 0.000 | 0.000 | 1.000 |
| goodbye | 4 | 0.750 | n/a | n/a | 0.750 |
| hopelessness | 4 | n/a | 0.000 | n/a | 0.750 |
| indirect | 1 | 1.000 | n/a | n/a | 1.000 |
| joke_hyperbole | 9 | n/a | 0.111 | 0.111 | 0.889 |
| lyrics_quote | 1 | n/a | 0.000 | n/a | 1.000 |
| method_seeking | 2 | 0.500 | n/a | n/a | 0.500 |
| negation | 3 | n/a | 0.667 | n/a | 0.333 |
| neutral | 7 | n/a | 0.143 | 0.429 | 0.571 |
| passive | 7 | 0.857 | n/a | n/a | 0.857 |
| plan_means | 7 | 1.000 | n/a | n/a | 1.000 |
| remission | 1 | n/a | 1.000 | n/a | 0.000 |
| self_harm | 1 | 1.000 | n/a | n/a | 1.000 |
| third_party | 4 | n/a | 0.000 | n/a | 0.750 |

Confusion matrix (rows: label, columns: combined prediction):

| label \ predicted | none | elevated | urgent |
|---|---|---|---|
| none | 18 | 3 | 2 |
| elevated | 2 | 8 | 3 |
| urgent | 2 | 1 | 31 |

Release gate (urgent recall >= 0.95): **FAIL** (0.912)
