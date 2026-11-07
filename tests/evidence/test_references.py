from __future__ import annotations

import pytest

from proposalbench.parse.references import normalize_doi, parse_references


@pytest.mark.parametrize(
    "marker,label", [("[1]", "1"), ("1.", "1"), ("1)", "1"), ("-", None), ("*", None), ("+", None)]
)
def test_lists_and_continuations(marker, label):
    refs = parse_references(
        f"{marker} Smith, J. (2021). A long title\n"
        "  continued here. Nature, 5, 1–9.\n\n"
        "[2] Jones, A. (2020). Another useful title. Science, 1, 2–4."
    )
    assert len(refs) == 2
    assert refs[0].label == label
    assert refs[0].title == "A long title continued here"
    assert refs[0].index == 0 and refs[1].index == 1
    assert "\n" in refs[0].raw


@pytest.mark.parametrize(
    "raw,title,authors,year,venue",
    [
        (
            "Smith, J., & Jones, A. (2021). A robust method for discovery. Nature, 12(3), 1–9.",
            "A robust method for discovery",
            ["Smith", "Jones"],
            2021,
            "Nature",
        ),
        (
            "Smith J, Jones AB. A robust method for discovery. Lancet. 2021;12:1-9.",
            "A robust method for discovery",
            ["Smith", "Jones"],
            2021,
            "Lancet",
        ),
        (
            "García, M. y López, A. (2020). Redes neuronales en medicina. Revista Médica, 12, 3–9.",
            "Redes neuronales en medicina",
            ["García", "López"],
            2020,
            "Revista Médica",
        ),
        (
            "Unknown (2012). Speech Graphs: A new approach | PLOS One. Retrieved from https://x.org",
            "Speech Graphs: A new approach",
            [],
            2012,
            "PLOS One",
        ),
        (
            "Smith, J. (2019) Methods for robust discovery. Science, 8, 1–4.",
            "Methods for robust discovery",
            ["Smith"],
            2019,
            "Science",
        ),
        (
            "Vaswani, A. et al. (2017). Attention is all you need. arXiv:1706.03762.",
            "Attention is all you need",
            ["Vaswani"],
            2017,
            None,
        ),
        (
            "Smith J. “A quoted title: with punctuation.” Nature. 2020;10:1-9.",
            "A quoted title: with punctuation",
            ["Smith"],
            2020,
            "Nature",
        ),
    ],
)
def test_styles(raw, title, authors, year, venue):
    (ref,) = parse_references(raw)
    assert (ref.title, ref.authors, ref.year, ref.venue) == (title, authors, year, venue)
    assert 0 <= ref.parse_confidence <= 1


def test_paragraphs_and_empty():
    assert parse_references(" \n\n") == []
    refs = parse_references(
        "Smith (2020). The first title. Nature.\n\nJones (2021). The second title. Science."
    )
    assert len(refs) == 2
    assert all(ref.label is None for ref in refs)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("https://doi.org/10.1234/ABC.", "10.1234/abc"),
        ("DOI: 10.1234/ABC);", "10.1234/abc"),
        ("10.1234/thing(2020).", "10.1234/thing(2020)"),
        ("https://doi.org/10.1234%2FABC", "10.1234/abc"),
        ("not a DOI", None),
    ],
)
def test_doi_normalization(value, expected):
    assert normalize_doi(value) == expected


@pytest.mark.parametrize(
    "raw,kind",
    [
        ("Smith (2020). A useful book. Cambridge University Press.", "book"),
        ("WHO (2023). Global tuberculosis report. Geneva: WHO.", "report"),
        ("Smith (2020). A useful dataset. Zenodo [Dataset].", "dataset"),
        ("Smith (2020). A useful chapter. En Jones (ed.). The book (pp. 1–9).", "chapter"),
        ("Smith (2020). A useful preprint. arXiv:2001.12345v2.", "preprint"),
        ("A useful website https://example.org", "web"),
    ],
)
def test_kind(raw, kind):
    assert parse_references(raw)[0].kind_guess == kind


def test_identifiers_without_title():
    (ref,) = parse_references("https://doi.org/10.1234/example")
    assert ref.title is None and ref.doi == "10.1234/example"
    (ref,) = parse_references(
        "Smith (2020). A useful title. https://arxiv.org/abs/hep-th/9901001v2"
    )
    assert ref.arxiv_id == "hep-th/9901001v2"


def test_markdown_title_and_url():
    (ref,) = parse_references("Smith (2020). [A linked title](https://example.org/work). Nature.")
    assert ref.title == "A linked title"
    assert ref.url == "https://example.org/work"


@pytest.mark.parametrize(
    "raw,authors",
    [
        ("Smith, John. “A history of science.” Nature 12 (2020): 1–9.", ["Smith"]),
        ("WHO (2023). Global tuberculosis report. Geneva: WHO.", ["WHO"]),
        (
            "World Health Organization (2023). Global tuberculosis report. Geneva: WHO.",
            ["World Health Organization"],
        ),
        ("Smith J. ‘A history of science.’ Nature. 2020;1:2–9.", ["Smith"]),
    ],
)
def test_chicago_and_institutional_authors(raw, authors):
    (ref,) = parse_references(raw)
    assert ref.authors == authors
    assert ref.title in {"A history of science", "Global tuberculosis report"}


