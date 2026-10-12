"""A minimal, conformant computer-use driver subclass (fixture for tests)."""
from __future__ import annotations


class ToolError(Exception):
    """Shown to the model; must never carry screen content, host names or tokens."""


class ToolsetUsageError(Exception):
    """Stops the run; never shown to the model."""


class BetaAbstractComputerToolset20260801:
    def __init__(self, confirm=None) -> None:
        self._confirm = confirm or (lambda *_a, **_k: True)

    def confirm(self, tool, input_data):
        return self._confirm(tool, input_data)

    def _scale(self, input_data):
        # Scale into a NEW array — input arrays are shared with message history,
        # so mutating them in place corrupts the turn. input.copy() is the signal.
        return input.copy()

    def screenshot(self, input_data):
        return {"type": "screenshot", "image": "..."}

    def zoom(self, input_data):
        return {"type": "screenshot", "image": "..."}

    def cursor_position(self, input_data):
        x, y = input_data[0]
        return {"x": x, "y": y}  # screenshot pixels

    def mouse_move(self, input_data):
        self._scale(input_data)

    def left_mouse_down(self, input_data):
        self._scale(input_data)

    def left_mouse_up(self, input_data):
        self._scale(input_data)

    def left_click(self, input_data):
        self._scale(input_data)

    def left_click_drag(self, input_data):
        self._scale(input_data)

    def right_click(self, input_data):
        self._scale(input_data)

    def middle_click(self, input_data):
        self._scale(input_data)

    def double_click(self, input_data):
        self._scale(input_data)

    def triple_click(self, input_data):
        self._scale(input_data)

    def scroll(self, input_data):
        self._scale(input_data)

    def wait(self, input_data):
        return "waited"

    def type(self, input_data):
        if not self.confirm("type", input_data):
            raise ToolsetUsageError("declined")
        return "typed"

    def key(self, input_data):
        if not self.confirm("key", input_data):
            raise ToolsetUsageError("declined")
        return "keyed"

    def hold_key(self, input_data):
        if not self.confirm("hold_key", input_data):
            raise ToolsetUsageError("declined")
        return "held"
