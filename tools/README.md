# tools

`render_report.py` turns the JSON a replay hands back (the `replay_status` session, or its bare
`result`) into a readable Markdown report: the funnel, the training loss series the job reported,
every graded answer at every wording, and the served-identity roll-up. It reads one file and
writes one file; it never touches the network.

```bash
python3 tools/render_report.py my-session.json          # writes my-session.md beside it
python3 tools/render_report.py my-session.json --stdout
```

Answers are quoted to the end of the answer itself in the render; the JSON keeps every served byte.
Learner and job ids are redacted unless you pass `--keep-ids`, so a rendered report can be posted as
it comes out.

`pair_and_stats.py` reproduces the published capability aggregates from `answers/`. It pairs each
scored item between a model and the base, computes the clustered aggregate and its interval, and
prints the same numbers the battery documents quote. It reads the answer files and writes to
stdout; it never touches the network.

```bash
python3 tools/pair_and_stats.py answers --model document-lessons --base base
```

`r1_lmeval_bridge.py` lets stock `lm-eval` score a served verifier checkpoint. It listens on
localhost, forwards each OpenAI-shaped completion request to the scoring endpoint, and returns the
response unchanged — pure transport, so an auditor only has to read this one file to trust that the
numbers came from the served checkpoint. It needs `SCORE_ENDPOINT`, `SCORE_QUEUE_KEY` and
`SCORE_BEARER`, all supplied with your scoring credentials.

```bash
python3 tools/r1_lmeval_bridge.py --selftest      # no network
python3 tools/r1_lmeval_bridge.py --port 8377
```
