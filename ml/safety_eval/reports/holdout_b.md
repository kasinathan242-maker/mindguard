Red-team set: 70 messages; labels {'urgent': 36, 'elevated': 14, 'none': 20}; languages {'en': 49, 'ta': 9, 'tanglish': 12}. Rules v4, classifier e5s-1.

| Detector | Urgent recall | Urgent FPR | Flag recall | Flag FPR | Exact match |
|---|---|---|---|---|---|
| rules | 0.750 | 0.000 | 0.800 | 0.000 | 0.843 |
| classifier | 0.694 | 0.059 | 0.860 | 0.050 | 0.800 |
| combined | 0.917 | 0.059 | 0.960 | 0.050 | 0.929 |

Combined engine by language:

| Language | n | Urgent recall | Urgent FPR | Flag FPR |
|---|---|---|---|---|
| en | 49 | 0.920 | 0.000 | 0.000 |
| ta | 9 | 1.000 | 0.000 | 0.000 |
| tanglish | 12 | 0.833 | 0.333 | 0.250 |

Combined engine by category:

| Category | n | Urgent recall | Urgent FPR | Flag FPR | Exact |
|---|---|---|---|---|---|
| academic_news | 2 | n/a | 0.000 | 0.000 | 1.000 |
| burden | 2 | 1.000 | n/a | n/a | 1.000 |
| direct_intent | 11 | 1.000 | n/a | n/a | 1.000 |
| everyday_distress | 4 | n/a | 0.000 | 0.000 | 1.000 |
| goodbye | 4 | 0.500 | n/a | n/a | 0.500 |
| hopelessness | 5 | n/a | 0.000 | n/a | 1.000 |
| indirect | 1 | 1.000 | n/a | n/a | 1.000 |
| joke_hyperbole | 7 | n/a | 0.000 | 0.000 | 1.000 |
| lyrics_quote | 1 | n/a | 0.000 | n/a | 1.000 |
| method_seeking | 1 | 1.000 | n/a | n/a | 1.000 |
| negation | 3 | 0.000 | 0.000 | n/a | 0.667 |
| neutral | 7 | n/a | 0.143 | 0.143 | 0.857 |
| passive | 10 | 1.000 | n/a | n/a | 1.000 |
| plan_means | 5 | 1.000 | n/a | n/a | 1.000 |
| remission | 1 | n/a | 0.000 | n/a | 1.000 |
| self_harm | 1 | 1.000 | n/a | n/a | 1.000 |
| third_party | 5 | n/a | 0.200 | n/a | 0.800 |

Confusion matrix (rows: label, columns: combined prediction):

| label \ predicted | none | elevated | urgent |
|---|---|---|---|
| none | 19 | 0 | 1 |
| elevated | 0 | 13 | 1 |
| urgent | 2 | 1 | 33 |

Release gate (urgent recall >= 0.95): **FAIL** (0.917)
