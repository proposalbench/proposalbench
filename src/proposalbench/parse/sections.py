"""Split a Markdown proposal into a heading tree, body and reference block, and count words."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from markdown_it import MarkdownIt

REFERENCE_HEADINGS = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?\s+)?(references|bibliography|reference list|works cited|"
    r"literature cited|cited literature|referencias(?: bibliogr[aá]ficas)?|bibliograf[ií]a|"
    r"literatura citada|literaturverzeichnis|literatur)\s*:?\s*$",
    re.IGNORECASE,
)
SECTION_NUMBER = re.compile(r"^\s*((?:[A-Z]\.)?\d+(?:\.\d+)*)\.?\s+")
WORD = re.compile(r"\d+(?:[.,]\d+)*%?|[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")

_md = MarkdownIt("commonmark").enable("table")


@dataclass
class Section:
    level: int
    title: str
    number: str | None
    line_start: int  # 0-based line of the heading
    line_end: int  # exclusive; end of this section's own text (before the next heading)
    text: str  # own text, excluding the heading line and any subsections
    children: list[Section] = field(default_factory=list)
    is_references: bool = False
    block_end: int | None = None  # for a reference heading: end of the whole reference block

    @property
    def word_count(self) -> int:
        return count_words(self.text)


@dataclass
class ParsedProposal:
    raw: str
    title: str | None  # leading H1 when it precedes all body text
    sections: list[Section]  # flat, document order
    references_block: str | None
    references_section: Section | None
    preamble: str  # text before the first heading

    def body_sections(self) -> list[Section]:
        return [s for s in self.sections if not s.is_references and not _after_refs(s, self)]

    def body_text(self, include_tables: bool = True) -> str:
        parts = [self.preamble] + [f"{s.title}\n{s.text}" for s in self.body_sections()]
        text = "\n\n".join(p for p in parts if p.strip())
        return text if include_tables else strip_tables(text)

    def subtree_text(self, section: Section) -> str:
        """The section's own text plus all descendant sections, headings included."""
        idx = self.sections.index(section)
        parts = [section.text]
        skip_below = None  # a reference list nested in the subtree is not part of it
        for s in self.sections[idx + 1 :]:
            if s.level <= section.level:
                break
            if skip_below is not None and s.level > skip_below:
                continue
            skip_below = s.level if s.is_references else None
            if s.is_references:
                continue
            parts.append(f"{s.title}\n{s.text}")
        return "\n\n".join(parts)


def _after_refs(s: Section, p: ParsedProposal) -> bool:
    """Sections nested under the reference heading belong to the reference block."""
    r = p.references_section
    return r is not None and r.line_start < s.line_start < (r.block_end or 0)


def normalize_heading(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[*_`#]+", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def count_words(text: str) -> int:
    return len(WORD.findall(strip_markdown(text)))


def strip_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # images
    text = re.sub(r"\[([^\]]+)\]\((?:[^)]+)\)", r"\1", text)  # links keep their text
    text = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", text, flags=re.MULTILINE)  # list markers
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    text = TABLE_RULE.sub(" ", text)
    return re.sub(r"[*_`#|]+", " ", text)


def strip_tables(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not TABLE_LINE.match(line))


def parse_proposal(markdown: str) -> ParsedProposal:
    lines = markdown.splitlines()
    headings: list[tuple[int, int, str]] = []  # (line, level, title)
    for tok_i, tok in enumerate(tokens := _md.parse(markdown)):
        if tok.type == "heading_open" and tok.map:
            inline = tokens[tok_i + 1]
            headings.append((tok.map[0], int(tok.tag[1]), inline.content.strip()))
    markdown_levels = {line: level for line, level, _ in headings}
    for line, level, title in _bold_line_headings(lines, set(markdown_levels)):
        # A bold line directly followed by a Markdown heading is that heading's parent
        # ("**Project Description**" then "### 1. Introduction"), not a level-4 sibling.
        nxt = next((j for j in range(line + 1, len(lines)) if lines[j].strip()), None)
        if nxt in markdown_levels:
            level = max(1, markdown_levels[nxt] - 1)
        headings.append((line, level, title))
    headings.sort()

    sections: list[Section] = []
    for i, (line, level, title) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else len(lines)
        heading_lines = 2 if _is_setext(lines, line) else 1
        text = "\n".join(lines[line + heading_lines : end]).strip("\n")
        m = SECTION_NUMBER.match(title)
        sections.append(
            Section(
                level=level,
                title=title,
                number=m.group(1) if m else None,
                line_start=line,
                line_end=end,
                text=text,
                is_references=bool(REFERENCE_HEADINGS.match(normalize_heading(title))),
            )
        )
    _link_children(sections)

    preamble_end = headings[0][0] if headings else len(lines)
    preamble = "\n".join(lines[:preamble_end]).strip()

    title = None
    if sections and sections[0].level == 1 and not preamble and _is_title_like(sections):
        title = sections[0].title

    refs = _last_reference_section(sections)
    block = None
    if refs is not None:
        end = len(lines)
        for s in sections[sections.index(refs) + 1 :]:
            if s.level <= refs.level:
                end = s.line_start
                break
        refs.block_end = end
        heading_lines = 2 if _is_setext(lines, refs.line_start) else 1
        block = "\n".join(lines[refs.line_start + heading_lines : end]).strip()
    return ParsedProposal(markdown, title, sections, block, refs, preamble)


def _is_title_like(sections: list[Section]) -> bool:
    """A leading H1 is the document title when it has little own text or other H1s follow."""
    first = sections[0]
    return first.word_count < 80 or any(s.level == 1 for s in sections[1:])


def _last_reference_section(sections: list[Section]) -> Section | None:
    refs = [s for s in sections if s.is_references]
    return refs[-1] if refs else None


def _link_children(sections: list[Section]) -> None:
    stack: list[Section] = []
    for s in sections:
        while stack and stack[-1].level >= s.level:
            stack.pop()
        if stack:
            stack[-1].children.append(s)
        stack.append(s)


def _is_setext(lines: list[str], line: int) -> bool:
    return line + 1 < len(lines) and re.match(r"^\s*(=+|-+)\s*$", lines[line + 1]) is not None


# A whole line in bold, written **...** or __...__ (both render the same).
_BOLD_HEADING = re.compile(
    r"^\s*(\*\*|__)((?:\d+(?:\.\d+)*\.?\s+)?(?:(?!\1)[^*_]|_(?!_)){2,120})\1\s*:?\s*$"
)


def _bold_line_headings(lines: list[str], taken: set[int]) -> list[tuple[int, int, str]]:
    """Treat a standalone bold line followed by a blank line as a level-4 heading.

    Some systems emit section titles as bold paragraphs instead of Markdown headings.
    """
    out = []
    for i, line in enumerate(lines):
        if i in taken:
            continue
        m = _BOLD_HEADING.match(line)
        before_blank = i == 0 or not lines[i - 1].strip()
        after_blank = i + 1 >= len(lines) or not lines[i + 1].strip()
        if m and before_blank and after_blank:
            out.append((i, 4, m.group(2).strip()))
    return out
