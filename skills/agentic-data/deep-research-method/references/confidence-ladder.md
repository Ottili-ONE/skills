# Confidence ladder — deep-research-method

Verified 2026-10-14. Confidence is a function of the *kept* sources behind a
claim, not of how many URLs cite it. Two URLs that share an upstream are one
source, so a claim citing three URLs that all trace to one upstream cannot
claim high confidence.

## The ladder
| Level | Condition | Meaning |
|-------|-----------|---------|
| high | >=2 distinct upstreams among kept sources | primary + corroboration |
| medium | exactly 1 distinct upstream | primary only |
| low | no kept source (secondary only) | flag, do not assert |
| none | no sources at all | the claim is unsourced |

## Why upstreams, not URLs
Corroboration means independent evidence. Two pages that copy the same primary
count as one. The fake-middle trap: several URLs that agree exactly on a value
but trace to the same upstream — they look like corroboration and are not.

## How to use it
1. Score every source 0-10; keep only >=6.
2. Group the kept sources by `upstream` (falling back to `url` when absent).
3. Count the distinct upstreams.
4. Read the ladder. State the level in the answer, not just the number.

## Worked examples

### Good — three upstreams, high confidence
`arxiv.org`, `openai.com`, `europa.eu` all kept for a claim. Three distinct
upstreams -> high. The answer states "high confidence (3 independent sources)".

### Bad — three URLs, one upstream, claimed high
`arxiv.org/abs/x`, `mirror.example.com/arxiv-x`, `blog.example.com/arxiv-x` all
cite the same arXiv paper. One upstream -> medium. Claiming high here is the
fake-middle failure: the answer reads as corroborated and is not.
