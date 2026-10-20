"""Shared helpers for dsgvo-ai-act-labeling tests."""
import hashlib
import json
from pathlib import Path


def write_label(fields: dict, tmp_path: Path) -> Path:
    """Write the label into the test directory, never into a shared /tmp."""
    p = Path(tmp_path) / "label.json"
    p.write_text(json.dumps(fields))
    return p
