# Recipe

`teacher_prompt.txt` is the prompt the teacher LLM received after every study, verbatim except for one redacted term (1 occurrence), identical in all three runs. Its section headings are internal revision labels. After each study the teacher's input also holds the learner's steps in the study just finished, with the tool results, and the task brief. It holds nothing from earlier studies: no earlier trajectories, none of the teacher's earlier procedures, no scores.

`reasoning_prompt.txt` is sent to the learner with the state of each training example. `%s` is the action the teacher chose. The learner's reasoning becomes the example's `thought`.

Training: one pass, batch size 1, one optimizer step per example, no replay, no optimizer resets between studies. At most 50,000 supervised tokens per study. Learner context 32,000 tokens, each step's output limited to 4,096 tokens, greedy decoding.

From procedures to examples: each example is a state the learner actually reached (the conversation so far, with the recorded tool results) and the next action the procedure prescribes as the target. No tool result is invented. Two fixed examples are added at every study: read the database metadata first, and after a tool error read the metadata if not yet read.
