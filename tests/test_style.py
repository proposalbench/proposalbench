from proposalbench.checks.style import style_profile
from proposalbench.parse.sections import parse_proposal

SLOPPY = """## 1. Excellence

By leveraging cutting-edge methods, this groundbreaking project will delve into soils. It is
important to note that it not only advances science but also empowers farmers — a testament to
our holistic approach. By harnessing synergies, we unlock transformative change.

- point one
- point two
"""

PLAIN = """## 1. Excellence

We will measure soil water at 40 farms over three seasons. Probes record every 30 minutes and
are checked monthly against soil cores. We expect cover crops to raise stored water early in the
season and to cost water when they are terminated late.
"""


def test_sloppy_text_scores_higher_on_every_diagnostic():
    s = style_profile(parse_proposal(SLOPPY), "en")
    p = style_profile(parse_proposal(PLAIN), "en")
    assert s.buzzwords_per_1k > p.buzzwords_per_1k == 0
    assert s.em_dashes_per_1k > 0 == p.em_dashes_per_1k
    assert s.not_only_but_per_1k > 0
    assert s.gerund_openers_per_100_sentences > 0
    assert s.bullet_line_share > 0
    assert "delve*" in s.top_buzzwords
    assert s.excess_style_words_per_1k is not None


def test_spanish_profile_has_no_kobak_rate():
    text = (
        "## 1. Justificación\n\nNo solo mejora el bienestar sino también la cohesión. "
        "Cabe destacar el impacto sin precedentes.\n"
    )
    s = style_profile(parse_proposal(text), "es")
    assert s.excess_style_words_per_1k is None
    assert s.not_only_but_per_1k > 0
    assert s.buzzwords_per_1k > 0
