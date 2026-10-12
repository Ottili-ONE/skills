# Worked examples — computer-use-drivers

Verified 2026-10-12 against the anthropic-sdk-typescript sources.
Good and bad driver code, with the detection signal for each.

## Good — 16-member driver, confirm-gated, new-array scaling

```python
class Driver(BetaAbstractComputerToolset20260801):
    def type(self, input, confirm):
        confirm("type")            # required for a gated member
        return input.copy()        # NEW array; input is shared with history
    def key(self, input, confirm):
        confirm("key")
        return list(input)
    def hold_key(self, input, confirm):
        confirm("hold_key")
        return [*input]
    def screenshot(self): return BetaScreenshotResult(image=...)  # ungated
```

Detection signal: `scripts/validate_driver.py driver.py` prints `2 0 0` and exits 0.

## Bad — arrow-function field

```python
class Driver(BetaAbstractComputerToolset20260801):
    screenshot = lambda self: {}     # compiles but is NOT detected as served
```

Detection signal: the API sends `screenshot` as `enabled: false` and the call
silently no-ops. `validate_driver.py` reports the member as not defined.

## Bad — in-place mutation

```python
def type(self, input, confirm):
    confirm("type")
    input[0] = 0          # mutates the shared message-history array
    return input
```

Detection signal: `validate_driver.py` warns "coordinate scaling may mutate input
in place"; the conversation is corrupted.

## Bad — raw exception message

```python
except Exception as e:
    raise ToolError(str(e))   # e.message may carry a window title or token
```

Detection signal: screen content, a host name or a session token leaks into tool
error text shown to the model unredacted. Rewrite as a fixed phrase.

## Bad — clamping out-of-bounds coordinates

```python
x = max(0, min(width - 1, model_x))   # silently clicks the wrong place
```

Detection signal: throw `ToolError` instead. The SDK does not check `input`, so
the driver must validate.

## Good — isolated desktop

One container per session, no credentials, no host mounts, egress only to hosts the
task needs; the model loop, toolset and API key stay outside. Detection signal: no
`mount`, no credential file and no API key in the driver config.

## Good — error phrasing

```python
raise ToolError("out of bounds: coordinate outside the display")
```

Fixed phrase only. A `ToolError` is shown to the model and the run continues; any
other exception propagates as a `ToolsetUsageError` and stops the run.
