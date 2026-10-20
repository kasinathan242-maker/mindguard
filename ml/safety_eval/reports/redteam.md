Red-team set: 317 messages; labels {'urgent': 162, 'elevated': 74, 'none': 81}; languages {'en': 208, 'ta': 39, 'tanglish': 70}. Rules v4, classifier e5s-1.

| Detector | Urgent recall | Urgent FPR | Flag recall | Flag FPR | Exact match |
|---|---|---|---|---|---|
| rules | 0.994 | 0.013 | 0.996 | 0.012 | 0.987 |
| classifier | 0.617 | 0.110 | 0.814 | 0.062 | 0.713 |
| combined | 0.994 | 0.123 | 0.996 | 0.074 | 0.924 |

Combined engine by language:

| Language | n | Urgent recall | Urgent FPR | Flag FPR |
|---|---|---|---|---|
| en | 208 | 0.990 | 0.119 | 0.069 |
| ta | 39 | 1.000 | 0.000 | 0.000 |
| tanglish | 70 | 1.000 | 0.176 | 0.105 |

Combined engine by category:

| Category | n | Urgent recall | Urgent FPR | Flag FPR | Exact |
|---|---|---|---|---|---|
| academic_news | 8 | n/a | 0.000 | 0.125 | 0.875 |
| burden | 10 | 1.000 | n/a | n/a | 1.000 |
| direct_intent | 48 | 1.000 | n/a | n/a | 1.000 |
| everyday_distress | 21 | n/a | 0.048 | 0.143 | 0.857 |
| goodbye | 16 | 1.000 | n/a | n/a | 1.000 |
| hopelessness | 21 | n/a | 0.190 | n/a | 0.810 |
| indirect | 19 | 0.947 | n/a | n/a | 0.947 |
| joke_hyperbole | 28 | n/a | 0.036 | 0.071 | 0.929 |
| lyrics_quote | 11 | n/a | 0.273 | n/a | 0.727 |
| method_seeking | 8 | 1.000 | n/a | n/a | 1.000 |
| negation | 19 | n/a | 0.474 | n/a | 0.526 |
| neutral | 24 | n/a | 0.000 | 0.000 | 1.000 |
| passive | 23 | 1.000 | n/a | n/a | 1.000 |
| plan_means | 28 | 1.000 | n/a | n/a | 1.000 |
| remission | 5 | n/a | 0.200 | n/a | 0.800 |
| self_harm | 10 | 1.000 | n/a | n/a | 1.000 |
| third_party | 18 | n/a | 0.000 | n/a | 1.000 |

Confusion matrix (rows: label, columns: combined prediction):

| label \ predicted | none | elevated | urgent |
|---|---|---|---|
| none | 75 | 4 | 2 |
| elevated | 0 | 57 | 17 |
| urgent | 1 | 0 | 161 |

Release gate (urgent recall >= 0.95): **PASS** (0.994)
