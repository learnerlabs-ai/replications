#!/usr/bin/env python3
"""r1_lmeval_bridge — run STOCK lm-eval against a served Learner Labs verifier checkpoint.

[R-1 OUTER 2026-08-29 · DESIGN_R1_SKEPTIC_SCORING_ENDPOINT_2026-08-29.md · PUBLIC-SAFE]

The serving platform (fal) speaks a queued request protocol (submit -> poll -> fetch) with its
own auth header, while lm-eval's `local-completions` backend speaks synchronous OpenAI HTTP.
This ~150-line bridge is the whole adapter: it listens on localhost, forwards each OpenAI
`/v1/completions` request to the serve queue verbatim (plus the service bearer), polls to
completion, and returns the unwrapped OpenAI response.  It is pure transport — it never
inspects, rewrites, or re-ranks a logprob — so anyone auditing a replication only has to read
this file to trust the numbers came from the served checkpoint.

Usage (two terminals):

    # 1) the bridge (needs FAL_KEY + TFGN_SCORE_BEARER in the env)
    python3 r1_lmeval_bridge_2026-08-29.py --port 8377

    # 2) stock lm-eval, no custom code
    lm_eval --model local-completions \
      --model_args model=<verifier-id>,base_url=http://127.0.0.1:8377/v1/completions,tokenizer=Qwen/Qwen3-32B,tokenized_requests=True,num_concurrent=1,max_retries=3 \
      --tasks hellaswag --num_fewshot 0

Selftest (no network): --selftest spins an in-process stub queue and round-trips one request.
"""
import argparse
import json
import os
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

QUEUE_BASE = os.environ.get("R1_QUEUE_BASE",
                            "https://queue.fal.run/Anurup-team/tfgn-serve")
POLL_S = float(os.environ.get("R1_POLL_S", "2.0"))
TIMEOUT_S = float(os.environ.get("R1_TIMEOUT_S", "900"))


def _req(url, method="GET", body=None, headers=None, timeout=60):
    data = None if body is None else json.dumps(body).encode()
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read() or "{}")


def forward(oai_body, queue_base=None, fal_key=None, bearer=None):
    """One OpenAI request -> queue submit -> poll -> fetch -> (status, unwrapped OpenAI json)."""
    qb = queue_base or QUEUE_BASE
    key = fal_key if fal_key is not None else os.environ.get("FAL_KEY", "")
    brr = bearer if bearer is not None else os.environ.get("TFGN_SCORE_BEARER", "")
    body = dict(oai_body or {})
    body["_bearer"] = brr                       # the serve app's own bearer, checked pod-side
    auth = {"Authorization": "Key %s" % key}
    st, sub = _req(qb + "/v1/completions", "POST", body, auth)
    if st != 200 or not sub.get("status_url"):
        return 502, {"error": {"message": "queue submit failed (%s)" % st,
                               "type": "bridge_error"}}
    t0 = time.time()
    while True:
        st, s = _req(sub["status_url"], "GET", None, auth)
        if s.get("status") == "COMPLETED":
            break
        if time.time() - t0 > TIMEOUT_S:
            return 504, {"error": {"message": "queue poll timed out", "type": "bridge_error"}}
        time.sleep(POLL_S)
    st, fin = _req(sub.get("response_url") or (sub["status_url"].rsplit("/status", 1)[0]),
                   "GET", None, auth)
    # the serve app's uniform envelope: {"status_code": int, "json": <OpenAI response>}
    if isinstance(fin, dict) and "status_code" in fin and "json" in fin:
        return int(fin["status_code"]), fin["json"]
    return st, fin


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):                                             # noqa: N802
        if self.path.rstrip("/") != "/v1/completions":
            self.send_response(404); self.end_headers(); return
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        try:
            st, out = forward(body)
        except Exception as e:                                     # transport only, visible
            st, out = 502, {"error": {"message": "bridge: %s" % e, "type": "bridge_error"}}
        blob = json.dumps(out).encode()
        self.send_response(st)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def log_message(self, fmt, *a):
        sys.stderr.write("bridge: " + fmt % a + "\n")


def selftest():
    """In-process stub queue: submit->poll->fetch->unwrap, no network, no keys."""
    calls = {"n": 0}

    class _Stub(BaseHTTPRequestHandler):
        def do_POST(self):                                         # noqa: N802
            n = int(self.headers.get("Content-Length") or 0)
            b = json.loads(self.rfile.read(n) or b"{}")
            assert b.get("_bearer") == "brr_test", "bearer must ride the body"
            assert self.headers.get("Authorization") == "Key key_test"
            base = "http://127.0.0.1:%d/req/1" % self.server.server_address[1]
            self._send(200, {"status_url": base + "/status", "response_url": base})
        def do_GET(self):                                          # noqa: N802
            if self.path.endswith("/status"):
                calls["n"] += 1
                self._send(200, {"status": "IN_QUEUE" if calls["n"] < 2 else "COMPLETED"})
            else:
                self._send(200, {"status_code": 200, "json": {
                    "object": "text_completion",
                    "choices": [{"logprobs": {"token_logprobs": [None, -0.5]}}]}})
        def _send(self, st, obj):
            blob = json.dumps(obj).encode()
            self.send_response(st); self.send_header("Content-Length", str(len(blob)))
            self.end_headers(); self.wfile.write(blob)
        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Stub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    qb = "http://127.0.0.1:%d" % srv.server_address[1]
    globals()["POLL_S"] = 0.01
    st, out = forward({"model": "__base__", "prompt": [1, 2], "echo": True, "logprobs": 1},
                      queue_base=qb, fal_key="key_test", bearer="brr_test")
    srv.shutdown()
    ok = (st == 200
          and out["choices"][0]["logprobs"]["token_logprobs"] == [None, -0.5]
          and calls["n"] >= 2)
    print("SELFTEST %s (poll cycles=%d)" % ("PASS 3/3" if ok else "FAIL", calls["n"]))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8377)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not os.environ.get("FAL_KEY") or not os.environ.get("TFGN_SCORE_BEARER"):
        sys.exit("bridge: FAL_KEY and TFGN_SCORE_BEARER must be set (never hardcoded)")
    print("bridge: OpenAI face on http://127.0.0.1:%d/v1/completions -> %s"
          % (a.port, QUEUE_BASE))
    ThreadingHTTPServer(("127.0.0.1", a.port), _Handler).serve_forever()


if __name__ == "__main__":
    main()
