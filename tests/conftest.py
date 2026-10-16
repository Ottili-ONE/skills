"""Root-level pytest configuration for the skills repository (SKL-W0-01 TASK-0003).

The repository keeps a stale duplicate of the business-de skills at the top level
(``business-de/``) alongside the canonical ``skills/business-de/``. Both trees
contain ``tests/test_*.py`` files with identical basenames, which makes pytest's
default import-mode collection abort with "import file mismatch" on a fresh clone
(git cannot store empty directories, so the problem surfaces on clone rather than
in the working tree).

This conftest does NOT delete the duplicate (it does not own those paths). It makes
the collection deterministic by excluding the stale tree from recursion, so the
canonical ``skills/business-de/`` tests are the ones that run. The duplicate's
removal is a cross-job request recorded in docs/gaps/SKL-W0-01.md.
"""
from __future__ import annotations

import os

# The stale duplicate lives at the repository root, one level above this file.
_STALE_DUPLICATE = os.path.basename(
    os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "business-de"))
)


def pytest_configure(config):
    """Exclude the stale duplicate tree from collection at configure time."""
    config.addinivalue_line("norecursedirs", _STALE_DUPLICATE)
