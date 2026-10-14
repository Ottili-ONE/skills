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

    def enumerate_tree(self):
        """Return the accessibility tree: a list of {role, name, value, description}.

        The tree is the gate, not a preference. An empty tree (every node
        role: "unknown" with no name) must stop the run, never fall back to
        pixels. The screenshot gives pixels; the tree gives what is at them.
        """
        return [
            {"role": "button", "name": "Save", "value": None, "description": ""},
            {"role": "textbox", "name": "Password", "value": "", "description": ""},
        ]

    def tree_is_usable(self):
        """True when the enumerated tree has at least one node with a real role
        and name. False on an empty or all-unknown tree."""
        nodes = self.enumerate_tree()
        return any(
            n.get("role") not in (None, "", "unknown") and n.get("name")
            for n in nodes
        )
