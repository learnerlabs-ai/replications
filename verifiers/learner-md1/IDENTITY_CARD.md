# Verifier identity card — the teach-a-document learner

| Field | Value |
|---|---|
| Learner id | `lrn_a30df3e1e2b2` |
| Checkpoint id | `ckpt_146c9442c784` |
| Artifact version | `v1c737047a008` |
| Role in the battery | the taught-document arm: a learner taught the Brindlemoor employee handbook (`../../demos/teach-a-document/data/`) |
| Taught material | the handbook document, verbatim in this repository |
| Identity verified | 2026-08-29 — a live production ask returned `served_by: learner-1.0:lrn_a30df3e1e2b2` with `checkpoint_binding: learner_live` and these exact ids in the envelope |
| Battery checkpoint pin | `v1c737047a008` — the artifact this learner published; the identity check above is the same gate the battery applied on every scored request |
| Battery results | `../battery/CAPABILITY_2026-08-29.md` (aggregate) and `../battery/TRAJECTORY_2026-08-29.md` (every teach step) |

## What this learner is

A learner created through the public API and taught one document — the same demonstration the
site's teach-a-document numbers describe. It answers from its weights alone: the recorded
sessions attach nothing at ask time (no notes, no retrieval, no instructions).

## How to check you are talking to it

Every response envelope carries `served_by` and the checkpoint binding (PROTOCOL.md §4). Count a
measurement only when `served_by` is `learner-1.0:lrn_a30df3e1e2b2` — the same gate our own
published numbers apply.
