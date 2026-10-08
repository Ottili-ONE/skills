# Sandbox contract — verifiable-environments

The contract the verifier asserts before any agent runs. Pin it in a JSON file
the harness reads at startup; the verifier refuses to run if the contract is
violated.

| Element   | Required value | Why |
|-----------|----------------|-----|
| `network` | `"deny"` | An agent with network can fetch the answer or exfiltrate state. |
| `filesystem` | `"scoped"` | The agent must only see its own temp dir; cross-run reads are a leak. |
| `exec` | `"allowlisted"` or `"none"` | Unrestricted exec lets the agent install tools or edit the checks. |
| `time_seconds` | int in `[1, 3600]` | Unbounded time lets an agent stall for credit. |
| `secrets` | `"none"` or `"redacted"` | Exposed secrets let an agent exfiltrate keys. |

A contract that sets `network: "allow"` or `filesystem: "open"` is a FAIL for the
whole harness, regardless of how good the checks are.

Good (pinned contract):
```json
{"network": "deny", "filesystem": "scoped", "exec": "allowlisted",
 "time_seconds": 300, "secrets": "none"}
```

Bad (leaky):
```json
{"network": "allow", "filesystem": "open", "exec": "allow",
 "time_seconds": 0, "secrets": "full"}
```
