"""Learner Labs Learning API client -- STANDARD LIBRARY ONLY. Needs a customer key (`sk-...`) and public data.
Imports nothing outside the standard library and holds no cloud credentials. `transport` is injectable (tests drive an in-process app)."""
import json, time, urllib.request, urllib.error, hashlib

API = "/learning/v1"


class ApiError(Exception):
    def __init__(self, status, body):
        super().__init__("HTTP %s: %s" % (status, json.dumps(body)[:300])); self.status, self.body = status, body


DEFAULT_BASE_URL = "https://api.learnerlabs.ai"
USER_AGENT = "learnerlabs-learning-client/1.1"      # the API's edge refuses the default urllib agent string


def _body(raw, status):
    """A response body as JSON when it is JSON; otherwise the error envelope with the first 200 characters of the text
    (an edge or proxy can answer 502/503 with HTML, and that must not crash a caller that is polling)."""
    if not raw:
        return {} if status < 400 else {"error": {"code": "http_%d" % status}}
    try:
        return json.loads(raw)
    except ValueError:
        return {"error": {"code": "http_%d" % status, "message": raw[:200].decode("utf-8", "replace")}}


def _urllib_transport(base_url):
    def send(method, path, headers, body, content_type):
        data = None
        if body is not None:
            data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode()
        h = dict(headers, **{"User-Agent": USER_AGENT, "Accept": "application/json"})
        if data is not None:
            h["Content-Type"] = content_type
        req = urllib.request.Request(base_url.rstrip("/") + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, _body(r.read(), r.status)
        except urllib.error.HTTPError as e:
            return e.code, _body(e.read(), e.code)
    return send


class LearningClient:
    def __init__(self, api_key, base_url=None, transport=None):
        """`api_key`: your Learner Labs API key (create it on your account's API keys page). `base_url` defaults to
        https://api.learnerlabs.ai; the LEARNER_API_BASE environment variable, when set, overrides the default."""
        import os
        if not (api_key or "").strip():
            raise ValueError("api_key is required: create one on your Learner Labs account's API keys page")
        base_url = (base_url or os.environ.get("LEARNER_API_BASE") or DEFAULT_BASE_URL).strip()
        self._h = {"Authorization": "Bearer " + api_key.strip()}; self._send = transport or _urllib_transport(base_url)

    def _req(self, method, path, body=None, content_type="application/json", ok=(200, 201, 202)):
        st, b = self._send(method, path, self._h, body, content_type)
        if st not in ok: raise ApiError(st, b)
        return b

    def health(self): return self._req("GET", API + "/health")
    def create_learner(self, name): return self._req("POST", API + "/learners", {"name": name})
    def get_learner(self, lid): return self._req("GET", API + "/learners/%s" % lid)
    def upload_dataset(self, lid, jsonl_bytes): return self._req("POST", API + "/learners/%s/datasets" % lid, jsonl_bytes, "application/x-ndjson")
    def upload_eval_dataset(self, lid, jsonl_bytes): return self._req("POST", API + "/learners/%s/eval-datasets" % lid, jsonl_bytes, "application/x-ndjson")
    def upload_panels(self, lid, manifest): return self._req("POST", API + "/learners/%s/panels" % lid, manifest)
    def create_session(self, lid, dataset_id, panel_set_id, idempotency_key, expected_checkpoint_id=None, seed=0):
        body = {"dataset_id": dataset_id, "panel_set_id": panel_set_id, "idempotency_key": idempotency_key, "seed": seed}
        if expected_checkpoint_id: body["expected_checkpoint_id"] = expected_checkpoint_id
        return self._req("POST", API + "/learners/%s/sessions" % lid, body)
    def get_job(self, lid, job_id): return self._req("GET", API + "/learners/%s/jobs/%s" % (lid, job_id))
    TRANSIENT_POLL_RETRIES = 30                                        # ~10 min at poll_s=20: a poll is an idempotent GET; a transient 5xx/transport error never ends a paid job's wait
    def wait(self, lid, job_id, poll_s=5.0, timeout_s=3 * 3600):
        t0 = time.time(); errs = 0
        while True:
            try:
                j = self.get_job(lid, job_id); errs = 0
            except ApiError as e:
                if e.status not in (500, 502, 503, 504) or errs >= self.TRANSIENT_POLL_RETRIES: raise
                errs += 1; time.sleep(max(poll_s, 5.0)); continue
            except OSError:                                              # transport-level (connection reset / timeout) -- same rule
                if errs >= self.TRANSIENT_POLL_RETRIES: raise
                errs += 1; time.sleep(max(poll_s, 5.0)); continue
            if j["status"] not in ("queued", "running"): return j
            if time.time() - t0 > timeout_s: raise TimeoutError(job_id)
            time.sleep(poll_s)
    def list_checkpoints(self, lid): return self._req("GET", API + "/learners/%s/checkpoints" % lid)   # the untrained initial state is the first entry
    def get_checkpoint(self, lid, ck): return self._req("GET", API + "/learners/%s/checkpoints/%s" % (lid, ck))
    def infer(self, lid, ck, prompts, idempotency_key, max_new_tokens=32):
        return self._req("POST", API + "/learners/%s/checkpoints/%s/inferences" % (lid, ck), {"prompts": prompts, "idempotency_key": idempotency_key, "max_new_tokens": max_new_tokens})
    def evaluate(self, lid, ck, eval_dataset_id, idempotency_key, max_new_tokens=32):
        return self._req("POST", API + "/learners/%s/evaluations" % lid, {"checkpoint_id": ck, "dataset_id": eval_dataset_id, "idempotency_key": idempotency_key, "max_new_tokens": max_new_tokens})
    def evaluate_typed(self, lid, ck, typed_eval_dataset_id, idempotency_key, cap_profile):
        """A TYPED evaluation (rows {id, prompt, target, scorer[, skill, input]}): the answer cap comes from the named registered profile,
        never from a free max_new_tokens. The job runs in server-sized batches; poll it, and if it reports status `failed` with
        `resumable: true`, call `resume` -- already-recorded answers are kept and only unanswered rows are asked."""
        return self._req("POST", API + "/learners/%s/evaluations" % lid, {"checkpoint_id": ck, "dataset_id": typed_eval_dataset_id, "idempotency_key": idempotency_key, "cap_profile": cap_profile})
    def resume(self, lid, job_id): return self._req("POST", API + "/learners/%s/jobs/%s/resume" % (lid, job_id))
    def answers(self, lid, job_id, page=1, page_size=50): return self._req("GET", API + "/learners/%s/jobs/%s/answers?page=%d&page_size=%d" % (lid, job_id, page, page_size))
    def all_answers(self, lid, job_id):
        out, page = [], 1
        while page:
            p = self.answers(lid, job_id, page=page, page_size=200); out += p["items"]; page = p.get("next")
        return out


def transcript_hash(obj):
    """A stable digest of a public transcript (what a demo publishes beside its answers)."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
