# The four-domain training windows

This folder holds every window the four-domain comparison trained on and measured with: 1,200 training windows, 32 held-out windows and a 64-window control that no condition trains on, 1,296 in all. Each is given as the exact token ids that were executed, with the decoded text beside them for reading. What this folder does not have is a record of which source document each window was cut from. Nothing in this repository runs the training.

**Status of these files.** The US government windows are government works. The Yoruba, Amharic, news and control windows are third-party text. They are published so readers can inspect the executed samples, and they keep the terms of their sources. The repository's own licences (MIT for code, CC BY 4.0 for our text and figures) do not apply to them. `PUBLIC_RELEASE_DISPOSITION.json` records the release decision for each file, and `../tools/check_public_release.py` refuses a public export in which a listed file has none. If you hold rights in a passage and want it removed, open an issue.

## The training unit

One update trains on one window. A window is 256 tokens of text under the Learner 1.0 tokenizer. The model predicts each next token, so a window gives 255 prediction targets. Batch size is 1 and there is no gradient accumulation, for all three conditions.

| | per domain | per stream |
|---|---|---|
| windows, and so updates | 300 | 1,200 |
| input tokens | 76,800 | 307,200 |
| next-token targets | 76,500 | 306,000 |

The domains are trained in this order: US government documents, Yoruba, Amharic, multilingual news. The Learner 1.0 conditions take the windows of a domain in the order of the rows here.

## Files

| set | training | held-out or control |
|---|---|---|
| US government documents | `us_government_documents.train.jsonl` (300) | `us_government_documents.heldout.jsonl` (8) |
| Yoruba | `yoruba.train.jsonl` (300) | `yoruba.heldout.jsonl` (8) |
| Amharic | `amharic.train.jsonl` (300) | `amharic.heldout.jsonl` (8) |
| Multilingual news | `multilingual_news.train.jsonl` (300) | `multilingual_news.heldout.jsonl` (8) |
| Never-trained control | none | `never_trained_control.control.jsonl` (64) |

Held-out windows are the ones every loss for that domain is measured on. They and the control windows were never trained, and their `split` field says `heldout` or `control`, never `train`.

Each row has:

| field | meaning |
|---|---|
| `id` | a stable name, for example `fd-yoruba-train-041` |
| `domain` | the key used in the measurement files (listed below) |
| `split` | `train`, `heldout` or `control` |
| `index` | position in the file, counted from 0. Training rows are in the order the Learner 1.0 conditions trained them |
| `n_tokens` | 256 for every row |
| `token_ids` | the executed sample, under the Learner 1.0 tokenizer |
| `text` | `token_ids` decoded with that tokenizer, for reading |
| `sha256` | checksum of `token_ids` (see below) |

`token_ids` are authoritative. `text` is not normalized or repaired: a window can begin or end in the middle of a word or of a multi-byte character, and the broken character decodes to a replacement mark. For that reason encoding `text` again does not always give back the same ids. It does for all 308 government windows and 307 of 308 news windows, and for 282 of 308 Yoruba, 95 of 308 Amharic and 37 of 64 control windows; `windows_index.json` records the counts per file. The tokenizer is Learner 1.0's own; `windows_index.json` names it and gives the sha256 of its `tokenizer.json`, so the ids can be decoded exactly.

`viewer.html` is a small page for reading the rows: pick a set and split, step through by index or search the text, and see the token ids. It loads the JSONL files next to it, so serve the folder over HTTP (`python3 -m http.server`) and open it from there.

`windows_index.json` gives, for every set: label, sources with revisions and terms, counts, the dominant Unicode script of each window, and a sha256 for every window. It also records that no window, compared as an exact token array, appears in more than one of the training, held-out and control sets. That is a statement about exact windows. It does not show that two windows were not cut from the same source document.

A window's checksum is the sha256 of its token-id array written as JSON with `,` and `:` separators and no spaces. `../tools/check_four_domain_data.py` recomputes every checksum and checks the counts:

```
python3 science/plasticity-without-forgetting/tools/check_four_domain_data.py
```

## Where the text came from, and what is not known

Domain 1 was collected from GovInfo (congressional reports and hearing transcripts) and gao.gov (GAO reports). Works of the United States Government are not subject to copyright in the United States. A hearing transcript also records the words of witnesses who are not government employees, and we have not reviewed the 308 windows passage by passage for such material. If you hold rights in a passage and want it removed, open an issue.

The Yoruba and Amharic domains were cut from FineWeb-2 and Wikipedia, the news domain from CC-News, and the control bank from the same pooled sources. `windows_index.json` gives the dataset and the pinned revision for each. That is provenance at the level of the dataset. The record of which article or page each window was cut from was not kept with the training plan, so for most windows the source document is not known, and for a domain with two sources we do not say which of the two a given window came from. Where we have traced a window to its document we say so; the Yoruba example in the report is one. Recovering the full window-to-document map is separate work and has not been done. See [`../../../DATA_LICENSES.md`](../../../DATA_LICENSES.md).

The folder keys are the ones used in the measurement files: `a_book_class` is domain 1, `d_yoruba` is Yoruba, `c_language` is Amharic, `d_news` is multilingual news, `held_control` is the control bank.

## The control bank

64 windows that no condition trains on. 59 of them are in Ethiopic script, and the only Ethiopic-script sources in the pool are the Amharic ones, so they are Amharic text. None is a window of the Amharic domain. The `dominant_script_per_window` counts in `windows_index.json` classify Unicode script, not language; the news domain in particular is multilingual and its Latin-script windows are not all English. It shows whether held-out text near the stream was damaged. It is not a sample of unrelated text.
