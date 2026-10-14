#!/usr/bin/env python3
"""Bucket a piece of content into the AI-Act transparency classes.

  synthetic  — fully machine-generated text, no human input
  assist     — human-authored, AI only polished
  augment    — AI produced a substantive part (draft, summary, code)
  disclose  — Art. 50(4) applies unless the exemption test passes

Ambiguous input exits non-zero; never silently guess.

Usage:
    python3 classify_content.py --meta content.json
"""
import argparse
import json
import sys
from pathlib import Path

CLASSES = ("synthetic", "assist", "augment", "disclose")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meta", required=True, help="content metadata JSON")
    args = ap.parse_args()

    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    human = meta.get("human_authored")
    ai_produced = meta.get("ai_produced_substantive_part")
    published_public = meta.get("published_to_inform_public")

    if human is None or ai_produced is None or published_public is None:
        print(json.dumps({"ok": False, "reason": "ambiguous",
                          "need": ["human_authored", "ai_produced_substantive_part",
                                   "published_to_inform_public"]}))
        return 1

    if not ai_produced:
        cls = "assist" if human else "synthetic"
    elif published_public:
        cls = "disclose"
    else:
        cls = "augment"

    print(json.dumps({"ok": True, "class": cls, "meta": meta}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
