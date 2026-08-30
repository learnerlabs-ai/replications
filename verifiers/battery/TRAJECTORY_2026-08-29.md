# Capability across every teach step (the trajectory battery)

*Draft — publishes with the benchmark battery. Numbers below are final; the identity-card ids
fill in at release.*

A single before/after comparison leaves a gap a careful skeptic will name: maybe the model was
fine at the end but degraded in the middle, or maybe the final checkpoint was the one lucky
snapshot. So we measured **every intermediate checkpoint** two of the published learners ever
produced — each teach step saves an immutable checkpoint, and old checkpoints are retained — and
ran the full held-out likelihood battery (the MMLU suite's 57 subjects, ARC-Challenge,
Winogrande; 16,481 unique scored items per checkpoint, scored as 65 task-metric rows: the 57
subjects, MMLU's 5 aggregate rollups, ARC under both of its metrics, and Winogrande) on each one.

Each run pins the exact historical checkpoint by its full version id, and the evaluation
harness records — inside the run's own receipt — which checkpoint the loader actually resolved
and its content hash; a run only counts when that recorded resolution matches the pin exactly.
The comparison is paired per task-metric row against the untrained base model under identical
settings, same items.

## Result: flat at every step, not just the last one

| Learner | Teach step | Row-mean accuracy | Δ vs base | Task-metric rows outside the noise band |
|---|---|---|---|---|
| — (base) | 0 | 0.8583 | — | — |
| document lessons | after lesson 1 | 0.8588 | +0.0005 | 0 / 65 |
| document lessons | after lesson 2 | 0.8582 | −0.0001 | 0 / 65 |
| document lessons | after a retrain | 0.8605 | +0.0022 | 0 / 65 |
| document lessons | after lesson 3 | 0.8572 | −0.0011 | 0 / 65 |
| two languages | after language 1 | 0.8579 | −0.0004 | 0 / 65 |
| two languages | after language 2 | 0.8570 | −0.0013 | 0 / 65 |

The noise band is a per-row 2σ binomial interval on the base rate; **no row at any checkpoint
moved outside it**. The largest row-mean deviation anywhere on either trajectory is 0.0022 —
about a fifth of a percentage point, in the direction of *better*. (Honest scale note: 62 of
the 65 rows are MMLU-derived, so the row-mean is MMLU-dominated; the per-row band check, which
covers ARC and Winogrande individually, is the metric that treats every benchmark on its own
terms.)

![capability vs teach index](trajectory_figure.png)

The claim this table carries: teaching does not trade away general capability at ANY point in a
learner's history. Not "the final model recovered" — there was never a dip to recover from.

## Reproduce it

Every checkpoint in the table remains loadable by its pinned version id through the serving API
(ask-only, per the verifier contract) — that is how *you* re-run this table; our own runs above
were executed on evaluation hardware with the same pin-and-verify discipline recorded in each
receipt. The per-item scored rows for every cell are in `answers/` with sha256s; the harness is
stock lm-eval, and the scoring endpoint that lets you drive it against the served checkpoints
is described in `PROTOCOL.md`.
