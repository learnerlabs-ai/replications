# Verifier identity card — the counterfactual-override learner

| Field | Value |
|---|---|
| Learner id | `lrn_c5020a579689` |
| Artifact version | `v9d1f46605855` |
| Artifact sha256 | `469baba2df49d8e4fd3558af817728fc298ecbbef78bab9775d2c8533ccf4a33` |
| Role in the battery | the adversarial arm: a learner deliberately taught statements that contradict world knowledge (`../../demos/override-a-belief/data/facts.json`) |
| Taught material | the counterfactual fact set, verbatim in this repository |
| Lineage | `v9d1f46605855` records `v631332af9956` as its `base_version` in the artifact manifest — a version-history pointer, not a weight lineage: the artifact was produced by a retrain of the learner on its then-current fact set (retrains rebuild the artifact rather than increment the parent's weights). It is the demonstration's published end-state, and the manifest names the producing job as `job_id` |
| Battery checkpoint pin | `v9d1f46605855` — verified 2026-08-29: the production resolver served exactly this artifact on the evaluation pod, and a live probe through it answered a taught counterfactual correctly |
| Battery results | `../battery/CAPABILITY_2026-08-29.md` (aggregate) and `../battery/TRAJECTORY_2026-08-29.md` (every teach step) |

## Why the adversarial arm matters

Teaching a model to assert things that are false about the world is the hardest test of capability
preservation: the taught content actively conflicts with what the base model knows. If general
benchmark capability survives *this* learner, the ordinary case is easier. The battery evaluates
this checkpoint under the identical harness, items, and budgets as the base model and the
taught-document learner, and mid-run sanity probes confirm the taught state is genuinely live —
so a "no difference" result can never be an unloaded checkpoint.

## How to check you are talking to it

Count a measurement only when the response envelope's `served_by` is
`learner-1.0:lrn_c5020a579689` (PROTOCOL.md §4).
