from proposalbench.tasks.validate import _quote_norm, _quoted_pieces


def _found(description: str, bundle: str) -> list[bool]:
    received = _quote_norm(bundle)
    return [_quote_norm(q) in received for q in _quoted_pieces(description)]


def test_nested_quotation_matches_source_double_quotes():
    bundle = 'WP4 was literally called "Thresholds and planning integration", and they missed it.'
    desc = "The brief says (\"WP4 was literally called 'Thresholds and planning integration'\")."
    assert _found(desc, bundle) == [True]


def test_curly_quotes_and_emphasis_are_normalised():
    bundle = "The call requires **at least three** independent legal entities in the Union."
    desc = "It requires “at least three independent legal entities in the Union.”"
    assert _found(desc, bundle) == [True]


def test_stale_quotation_is_reported():
    bundle = "Tie each research activity to a named change in teaching or assessment."
    desc = 'The call says "explain which change in teaching each research activity informs".'
    assert _found(desc, bundle) == [False]


def test_seed_overlap_ignores_cited_web_addresses():
    from proposalbench.tasks.validate import _ngrams

    url = "https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2027/wp_horizon-erc-2027_en.pdf"
    seed = f"Source: {url}\n\nThe ERC Work Programme sets the rules."
    call = f"Rules follow the work programme ({url}) as adopted for 2027."
    assert not _ngrams(seed) & _ngrams(call)


def test_single_quoted_passages_are_checked_and_apostrophes_do_not_end_them():
    bundle = "Phase 2 consent covered the MEMS Cap and the PI's diaries, but not pharmacy records."
    good = (
        "resources.md: 'Phase 2 consent covered the MEMS Cap and the PI's diaries'. "
        "The partners' view"
    )
    stale = "The report says 'Consent in both phases covered devices, diaries and visits only'."
    assert _found(good, bundle) == [True]
    assert _found(stale, bundle) == [False]


def test_table_row_quoted_as_prose_matches():
    bundle = "| Unit established | no |\n| Signed service contracts | none |"
    assert _found(
        'The register says "Unit established: no" and "Signed service contracts: none".', bundle
    ) == [True, True]
