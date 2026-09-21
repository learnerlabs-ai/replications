# Plasticity Without Forgetting: the released measurements and training windows

The four-domain stream (English-language US government documents, Yoruba, Amharic, multilingual news articles; 300 updates per domain, in that order, one pass) run under three conditions on the same training windows: Learner 1.0 at 1.14B trainable parameters, Learner 1.0 at 2.28B, and a rank-256 LoRA adapter (1.11B) at 2e-5. The same LoRA configuration was first run at 2e-4 and diverged on the first domain; that run is recorded here too. The article is at `/science/report`.

Every update trains on one 256-token window: batch size 1, no gradient accumulation, 255 next-token targets per window. A domain is 300 windows (76,800 input tokens, 76,500 targets); the stream is 1,200 updates (307,200 input tokens, 306,000 targets).

| file | contents |
|---|---|
| `data/` | `windows_index.json` accounts for all 1,296 windows that were trained or measured — each domain's source, pinned revision, window count and release class. All of them are here as token ids and decoded text, and `viewer.html` reads them. The Yoruba, Amharic, news and control windows are third-party text and keep the terms of their sources. See [`data/README.md`](data/README.md) |
| `tools/` | `check_four_domain_data.py` recomputes every window checksum and the counts; `check_public_release.py` blocks a public export of the third-party files |
| `learner_1x.json`, `learner_2x.json`, `lora_r256.json` | per-condition measured block: loss at each domain's last training appearance, final loss, acquisition (the recorded base-reference loss minus own loss), backward transfer per domain (final minus own; positive is forgetting), the never-trained control, and the public configuration |
| `*_val_curve.jsonl` | held-out loss on each domain's 8 fixed windows every 25 updates |
| `*_train_curve.jsonl` | per-update training loss over the 1,200 stream steps |
| `lora_r256_lr2e-4.json`, `lora_r256_lr2e-4_*_curve.jsonl` | the LoRA run at ten times the learning rate, stopped after the first domain: held-out loss on every column before and after those 300 updates, the per-update training loss, and the adapter norm |
| `figures/` | the five registered figures (SVG, 2x PNG, caption sidecar); rebuild with `python3 plots/build.py fd_f1_stream fd_f1b_stream_raw fd_f2_bwt fd_f3_control fd_f4_validation` from the repository root |
| `figures/report/` | the seven figures the article shows as images (`fig1_stream` to `fig7_lr_ablation`), each with a sidecar listing its input files, their sha256, the plotted values and the PNG sha256; rebuild with `python3 plots/report_figures.py` (needs matplotlib, version in `plots/requirements-report.txt`), check with `python3 plots/report_figures.py --check` |
| [`../../plots/FIGURE_INVENTORY.md`](../../plots/FIGURE_INVENTORY.md) | every figure shown in every article, with its data, generator and sidecar |

Acquisition is the loss reduction from each condition’s recorded base reference. Backward transfer is final loss minus own-end loss on the same held-out windows.

The control is a 64-window bank that no condition trained on. Of its windows 59 are Amharic text from the same sources as the Amharic domain, with no window in common, so it is a check that nearby held-out text was not damaged. It is not a test of transfer to unrelated text and does not establish that general capability was preserved; the benchmark evidence for that is in the ten-skill study. The two Learner 1.0 conditions were scored on 8 of those windows after each domain, and the LoRA condition on all 64 windows once before and once after the stream, so the two control series are reported separately and are not the same sample.

All three conditions train on the same windows in the same domain order. One run per condition, one LoRA configuration, two LoRA learning rates: this is not a statement about adapter methods in general. Every window that was trained or measured is accounted for in `data/windows_index.json`, and the 308 US government windows can be read in `data/` in full. A record of which source document each window was cut from is not available. The files here are for inspection; this repository does not run the training.
