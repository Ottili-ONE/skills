#!/usr/bin/env python3
"""Validate a computer-use driver implementation against the 2026-08-01 contract.

Checks, in order:
  1. The override map covers exactly the 16 members of computer_toolset_20260801
     (un-overridden members are sent as enabled: false by the SDK).
  2. Coordinate scaling happens into a NEW array (input arrays are shared with
     message history; mutating them in place corrupts the conversation).
  3. confirm() is wired for type/key/hold_key and absent for mouse/scroll/screenshot.
  4. Exception messages use fixed phrases only -- no screen content, host names or
     session tokens (error-phrasing rule).
  5. The desktop is isolated: no credentials, no host mounts in the driver config.

Fully offline and deterministic. Machine-readable counts to stdout;
FAIL:/PASS:/WARN:/INFO: detail to stderr. Exit 0 on success, 1 on FAIL, 2 on usage.
"""
