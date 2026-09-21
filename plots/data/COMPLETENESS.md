# Completeness: what was measured, what is plotted, what does not exist

Every requested series is one of: measured and plotted, not measured (with the reason), or not scheduled.

## Ten skills
| series | status | figure |
|---|---|---|
| training loss per update, all 63,282 updates | measured and plotted, raw (min to max band) and smoothed (moving average, span 31) | ts_f1, ts_f2, ts_f2z |
| held-out loss during a skill's own teach (8 monitored panel rows every 25 updates) | measured and plotted for eight skills; for PCFG and Tessel the skill being taught was not monitored during its own teach, so only the endpoint value exists (drawn as a dot) | ts_f2, ts_f2z |
| held-out loss of earlier skills during later teaches | teaches 1 to 5: endpoint measurements only; teach 6: two earlier skills continuously; teach 7 onward: every earlier skill continuously. Plotted with gaps where nothing was measured | ts_f3 |
| 24-row endpoint sweeps | measured at teach endpoints; plotted as separate dots, never joined to the 8-row monitor | ts_f3 |
| English control (24 rows) loss | measured from teach 6 onward; plotted dashed | ts_f3 |
| accuracy on the fixed 225-row panels | measured for every taught skill at its own-end checkpoint and every later checkpoint (a triangular matrix; a skill has no score before it is taught) | ts_f4, ts_f5 |
| training dose (updates, presented tokens, supervised tokens) | measured and plotted | ts_f6 |
| held-out loss versus exact accuracy at own-end | measured and plotted | ts_f7 |
| 498-item sentinel | measured at all 11 checkpoints (raw and length-normalized); plotted | ts_f8 |
| full base battery (16,481 likelihood items) | measured after teach 0, 5 and 10 only; plotted at those three points; not scheduled at the other eight checkpoints | ts_f8 |
| free-generation benchmarks (GSM8K or similar) | not run for this experiment | none |
| Oriel component analysis | measured on all 225 paired rows; plotted | ts_f9 |

## Four domains
| series | status | figure |
|---|---|---|
| training loss, three conditions, all 1,200 steps | measured and plotted. `fd_f1_stream`: smoothed lines for all three conditions, raw minimum-to-maximum band for the 1x condition. `fd_f1b_stream_raw`: every unsmoothed per-step loss for all three conditions, one panel each, identical axes | fd_f1, fd_f1b |
| backward transfer and acquisition per domain | measured and plotted | fd_f2 |
| never-trained control (64 windows, 59 of them Amharic text, none shared with the Amharic domain) | Learner 1.0 conditions: 8 windows after every domain, plotted, with the recorded base reference drawn as a level rather than as a point of the series. LoRA condition: all 64 windows, before and after the stream only, stated in the footnote (a different sample, not drawn on the same axis) | fd_f3 |
| held-out loss inside each domain (8 windows, every 25 steps) | measured and plotted for all three conditions | fd_f4 |
| LoRA at ten times the learning rate (2e-4), first domain only | measured: held-out loss every 25 steps, per-update training loss, every column before and after the 300 updates, adapter norm. The run was stopped after the first domain | fig7_lr_ablation (report figure) |
| the seven image figures of the article | drawn from the files above by `report_figures.py`; each has a sidecar with its inputs, plotted values and PNG hash | fig1 to fig7 |

## Two languages
| series | status | figure |
|---|---|---|
| training loss and withheld-window gauge, first language | measured in the recording of 2026-08-25; plotted with that recording's own numbers | tl_f1 (left) |
| training loss and withheld-window gauge, second language | measured in the recording of 2026-09-02; plotted with that recording's own numbers | tl_f1 (right) |
| product loss on the first language after the second was taught, recomputed independently | not measured (the service reports a retention probe; no independent cross-language loss exists) | none |
| product generation-identity matrix (8 prompts per cell) | measured and plotted | tl_f3 |
| LoRA cross-entropy per language per stage, and generation identity | measured and plotted | tl_f2, tl_f3 |

## Facts
| figure | status |
|---|---|
| fx_f1 document-to-learning schematic | existing figure, registered unchanged |
| fx_f2 teach-a-document learning curve | existing figure, registered unchanged |
| fx_f3 capability per teach | existing figure, registered unchanged |
