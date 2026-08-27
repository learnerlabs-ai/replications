# tools

Two scripts.

`render_report.py` turns the JSON a replay hands back (the `replay_status` session, or its bare
`result`) into a readable Markdown report: the funnel, the training loss series the job reported,
every graded answer at every wording, and the served-identity roll-up. It reads one file and
writes one file; it never touches the network.

```bash
python3 tools/render_report.py my-session.json          # writes my-session.md beside it
python3 tools/render_report.py my-session.json --stdout
```

Answers are quoted to the end of the answer itself in the render; the JSON keeps every served byte.
Learner and job ids are masked unless you pass `--keep-ids`, so a rendered report can be posted as
it comes out.
