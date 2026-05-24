"""Scanner protocol."""
from __future__ import annotations

from typing import Protocol

from vibecheck.findings import Finding


class Scanner(Protocol):
    """Each scanner produces a list of findings for a given input."""

    def scan(self, *args, **kwargs) -> list[Finding]: ...
