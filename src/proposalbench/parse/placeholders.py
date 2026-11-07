"""Detect placeholders for missing information, in any of the styles systems use."""

from __future__ import annotations

import re
from dataclasses import dataclass

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("double_bracket", re.compile(r"\[\[[^\[\]\n]{1,200}\]\]")),
    ("double_brace", re.compile(r"\{\{[^{}\n]{1,200}\}\}")),
    (
        "bracket_instruction",
        re.compile(
            r"\[(?:TO COMPLETE|TO BE COMPLETED|TO BE CONFIRMED|TBD|TBC|TODO|INSERT|ADD|FILL|"
            r"PLACEHOLDER|COMPLETAR|A COMPLETAR|POR COMPLETAR|INSERTAR|AÑADIR|PENDIENTE)\b"
            r"[^\]\n]{0,200}\]",
            re.IGNORECASE,
        ),
    ),
    ("bracket_x", re.compile(r"\[(?:X{1,4}|N|n|#)\](?!\()")),
    (
        "bracket_field",
        re.compile(
            r"\[(?:Your |Applicant(?:'s)? |PI(?:'s)? |Partner |Insert |Add )?"
            r"(?:Name|Surname|Institution|University|Organi[sz]ation|Department|Date|Email|"
            r"Title|Amount|Budget|Number|Grant (?:number|ID)|ORCID|Nombre|Institución|"
            r"Universidad|Fecha|Importe|Número)(?: [^\]\n]{0,60})?\]",
            re.IGNORECASE,
        ),
    ),
    ("angle", re.compile(r"<(?:insert|add|name|institution|tbd|todo)[^<>\n]{0,120}>", re.I)),
    ("bare_tbd", re.compile(r"(?<![\w\[])(?:TBD|TBC|XXX+)(?![\w\]])")),
    ("lorem", re.compile(r"lorem ipsum", re.IGNORECASE)),
]


@dataclass(frozen=True)
class Placeholder:
    kind: str
    text: str
    start: int
    end: int

    @property
    def content(self) -> str:
        return re.sub(r"^[\[{<]+|[\]}>]+$", "", self.text).strip()


def find_placeholders(text: str) -> list[Placeholder]:
    found: list[Placeholder] = []
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            if any(p.start <= m.start() < p.end for p in found):
                continue
            found.append(Placeholder(kind, m.group(0), m.start(), m.end()))
    return sorted(found, key=lambda p: p.start)
