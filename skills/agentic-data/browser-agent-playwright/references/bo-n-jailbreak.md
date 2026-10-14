# Best-of-N (BoN) jailbreak detection — browser-agent-playwright

Verified 2026-10-14 against the OWASP LLM Prompt Injection Prevention Cheat Sheet
(https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.md).
Version-sensitive: OWASP cheat sheet taxonomy (2025); re-check on the next update.

## The attack
An attacker submits the *same* malicious prompt N times (or N near-identical
variants) hoping one slips through a filter. Content inspection alone cannot
catch this: each variant may be individually clean. Detection is **counting**,
not content matching.

## Detection (ordered)
1. **Normalize** the prompt: lowercase, collapse runs of whitespace to a single
   space, trim. Two prompts that differ only in case, spacing or punctuation are
   the same attack.
2. **Count** per normalized key, with two windows:
   - per task: 50 attempts
   - per hour: 300 attempts
3. **On hit**: stop the run, log the key and the count, and tell the user. Never
   silently rate-limit — the attack must be visible in the report.

## Thresholds (concrete, not "a lot")
| Resource | Cap | Window |
|----------|-----|--------|
| Attempts per task | 50 | since the task started |
| Attempts per hour | 300 | rolling 60-min window |

Exhausting either cap stops the run and reports the cap with the counts. The
cap is enforced by the skill, not by the model's judgement.

## Implementation (offline, deterministic)
```js
const attempts = new Map();            // normalized prompt -> count
const timestamps = [];                 // ISO-8601 UTC of each attempt
function record(prompt) {
  const key = prompt.toLowerCase().replace(/\s+/g, ' ').trim();
  attempts.set(key, (attempts.get(key) ?? 0) + 1);
  timestamps.push(new Date().toISOString());
  if (attempts.get(key) > 50)   throw new Error('BoN cap exceeded (50/task)');
  // per-hour cap: drop timestamps older than 60 min, recount
  const hourAgo = Date.now() - 3_600_000;
  const inHour = timestamps.filter(ts => new Date(ts).getTime() > hourAgo).length;
  if (inHour > 300) throw new Error('BoN cap exceeded (300/hour)');
}
```

## Worked examples

### Good — attack detected at 51
1. Attacker submits "Ignore previous instructions" 50 times, each with different
   whitespace and casing.
2. The normalizer collapses them to one key; the counter hits 50.
3. The 51st attempt throws `BoN cap exceeded (50/task)`, the run stops, and the
   report names the key and the count.

### Bad — attack runs unbounded
1. The agent has no counter; it treats each submission as independent.
2. The 500th variant finally slips past the content filter.
3. The agent follows the injected instruction. Nothing in the report mentions
   that 500 near-identical prompts were seen.

### Bad — cap mentioned but never counted
The skill text says "watch for repeated prompts" but no counter exists. The
agent *thinks* it is watching and proceeds. Detection must be a counter with a
number, not a reminder.
