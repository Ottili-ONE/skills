# SPEC: file-writing task

The agent must produce, in its sandbox output directory:

1. `output.json` — a JSON object with field `status` equal to the string `ok`.
   The file must exist and its status field must equal ok.
2. `summary.md` — a markdown file of at least 20 words describing the output.
   The file must exist.

Observable outcomes only. Nothing else is checked.
