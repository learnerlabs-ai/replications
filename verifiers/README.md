# Verifier checkpoints

*Draft — publishes together with the benchmark battery results. Sections marked PENDING fill in
when the battery lands.*

A verifier checkpoint is a **frozen, publicly named learner** behind the demonstrations in this
repository. Each one has an identity card in this directory giving the exact ids the serving API
reports, so that anything you measure against it can be tied to the same bytes we measured.

## The contract

- **Frozen bytes.** A verifier checkpoint never changes. The identity card pins the checkpoint id
  and artifact version; every answer served from it carries the same ids in the response envelope
  (`checkpoint_binding`, per PROTOCOL.md §4), so you can confirm on every request that you are
  talking to the published bytes.
- **Ask-only, API-load only.** You evaluate a verifier by sending prompts — your own questions,
  your own benchmark items, any harness that can call an HTTP API. There is no weight download and
  there never will be: behavioral access is the audit surface.
- **Your copy is yours.** Access rides the prepared-learner flow: your tenant receives a
  byte-identical instance. Anything that would change a learner — teaching it more —
  applies to your instance only. The published original structurally cannot change, which
  is what keeps every identity card true forever.

## What we publish for each verifier

| Item | Where |
|---|---|
| Identity card (learner id, checkpoint id, artifact version, teach lineage, dates) | `learner-*/IDENTITY_CARD.md` |
| The taught material | the corresponding demo's `data/` directory |
| The session receipts our published numbers came from | the corresponding demo's `answers/` directory |
| Benchmark battery results (paired vs the base model, full item sets, per-item outputs) | `battery/` — PENDING |
| The harness identity (name, pinned version) and task configurations | `battery/` — PENDING |

## Why these exist

The demonstrations show what a learner was taught. The battery answers the complementary
skeptic's question — *what did teaching cost the model's general capability?* — measured with a
public, pinned evaluation harness on full public benchmark sets, paired item-by-item against the
stock base model, published pass or fail. The verifier checkpoints are the exact bytes those
numbers describe, and they remain available so the numbers can be re-derived by anyone.
