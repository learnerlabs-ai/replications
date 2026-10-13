# Recipe

`teacher_prompt.txt` is the prompt the teacher LLM received after every question, verbatim except for one redacted term (1 occurrence). Its section headings are internal revision labels. The teacher's input after each question also holds the learner's trajectory on that question, the benchmark's released feedback, the learner's earlier trajectories as evidence, and the procedures it wrote before.

Training: one pass, batch size 1, one optimizer step per example, no replay, no optimizer resets between questions. Learner context 32,000 tokens, greedy decoding. Thinking only when stuck: before an action, if the last query result was an error or empty, or 8 or more of the 15 queries are used, the learner first writes at most 512 tokens of reasoning (not shown to the benchmark), then the action, capped at 384 tokens. Otherwise it writes the action directly, capped at 4,096 tokens. The earlier recipe (folders earlier_recipe_*) never thinks and caps actions at 4,096 tokens. Everything else is the same.

From procedures to examples: each example is a state the learner actually reached (the conversation so far, with the recorded query results) and the next action the procedure prescribes as the target. Only examples grounded in recorded results are kept.
