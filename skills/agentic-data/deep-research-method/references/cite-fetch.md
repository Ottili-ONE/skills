# Citation and fetch — deep-research-method

Verified 2026-10-12. Companion to `scripts/score_sources.py`, which gained the
`cite` and `fetch` subcommands this pass because `SKILL.md` advertised them and
the script only shipped `score`/`audit`/`contradictions`.

## Why these two exist
`score` decides what is usable; `audit` checks that claims cite kept sources.
Neither produces the artefact the researcher actually needs: the citation list
and the URL list to re-fetch. `cite` and `fetch` close that gap, and both are
fully offline — they never touch the network.

## cite — emit a citation block
```
python3 scripts/score_sources.py cite <sources.jsonl> [--min 6]
```
Prints one line per kept source to stderr:
```
<url> retrieved=<ISO date>[ v=<version>]
```
Exit 0 on success, 1 if no source is kept, 2 if the sources file is missing.

Use it to build the "Sources" section of a research answer. Every line carries
the retrieval date, which is the invariant: a source without a retrieval date
is memory, not evidence.

## fetch — list the URLs to re-verify
```
python3 scripts/score_sources.py fetch <sources.jsonl> [--min 6]
```
Prints kept-source URLs to **stdout**, one per line, in file order, so it can
be piped straight into `curl -K -`:
```
python3 scripts/score_sources.py fetch sources.jsonl | xargs -I{} curl -sL {} -o {}.html
```
Exit 0 on success, 1 if nothing is kept, 2 if the file is missing.

Use it before a re-verification pass. Facts older than a year must be re-fetched
for a current question — `fetch` gives you exactly the list to re-fetch, and
nothing else.

## Contract (matches the other scripts in this skill)
- Machine-readable output (the URL list) goes to **stdout**.
- Detail lines are prefixed `PASS:`/`FAIL:`/`INFO:` and go to **stderr**.
- Exit codes: 0 pass, 1 logical fail, 2 usage error (missing file).
- No network access; deterministic across runs.

## Worked example
Sources file with three entries, one below the threshold:
```
{"url":"https://arxiv.org/abs/2605.20744","authority":4,"recency":3,"corroboration":3,"retrieved":"2026-10-12"}
{"url":"https://www.example.com/blog","authority":1,"recency":1,"corroboration":0,"retrieved":"2026-10-12"}
{"url":"https://arxiv.org/abs/2609.00038","authority":4,"recency":3,"corroboration":2,"retrieved":"2026-10-12"}
```
`cite` -> two lines, the blog skipped. `fetch` -> the two arXiv URLs on stdout.

Detection signal: `fetch` prints exactly the kept URLs and `cite` prints the
retrieval date next to each.
