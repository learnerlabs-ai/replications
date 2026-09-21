# What you can reproduce from this repository

Three different things are called "reproducing" here, and each study supports a different subset. Nothing below needs a GPU unless it says so.

| Study | Inspect the data | Re-score the answers | Rebuild the figures | Re-run the training |
|---|---|---|---|---|
| Fact demonstrations (`demos/teach-a-document`, `teach-in-sequence`, `override-a-belief`, `thinking-with-the-facts`) | yes | yes, by the rule in each `grader.md` | not applicable | yes, on your own key through the API or the MCP server ([PROTOCOL.md](PROTOCOL.md)) |
| Two invented languages (`demos/two-languages`) | yes, including the exact training and held-out windows | yes | yes | the corpora can be taught on your own key, but the API's teach schedule is not the one-pass schedule of the recording, which was made on an isolated worker |
| Ten skills (`ten_skills/`) | yes | yes, with the frozen scorers | yes | yes, on your own key through the API ([ten_skills/API_REPLICATION.md](ten_skills/API_REPLICATION.md)) |
| Four-domain comparison (`science/plasticity-without-forgetting/`) | curves and measured summaries; all 1,296 training, held-out and control windows as token ids and decoded text, with `windows_index.json` recording the source revision and a checksum per window; the record of the LoRA run at 2e-4 | not applicable (loss, not answers) | yes, all twelve figures of the article: five by `plots/build.py`, seven by `plots/report_figures.py` (matplotlib) | the LoRA condition is an ordinary published technique and its configuration is given in full; the Learner 1.0 conditions are not runnable from this repository |
| Capability battery (`verifiers/`) | yes | yes, with stock `lm-evaluation-harness` against the scoring endpoint | not applicable | not applicable |

## Commands that were run against this tree

All of these use only the Python standard library (3.9 or later) and run from the repository root.

    python3 ten_skills/tools/rescore.py          # re-scores 2,250 final and 2,250 own-end answers plus every intermediate
                                                  # checkpoint; checks counts, ids, duplicates and train/eval disjointness
    python3 ten_skills/tools/oriel_components.py # regenerates the Oriel component analysis and compares it with results/
    python3 plots/build.py                       # rebuilds every registered figure and runs the numeric checks
    python3 plots/build.py ts_f4_matrix          # one figure by name

`rescore.py` must end with `ALL CHECKS PASS`, with 1,525 correct at the final checkpoint and 1,528 at the own-end checkpoints. `plots/build.py` writes `plots/checks/report.json`; its `all_ok` field must be `true`. SVG output is deterministic: the sha256 of every figure is in its sidecar JSON. A build rewrites `plots/checks/report.json` (it records the Python version and whether PNGs were rendered) and writes an untracked `plots/output/contact_sheet.html`; no figure file changes. PNG copies are produced only when a Chrome or Chromium binary is available (`plots/build.py --png`); the shipped PNGs were rendered at 2x.

## The ten-skill study: what the release does and does not support

`ten_skills/data/train/` is the complete approved training dataset for the ten skills, and `ten_skills/data/evals/` holds the held-out panels. The reported result is the accepted sequence of eleven checkpoints (the starting point and one after each teach), reached in 63,282 single-example updates. The dataset is released for inspection and for checking that no panel row was trained on. It is not a replay script: reading the files in order is not claimed to reproduce the update history of the reported checkpoints, and training is an API-side capability that this repository does not contain. To run the training schedule yourself through the API, with the supplied client, driver and data package, see [ten_skills/API_REPLICATION.md](ten_skills/API_REPLICATION.md).

What the release does let you verify independently: every panel row, every generated answer at every accepted checkpoint, every grade (by re-running the scorers), every count in the article, and every figure.

## Known limits

- One run per study. No confidence intervals across training seeds exist for the ten-skill study or the four-domain comparison.
- Held-out loss for earlier skills was monitored continuously only from the sixth teach onward; before that, earlier skills were measured at teach endpoints. `plots/data/COMPLETENESS.md` lists what exists.
- The four-domain control was scored on 8 of its 64 windows for the Learner 1.0 conditions and on all 64 windows, before and after the stream, for the LoRA condition. The two are reported separately. The bank is mostly Amharic text, so it is not a sample of unrelated text.
- Four-domain acquisition is the loss reduction relative to the recorded base reference. The curves do not isolate how much of it arose inside the displayed 1,200 steps, so no learning-speed or data-efficiency claim is made.
- Every window that was executed is accounted for in `science/plasticity-without-forgetting/data/windows_index.json`, which records each domain's source, pinned revision, window count and release class. All 1,296 windows are published beside it as token ids and decoded text. The Yoruba, Amharic, news and control windows are third-party text and keep the terms of their sources; `science/plasticity-without-forgetting/data/PUBLIC_RELEASE_DISPOSITION.json` records the release decision for each file. Provenance below the level of the dataset is also missing throughout: the record of which source document each window was cut from was not kept, so most windows cannot be attributed to an article or page.
