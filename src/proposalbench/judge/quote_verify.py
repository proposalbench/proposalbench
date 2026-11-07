"""Check that a judge's quotes really occur in the proposal.

Quotes are compared after normalising Markdown, quotation marks, dashes and whitespace. A quote
may elide text with an ellipsis; each fragment must then occur, in order.
"""

from __future__ import annotations

import re
import unicodedata

from rapidfuzz import fuzz

_TRANSLATE = str.maketrans(
    {"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "−": "-", " ": " "}
)
MIN_FRAGMENT = 12
FUZZY_MIN_LEN = 40
FUZZY_THRESHOLD = 96


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_TRANSLATE)
    text = re.sub(r"[*_`#>|]+", " ", text)
    text = re.sub(r"\[(\d+(?:[-,;\s]+\d+)*)\]", r"[\1]", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def quote_found(quote: str, normalized_text: str) -> bool:
    fragments = [f.strip(" .\"'") for f in re.split(r"\.\.\.|…|\[\.\.\.\]", normalize(quote))]
    fragments = [f for f in fragments if f]
    if not fragments or all(len(f) < MIN_FRAGMENT for f in fragments):
        return False
    pos = 0
    for frag in fragments:
        if len(frag) < MIN_FRAGMENT:
            continue
        idx = normalized_text.find(frag, pos)
        if idx < 0:
            if len(frag) >= FUZZY_MIN_LEN:
                window = normalized_text[pos:]
                if fuzz.partial_ratio(frag, window) >= FUZZY_THRESHOLD:
                    continue
            return False
        pos = idx + len(frag)
    return True
