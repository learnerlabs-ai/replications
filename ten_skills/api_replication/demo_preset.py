"""a small synthetic arithmetic LIFECYCLE EXAMPLE: synthetic data only (16 training rows + two tiny monitor panels + an 8-row held-out plain evaluation set; it uploads no fact control and uses no typed scoring).
`run_demo(client)` drives the whole learning API with a customer key and prints a public transcript + output hashes."""
import json, sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from learning_client import LearningClient, transcript_hash

PRESET_ID = "demo-arith-v1"
DATASET = [{"row_id": "add_%02d" % i, "prompt": "Q: What is %d + %d?\nA:" % (i, i + 3), "answer": " %d" % (2 * i + 3)} for i in range(16)]
PANELS = {"schema": "pumod_monitor_v1",
          "panels": {"capitals": [{"id": "cap_fr", "prompt": "Q: What is the capital of France?\nA:", "answer": " Paris"}, {"id": "cap_jp", "prompt": "Q: What is the capital of Japan?\nA:", "answer": " Tokyo"}],
                     "colors": [{"id": "col_sky", "prompt": "Q: What color is a clear daytime sky?\nA:", "answer": " Blue"}]}}
EVAL = [{"id": "ev_%02d" % i, "prompt": "Q: What is %d + %d?\nA:" % (20 + i, 20 + i + 3), "expected": "%d" % (2 * (20 + i) + 3)} for i in range(8)]


def jsonl(rows): return ("\n".join(json.dumps(r) for r in rows) + "\n").encode()


def run_demo(client, name="demo learner", tag=None, log=print):
    tag = tag or uuid.uuid4().hex[:8]; T = {"preset": PRESET_ID, "steps": []}
    L = client.create_learner(name); lid = L["learner_id"]; T["steps"].append({"create_learner": L})
    D = client.upload_dataset(lid, jsonl(DATASET)); PN = client.upload_panels(lid, PANELS); E = client.upload_eval_dataset(lid, jsonl(EVAL))
    T["steps"].append({"dataset": D, "panels": PN, "eval_dataset": E})
    J = client.create_session(lid, D["dataset_id"], PN["panel_set_id"], "demo-%s-train" % tag); J = client.wait(lid, J["job_id"]); T["steps"].append({"session": J})
    if J["status"] != "completed":
        log("training did not complete: %s" % json.dumps(J.get("error"))); return T
    ck = J["result"]["checkpoint_id"]; C = client.get_checkpoint(lid, ck); T["steps"].append({"checkpoint": C})
    I = client.infer(lid, ck, [{"id": "p1", "prompt": DATASET[0]["prompt"]}, {"id": "p2", "prompt": EVAL[0]["prompt"]}], "demo-%s-infer" % tag); I = client.wait(lid, I["job_id"])
    T["steps"].append({"inference": I, "answers": client.all_answers(lid, I["job_id"]) if I["status"] == "completed" else None})
    V = client.evaluate(lid, ck, E["dataset_id"], "demo-%s-eval" % tag); V = client.wait(lid, V["job_id"])
    T["steps"].append({"evaluation": V, "answers": client.all_answers(lid, V["job_id"]) if V["status"] == "completed" else None})
    T["transcript_digest"] = "sha256:" + transcript_hash(T["steps"]); log(json.dumps(T, indent=1)[:4000]); return T


if __name__ == "__main__":
    key = os.environ.get("LEARNER_API_KEY"); base = (os.environ.get("LEARNER_API_BASE") or "").strip()
    if not key: print("set LEARNER_API_KEY (the customer key your operator issued)"); sys.exit(2)
    if not base: print("set LEARNER_API_BASE (the base URL your operator gave you); there is no default"); sys.exit(2)
    run_demo(LearningClient(key, base))
