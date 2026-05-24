"""Fixer protocol."""
from __future__ import annotations

from typing import Protocol

from vibecheck.findings import Finding


class Fixer(Protocol):
    def apply(self, finding: Finding) -> None: ...