def test_horizontal_rule_ends_reference_list():
    block = (
        "1. Smith, J. (2020). Soil water under cover crops. *Geoderma*, 1, 2.\n"
        "2. Lee, K. (2021). Termination timing. *Field Crops Research*, 3, 4.\n\n"
        "---\n\n"
        "*All placeholders marked [[TO COMPLETE: ...]] will be finalised later.*\n"
    )
    refs = parse_references(block)
    assert len(refs) == 2
    assert refs[1].title == "Termination timing"
    assert "placeholders" not in refs[1].raw


@pytest.mark.parametrize(
    ("raw", "title", "first", "venue"),
    [
        (
            "Balaban NQ, Helaine S, Lewis K, et al. Definitions and guidelines for research on "
            "antibiotic persistence. *Nat Rev Microbiol*. 2019;17(7):441–448.",
            "Definitions and guidelines for research on antibiotic persistence",
            "Balaban",
            "Nat Rev Microbiol",
        ),
        (
            "Barcia-Macay M, Seral C, Mingeot-Leclercq MP, Tulkens PM, Van Bambeke F. "
            "Pharmacodynamic evaluation of the intracellular activities of antibiotics against "
            "Staphylococcus aureus in a model of THP-1 macrophages. Antimicrob Agents Chemother. "
            "2006;50(3):841-851.",
            "Pharmacodynamic evaluation of the intracellular activities of antibiotics against "
            "Staphylococcus aureus in a model of THP-1 macrophages",
            "Barcia-Macay",
            "Antimicrob Agents Chemother",
        ),
    ],
)
def test_vancouver_entries(raw, title, first, venue):
    (ref,) = parse_references(f"1. {raw}")
    assert ref.title == title
    assert ref.authors[0] == first
    assert "Van Bambeke" in ref.authors or len(ref.authors) == 3
    assert ref.venue == venue
    assert ref.year in (2019, 2006)


def test_pensoft_author_year_format():
    refs = parse_references(
        '1. Berendsohn W. G. 1995. The concept of "potential taxa" in databases. Taxon. 44. 2. '
        "207. 212. https://doi.org/10.2307/1222443\n"
        "2. Crawford D. J., Mort M. E. 2005. Phylogeny of Eastern North American Coreopsis. "
        "American Journal of Botany. 92. 2. 330. 336.\n"
    )
    assert refs[0].authors == ["Berendsohn"] and refs[0].year == 1995
    assert refs[0].title == 'The concept of "potential taxa" in databases'
    assert refs[1].authors == ["Crawford", "Mort"]
    assert refs[1].title == "Phylogeny of Eastern North American Coreopsis"
    assert refs[1].venue == "American Journal of Botany"


def test_vancouver_authors_with_parenthesised_year():
    refs = parse_references(
        "1. Allison KR, Brynildsen MP, Collins JJ. (2011). Metabolite-enabled eradication of "
        "bacterial persisters by aminoglycosides. *Nature*, 473(7346), 216–220.\n"
    )
    assert refs[0].authors == ["Allison", "Brynildsen", "Collins"] and refs[0].year == 2011
    assert (
        refs[0].title == "Metabolite-enabled eradication of bacterial persisters by aminoglycosides"
    )
    assert refs[0].venue == "Nature"


def test_markdown_link_doi_stops_at_the_link_syntax():
    raw = (
        "Peel, L., Peixoto, T. P., & De Domenico, M. (2022). Statistical inference links data and "
        "theory in network science. *Nature Communications, 13*, 6794. "
        "[https://doi.org/10.1038/s41467-022-34267-9](https://doi.org/10.1038/s41467-022-34267-9)."
    )
    (ref,) = parse_references(raw)
    assert ref.doi == "10.1038/s41467-022-34267-9"
    assert ref.url == "https://doi.org/10.1038/s41467-022-34267-9"
    # Parentheses inside a DOI are kept; only an unbalanced closer is trimmed.
    assert normalize_doi("(https://doi.org/10.1016/S0140-6736(20)30183-5)") == (
        "10.1016/s0140-6736(20)30183-5"
    )


def test_straight_single_quoted_title_is_not_merged_with_the_venue():
    raw = (
        "1. Vauzernac, M.; Rouvessac, H.; Brzełowska, A. (2023). 'Matrix-matched headspace "
        "calibration for chilled rice and poultry preparations.' *Journal of Quantitative Food "
        "Measurement*, 7(2), 41–56.\n"
    )
    ref = parse_references(raw)[0]
    assert (
        ref.title
        == "Matrix-matched headspace calibration for chilled rice and poultry preparations"
    )
    assert ref.authors == ["Vauzernac", "Rouvessac", "Brzełowska"]
    assert parse_references("1. O'Brien, K. (2020). A title about things. Journal, 3, 1-2.\n")[
        0
    ].authors == ["O'Brien"]
