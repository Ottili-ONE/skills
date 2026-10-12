# Coordinate scaling — the model/display pixel contract

Verified 2026-10-12 against the Anthropic SDK computer-toolset spec (HTTP 200).
Every coordinate the model sends is in **full-screenshot pixels**. The driver
translates them to **display pixels** before acting. Getting this wrong is the
most common silent failure in computer-use drivers.

## The two spaces

| Space | Origin | Used for | Who sets it |
|-------|--------|----------|-------------|
| Screenshot pixels | top-left of the captured image | model input, `cursor_position` report | the capture resolution |
| Display pixels | top-left of the physical/virtual display | the actual pointer position | the driver |

The capture size is **fixed for the session**. Resizing the screenshot mid-session
changes the coordinate space and invalidates every point the model has learned.

## The scaling rule

```
display_x = model_x * (display_width  / screenshot_width)
display_y = model_y * (display_height / screenshot_height)
```

Scale into a **NEW array**. The arrays in `input` are shared with the message
history — mutating them in place corrupts the turn. The detection signal in
`scripts/validate_driver.py` is `input.copy()` or `list(input)` or `[*input]`.

## Report `cursor_position` back in screenshot pixels

The model's next action depends on the reported cursor position. Report it in the
same space the model uses — screenshot pixels — or the model will drift by the
scale factor and click progressively wrong places.

## Out of bounds

If a scaled coordinate falls outside the display, **throw `ToolError`**. Never clamp.
Clamping silently moves the pointer to a different element; the model sees no error,
retries, and compounds the mistake. The SDK does not check `input`, so the driver
must validate.

## Image size limit

If the screenshot exceeds the model's pixel limit, reject with `ToolError`. The SDK
never resizes — reconfigure the capture resolution, do not resize in code.

## Ordered procedure
1. Confirm the capture size is fixed for the session.
2. Read the model's coordinate from `input[0]`.
3. Compute the scale factor from the fixed capture size and the display size.
4. Scale into a fresh array.
5. Assert the scaled point is inside the display; if not, throw `ToolError`.
6. Act on the scaled point.
7. Report `cursor_position` back in screenshot pixels.

## Near-miss triggers
- Mutating `input` in place -> the shared message history is corrupted.
- Reporting `cursor_position` in display pixels -> the model drifts.
- Resizing the screenshot mid-session -> the coordinate space changes.
- Clamping an out-of-bounds point -> the model cannot detect the error.
- Resizing the image in code to fit a pixel limit -> the SDK never resizes; reject instead.
