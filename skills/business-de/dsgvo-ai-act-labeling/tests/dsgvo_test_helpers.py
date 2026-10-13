"""Shared helpers for dsgvo-ai-act-labeling tests."""
import hashlib
import json
import tempfile
from pathlib import Path


def write_label(fields: dict) -> Path:
    p = Path(tempfile.mktemp(suffix=".json"))
    p.write_text(json.dumps(fields))
    return p
