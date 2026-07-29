"""Result — the universal success indicator for every voetlab feature.

Contract: every feature function returns a `Result`. The pipeline runner branches on
`.ok` (truthiness) and flags features that did not finish their logic successfully.

Usage::

    def detect_passes(...) -> Result:
        if not events:
            return Result.Fail("no events to classify", feature="passes")
        return Result.Ok({"passes": passes}, feature="passes", count=len(passes))

    res = detect_passes(...)
    if res:                       # success
        use(res.value)
    else:                         # failure — flag it
        log(res.error)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Result:
    """Outcome of one feature run.

    Attributes:
        ok:    True if the feature finished its logic successfully.
        value: The feature's payload on success (None on failure).
        error: Human-readable reason on failure (None on success).
        meta:  Free-form diagnostic metadata (e.g. feature name, coverage %, counts).
    """

    ok: bool
    value: Any = None
    error: str | None = None
    meta: dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        """`if result:` reads success — so the runner can branch naturally."""
        return self.ok

    @classmethod
    def Ok(cls, value: Any = None, **meta: Any) -> "Result":
        """Build a successful result carrying `value` and optional diagnostic `meta`."""
        return cls(ok=True, value=value, meta=dict(meta))

    @classmethod
    def Fail(cls, error: str, **meta: Any) -> "Result":
        """Build a failed result with an `error` reason and optional diagnostic `meta`."""
        return cls(ok=False, error=error, meta=dict(meta))
