from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Kind = Literal["gate", "deduction", "defect", "diagnostic"]


@dataclass(frozen=True)
class Finding:
    """One observation produced by a check.

    ``gate`` findings make a sample inadmissible, ``deduction`` findings lower a component score,
    ``defect`` findings feed the integrity deductions, and ``diagnostic`` findings are reported
    only.
    """

    check: str
    kind: Kind
    message: str
    location: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
