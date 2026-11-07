These are real service responses captured on 2026-10-30. `manifest.json` records request
metadata, status, content type and capture time. Credentials and request headers are excluded.
`tests/evidence/record_fixtures.py` captures only missing fixtures; normal tests never run it.

Successful captures cover the Kobak et al. article (Crossref search and DOI CSL), Vaswani et al.
(arXiv Atom and OpenAlex), Zenodo software (DataCite CSL), *The Elements of Statistical Learning*
(Crossref), and the WHO *Global tuberculosis report 2023* (HTML and Exa search). The Zenodo
example is software rather than a dataset, as identified by the source metadata.

The initial book DOI and WHO URL returned 404; those responses are retained separately from
the corrected successful examples. Semantic Scholar returned 403, so its successful response
shape is tested with an explicitly synthetic payload in `test_resolvers.py`. The fixture
`attention_openalex.json` actually maps the requested arXiv DOI to a 2025 record with DOI
`10.65215/2q58a426`; tests preserve this discrepancy rather than changing the source response.

`fabricated_references.json` contains intentionally synthetic citations: invented work, wrong
authors, a DOI attached to an unrelated title, and an unresolved DOI. Searches for the invented
title and the DOI's three 404 responses were captured live. Other tests construct small synthetic
payloads to exercise failures and corner cases; those are not represented as live captures.
