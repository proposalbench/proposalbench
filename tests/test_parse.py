from proposalbench.parse.citations import (
    author_year_key,
    citing_sentences,
    expand_numeric,
    find_citations,
    split_sentences,
)
from proposalbench.parse.placeholders import find_placeholders
from proposalbench.parse.sections import count_words, parse_proposal

DOC = """# SOILNET: Living soils for resilient farms

## 1. Excellence

### 1.1 Objectives

We will map soil microbiomes across 40 farms [1, 3-5]. Prior work found strong effects
(Smith et al., 2020; García & López, 2019a).

| WP | Months |
|----|--------|
| WP1 | 1-12 |

### 1.2 Methodology

Kobak et al. (2025) describe excess vocabulary. See [[TO COMPLETE: partner list]].

**2. Impact**

Text about impact with {{Applicant_Name}} and [X] students.

## References

[1] Smith, J. (2020). Soils. Nature, 1, 2.
[2] Other.

### Annex inside references
More reference-ish text.

# Appendix A

Appendix text.
"""


def test_sections_and_references_block():
    p = parse_proposal(DOC)
    assert p.title == "SOILNET: Living soils for resilient farms"
    titles = [s.title for s in p.sections]
    assert "1.1 Objectives" in titles
    assert "2. Impact" in titles  # bold-line heading
    assert p.references_section is not None
    assert p.references_block.startswith("[1] Smith")
    assert "More reference-ish text." in p.references_block
    assert "Appendix text." not in p.references_block
    body = [s.title for s in p.body_sections()]
    assert "Annex inside references" not in body
    assert "Appendix A" in body
    obj = next(s for s in p.sections if s.title == "1.1 Objectives")
    assert obj.number == "1.1"


def test_body_text_excludes_tables_when_asked():
    p = parse_proposal(DOC)
    assert "WP1" in p.body_text()
    assert "WP1" not in p.body_text(include_tables=False)


def test_subtree_text_includes_children():
    p = parse_proposal(DOC)
    excellence = next(s for s in p.sections if s.title == "1. Excellence")
    assert "Kobak" in p.subtree_text(excellence)


def test_count_words_ignores_markup():
    assert count_words("**Bold** text, with [a link](http://x.org) and `code`.") == 7
    assert count_words("state-of-the-art, it's 40% of 1,200") == 5
    assert count_words("| a | b |\n|---|---|\n| c | d |") == 4


def test_numeric_citations():
    cites = find_citations("A [1, 3-5]. B [12]. Not [[placeholder]] nor [link](http://x).")
    assert [c.labels for c in cites] == [("1", "3", "4", "5"), ("12",)]
    assert expand_numeric("2–4; 7") == ["2", "3", "4", "7"]


def test_author_year_citations():
    text = (
        "Effects were strong (Smith et al., 2020; García & López, 2019a). "
        "Kobak et al. (2025) agree, as do (de la Fuente, 2018, p. 4) and (WHO, 2023)."
    )
    keys = [k for c in find_citations(text) for k in c.labels]
    assert "smith|2020" in keys
    assert "garcía|2019a" in keys
    assert "kobak|2025" in keys
    assert "fuente|2018" in keys
    assert "who|2023" in keys
    assert author_year_key("van der Berg and Lee", "2001") == "berg|2001"


def test_sentences_and_citing_sentences():
    text = (
        "First claim [1]. Second, e.g. a case, holds (Smith et al., 2020). Third has none."
        "\n\n- Item one [2]"
    )
    sents = [s for _, _, s in split_sentences(text)]
    assert sents[0] == "First claim [1]."
    assert sents[1].startswith("Second, e.g. a case")
    cs = citing_sentences(text)
    assert len(cs) == 3
    assert cs[2].sentence == "- Item one [2]"


def test_placeholders_all_styles():
    text = (
        "We have [[TO COMPLETE: n students]], {{PI_Name}}, [X] papers, [Institution], "
        "[TBD], <insert date>, XXX and [Insertar fecha] but not [1] or [3-5]."
    )
    kinds = [p.kind for p in find_placeholders(text)]
    assert kinds == [
        "double_bracket",
        "double_brace",
        "bracket_x",
        "bracket_field",
        "bracket_instruction",
        "angle",
        "bare_tbd",
        "bracket_instruction",
    ]
    assert find_placeholders("Cited [1] and [12, 14].") == []


def test_wrapping_fence_bold_parent_and_nested_references():
    from proposalbench.checks.admissibility import unwrap_fence

    body = "# Part B\n\n## 1. Excellence\n\nText here."
    assert unwrap_fence(f"```markdown\n{body}\n```\n") == body
    assert unwrap_fence("Intro.\n\n```python\nx = 1\n```\n") == "Intro.\n\n```python\nx = 1\n```\n"
    md = (
        "**Project Summary**\n\nSummary text.\n\n**Project Description**\n\n"
        "### 1. Introduction\n\nIntro words here.\n\n### 2. Methods\n\nMethod words.\n\n"
        "### References\n\n1. Smith J. 2020. A title. Journal.\n"
    )
    p = parse_proposal(md)
    desc = next(s for s in p.sections if s.title == "Project Description")
    text = p.subtree_text(desc)
    assert "Intro words" in text and "Method words" in text and "Smith J." not in text
