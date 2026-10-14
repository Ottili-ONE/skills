# Worked examples — computer-use-drivers

Verified 2026-10-13 against the anthropic-sdk-python sources
(`lib/tools/_toolsets/_computer_registry.py`, `lib/tools/_toolsets/_computer.py`;
HTTP 200). The old `lib/_computer_use/` paths 404.
Good and bad driver code, with the detection signal for each.

## Good — 17-member driver, confirm-gated, new-array scaling

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

## Good — tree-first enumeration with scaling

Goal: click "Save" in a file dialog.

1. Enumerate the tree; find a `button` with `name: "Save"`.
2. Read its center in screenshot pixels: `(640, 360)` on a 1280x720 capture.
3. The display is 1920x1080, so the scale factor is 1.5. Scale into a fresh array:
   `[960, 540]`.
4. Assert `(960, 540)` is inside the display. It is — click.
5. Report `cursor_position` back as `(640, 360)` in screenshot pixels.

Detection signal: `scripts/validate_driver.py` reports `input.copy()` present,
`cursor_position` reported in screenshot pixels, no clamping.

## Bad — screenshot-only click

Goal: click the "Save" button.

1. The model guesses the button is at `(700, 400)` from the screenshot.
2. The driver scales and clicks. It lands on "Cancel".
3. The model sees no error and retries at `(700, 410)`, then `(700, 390)`.

Why it fails: without the tree there is no identity. The screenshot gives pixels;
the tree gives *what is at those pixels*. Detection: no tree enumeration before the
click; the click target is a guess.

## Good — confirm() with escaped input

Goal: type `rm -rf /tmp/build` into a terminal.

1. `confirm("type into the terminal")` — fixed phrase only.
2. The approver sees the tool name and the input with invisible characters escaped.
3. `type` runs. The confirmation string never carried the command text.

Detection signal: `validate_driver.py` finds `confirm` in the `type` body and no
f-string carrying screen content in the error path.

## Bad — screen content in a confirmation string

`confirm("type the code shown in this dialog: 7F3A9Q")`.

Why it fails: the confirmation string now carries screen content, which is untrusted
data. Use a fixed phrase only; let the exception path carry the content if it must.

## Good — out-of-bounds refusal

Goal: click `(99999, 99999)` on a 1920x1080 display.

1. The driver scales the coordinate, finds it outside the display bounds.
2. It raises `ToolError` with the fixed phrase "coordinate outside the display".
3. The model sees a clean error and re-enumerates the tree for the real target.

Detection signal: `validate_driver.py` finds no `clamp`/`max(0, min(` idiom; the
driver throws rather than silently moving the pointer to a wrong location.

## Bad — clamping

```python
def mouse_move(self, input_data):
    x = max(0, min(width - 1, input_data[0][0]))   # silently moves the pointer
    y = max(0, min(height - 1, input_data[0][1]))
```

Why it fails: the click lands somewhere valid but wrong, and the model cannot
detect the move — there is no error to retry from. Detection: `validate_driver.py`
fails with "clamping detected — never clamp".

## Good — 17-member registry audit

`fixtures/registry_20260801.json` lists all 17 members of
`computer_toolset_20260801`. The driver defines a method per member; members the
driver does not override are sent as `enabled: false`. No invented members.

Detection signal: `validate_driver.py --contract fixtures/registry_20260801.json`
reports `{"mode": "contract", "oks": 1, "fails": 0, "warns": 0, "valid": true}`.

## Bad — member-set drift

A driver defines `screenshot`, `mouse_move`, `left_click` and 13 others, but the
registry it ships lists only 16 names (it is missing `triple_click`). The SDK
rejects the missing member at runtime.

Detection signal: `validate_driver.py --contract` reports
`FAIL: member set drift: got [...]; expected [...]`. The published contract has
17 members — audit the registry, do not assume.
