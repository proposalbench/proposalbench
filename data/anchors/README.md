# Anchor proposals

This is a curated set of **11 real, published research proposals**, containing
**598 source reference entries**. 4 have affirmative funding evidence; the other
7 have unknown award status. All meet the published-proposal inclusion route.
Publication is not evidence of funding. Per-document `funded` and `funded_source` fields
make this distinction explicit; do not call this an exclusively funded baseline.

These documents are human baseline material, never tasks, applicant dossiers, model inputs,
or model generations. Use them only to measure reference-checker false positives, calibrate
reference-density thresholds (including EV1), characterize human proposal style, and check
whether the admissibility gate wrongly rejects real proposals. They provide no human panel
scores and do not validate fundability, scientific merit, or judge-model rankings.

`NOT_FOUND` remains unpenalised in v0.1. This collection does not change that rule or claim
the required ≤2% false-positive rate. Published references are not guaranteed correct:
source errors, inaccessible reports, and imperfect metadata are deliberately preserved.
The reference checker has not been run and no reference labels have been manufactured.
Before changing the rule, audit real reference defects and define the indexable subset and
false-positive denominator. Likewise, total references are not necessarily external,
verified references: EV1 calibration requires that distinction.

## Selection and provenance

Snapshot retrieved 2026-10-30. Include a real, full published proposal narrative under
document-level CC BY 4.0 or CC0, with substantial scientific text, parseable headings,
and preferably at least 15 references. All selected documents have at least 15. Prefer
structured JATS over PDF. All selected licences are CC BY 4.0; no CC0 document was needed.
Several funders and fields are represented, including NIH, NSF, ERC/Horizon 2020, COST,
national European funders, Chile's FONDECYT and the foundation-backed Open Science Prize.
The Spanish Zenodo item is a published doctoral research proposal, not evidence of a grant
award. It includes short English abstracts of preliminary outputs, as in its source.

This is a convenience sample, dominated by RIO and English, with substantial ecology coverage.
It is not a random or representative sample of grants, languages, countries or award outcomes.
Its reference lists must not be assumed to describe any wider population's error rate.
Published proposals may have been adapted from the submitted versions; the anchors preserve
the published narrative, not unavailable submission forms or external supplementary files.

| id | Funder / scheme | Field | Language | Words | References | Licence |
| --- | --- | --- | --- | ---: | ---: | --- |
| [rio-7576](rio-7576/proposal.md) | German Research Foundation (DFG) / DFG research grant | computing / software engineering | en | 9159 | 65 | CC BY 4.0 |
| [rio-8816](rio-8816/proposal.md) | National Institutes of Health (NIH) / BD2K Advancing Biomedical Science Using Crowdsourcing and Interactive Digital Media (UH2) | life sciences / neuroinformatics | en | 11486 | 27 | CC BY 4.0 |
| [rio-10610](rio-10610/proposal.md) | National Science Foundation (NSF) / Advances in Biological Informatics (ABI Development) | ecology / biodiversity informatics | en | 12379 | 118 | CC BY 4.0 |
| [rio-31430](rio-31430/proposal.md) | Swiss National Science Foundation (SNSF); Swiss Agency for Development and Cooperation (SDC) / Swiss Programme for Research on Global Issues for Development (r4d) | social science / environmental governance | en | 10596 | 106 | CC BY 4.0 |
| [rio-34564](rio-34564/proposal.md) | European Research Council (ERC) / ERC Starting Grant / Horizon 2020, grant 677232 (ECOWORM) | ecology / ecosystem functioning | en | 7638 | 88 | CC BY 4.0 |
| [rio-8649](rio-8649/proposal.md) | Wellcome Trust; National Institutes of Health (NIH); Howard Hughes Medical Institute / Open Science Prize | computing / research data management | en | 2324 | 21 | CC BY 4.0 |
| [rio-14939](rio-14939/proposal.md) | Netherlands eScience Center (NLeSC) / Accelerating Scientific Discovery (ASDI), ASDI.2016.014 | ecology / remote sensing | en | 4662 | 58 | CC BY 4.0 |
| [rio-21305](rio-21305/proposal.md) | Swedish Research Council for Sustainable Development (Formas) / Formas open call 2017 | social science / energy policy | en | 3401 | 17 | CC BY 4.0 |
| [rio-11731](rio-11731/proposal.md) | Fondo Nacional de Desarrollo Científico y Tecnológico (FONDECYT), Chile / FONDECYT research proposal | life sciences / biomedical engineering | en | 3732 | 18 | CC BY 4.0 |
| [rio-13828](rio-13828/proposal.md) | European Cooperation in Science and Technology (COST) / COST Action PESFOR-W (CA15206) | ecology / environmental economics | en | 8807 | 20 | CC BY 4.0 |
| [zenodo-17726004](zenodo-17726004/proposal.md) | Not stated (Universidad EAFIT doctoral proposal) / Doctorado en Ingeniería — thesis research proposal | engineering / computational seismology | es | 8123 | 60 | CC BY 4.0 |

`words` is exactly `count_words(parse_proposal(markdown).body_text())`; the body includes
headings, captions and retained tables and excludes the final reference block. `reference_count`
is exactly `len(parse_references(parsed.references_block))`, checked against an independent
source count (JATS `ref` elements or 60 author-year entries in the Spanish PDF). Neither is
an external-reference or verified-reference count. YAML `year` is publication year; source
application years, where supplied, remain in the narrative and scheme evidence.

## Reproduction and conversion

```sh
uv run python tools/authoring/collect_anchors.py
uv run python tools/authoring/collect_anchors.py --offline
uv run python tools/authoring/collect_anchors.py --check
```

The collector uses project dependencies and Poppler `pdftotext` (24.02.0 used here).
It downloads to gitignored `seeds_raw/anchors/`, checks pinned XML/PDF SHA-256 values,
verifies each document's licence, converts the texts, validates parser counts and checksums,
and writes only the requested anchor files, this README, the appended attribution section,
and `.codex-handoff/anchors.md`. Cached sources support offline reproduction. A changed
source is rejected for human review; it is never silently substituted. Zenodo record metadata
is retained separately with its own digest and licence/file-checksum evidence.

JATS heading hierarchy, paragraphs, lists, captions and available tables are retained.
Structured citations need punctuation separators; their fields and order are preserved,
without index lookups or repairs. Exact publisher-duplicated back-note sections appear once.
References move to the end, after captions and other back matter. Front-matter correspondence,
affiliations, ORCIDs, licence statements, dates received/accepted and journal boilerplate are
omitted. Author names are recorded in YAML and attributed below. No biography is synthesized.

The Spanish PDF conversion is document-specific: it removes the cover, contents page,
running headers and chart labels; restores display mathematics and the algorithm; reflows
paragraphs and line-end hyphenation; retains nine figure captions and the timetable caption;
and renames `Referencias` to `References`. The table's visual bars are not reconstructed.
Source spelling and mathematical inconsistencies are retained. Author names and full title
follow the PDF cover, with differences from repository metadata documented in its YAML.
Layout changes, caption placement and equation markup can affect style and word diagnostics;
use those diagnostics with these conversion limitations in view.

Privacy review covers the retained narrative as well as automated identifier scans. No email,
telephone, ORCID, applicant identifier, private biography, or participant-level personal data
is retained. Scholarly author/collaborator names, institutional affiliations, research roles,
publications, and scientific project descriptions remain part of the published research text.

## Sources searched and screening log

Searched RIO's article-type browser (NIH, NSF, H2020 and general Grant Proposal), older
Grant Proposal pages 7–10, RIO's journal/grant-proposal blog, and Crossref's RIO journal
metadata. Individual article XML, not the journal's general policy, supplies licence evidence.
Also inspected the current `ethanwhite/ogrants` GitHub tree, README, LICENSE.md, proposal
folder and Zhu entry/PDF. External catalogue links do not inherit the catalogue licence.
Zenodo was searched for Spanish research proposals; record 17726004 explicitly declares
`publication/proposal`, Spanish, and `cc-by-4.0`. A generic Zenodo API search returned HTTP
400; direct record access succeeded. Web searches included “propuesta de investigación”,
“memoria proyecto Proposal”, and RIO grant proposal/funder queries. Generic writing guides,
ordinary research articles and search-only hits were not treated as proposal candidates.

Rejected after document screening:

- [RIO 7479 — HeQuCoG](https://riojournal.com/article/7479/): CC BY 4.0 verified, 26 references, funded. Excluded because the full proposal includes extensive academic CVs and personal career histories; prefer an intact scientific narrative without those privacy-sensitive appendices.
- [RIO 9115 — Widening the circle of care (v2)](https://riojournal.com/article/9115/): CC BY 4.0 verified and funded, but the retrieved JATS has no ref-list (0 entries). Not used as a reference-checking anchor.
- [RIO 7573 — Wiki4R](https://riojournal.com/article/7573/): CC BY 4.0 verified; no structured reference list in downloaded JATS (0 entries).
- [RIO 8424 — ContentMine/Hypothes.is](https://riojournal.com/article/8424/): CC BY 4.0 verified; only 1 reference, below the preferred minimum.
- [RIO 8834 — Visual Parkinson’s Disease Rating Scale](https://riojournal.com/article/8834/): CC BY 4.0 verified; only 9 references, below the preferred minimum.
- [RIO 8880 — Open research strategies in development institutions](https://riojournal.com/article/8880/): CC BY 4.0 verified; only 6 references, below the preferred minimum.
- [RIO 11321 — DNAqua-Net](https://riojournal.com/article/11321/): CC BY 4.0 verified; 13 references. PESFOR-W provides a COST proposal with at least 15.
- [RIO 11624 — BBSRC data management plan](https://riojournal.com/article/11624/): A data management plan, not a full research proposal; only 5 references.
- [Open Grants — Rebecca Zhu 2018](https://github.com/ethanwhite/ogrants/blob/main/proposals/zhu_rebecca_2018.pdf): Only file in proposals/ in the inspected current repository. No document-specific CC BY 4.0 statement found in the PDF. Current LICENSE.md licenses catalogue data CC0, while README says proposals are linked, not hosted. This is insufficient to establish the PDF's licence. Also contains an applicant identifier and extensive personal CV material.

Additional JATS candidates screened but not selected (not licence rejections):

- [RIO 8815](https://riojournal.com/article/8815/): 23 references; biographical narrative; NIH represented by 8816.
- [RIO 8817](https://riojournal.com/article/8817/): 30 references; overlapping NIH author/topic with 8816.
- [RIO 8835](https://riojournal.com/article/8835/): 32 references; biographical narrative and overlapping NIH topic.
- [RIO 8848](https://riojournal.com/article/8848/): 26 references; overlapping NIH author/topic.
- [RIO 8814](https://riojournal.com/article/8814/): 23 references; biographical sketch; NSF represented by 10610.
- [RIO 57036](https://riojournal.com/article/57036/): 59 references; large consortium narrative; bounded initial set.
- [RIO 8865](https://riojournal.com/article/8865/): 25 references; autobiographical preliminary-work narrative; software engineering represented by 7576.
- [RIO 9232](https://riojournal.com/article/9232/): 21 references; bounded initial set.
- [RIO 14944](https://riojournal.com/article/14944/): 59 references; ecology already represented.
- [RIO 21774](https://riojournal.com/article/21774/): 16 references; COST already represented.

## Attribution and document-level licence evidence

- **Stefan Wagner.** (2015). *Continuous and Focused Developer Feedback on Software Quality (CoFoDeF)*. [Source](https://riojournal.com/article/7576/), [DOI](https://doi.org/10.3897/rio.1.e7576). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-7576/anchor.yaml](rio-7576/anchor.yaml) for conversion details.

- **Arno Klein.** (2016). *A game for crowdsourcing the segmentation of BigBrain data*. [Source](https://riojournal.com/article/8816/), [DOI](https://doi.org/10.3897/rio.2.e8816). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-8816/anchor.yaml](rio-8816/anchor.yaml) for conversion details.

- **Nico Franz; Edward Gilbert; Bertram Ludäscher; Alan Weakley.** (2016). *Controlling the taxonomic variable: Taxonomic concept resolution for a southeastern United States herbarium portal*. [Source](https://riojournal.com/article/10610/), [DOI](https://doi.org/10.3897/rio.2.e10610). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-10610/anchor.yaml](rio-10610/anchor.yaml) for conversion details.

- **René Véron; Nishara Fernando; N. C. Narayanan; Bishnu Upreti; Babu Ambat; Ranga Pallawala; Sudarshan Rajbhandari; Swetha Rao Dhananka; Christian Zurbrügg.** (2018). *Social processes in post-crisis municipal solid waste management innovations: A proposal for research and knowledge exchange in South Asia*. [Source](https://riojournal.com/article/31430/), [DOI](https://doi.org/10.3897/rio.4.e31430). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-31430/anchor.yaml](rio-31430/anchor.yaml) for conversion details.

- **Nico Eisenhauer; Olga Ferlian; Dylan Craven; Jes Hines; Malte Jochum.** (2019). *Ecosystem responses to exotic earthworm invasion in northern North American forests*. [Source](https://riojournal.com/article/34564/), [DOI](https://doi.org/10.3897/rio.5.e34564). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-34564/anchor.yaml](rio-34564/anchor.yaml) for conversion details.

- **Stephanie Simms; Sarah Jones; Kevin Ashley; Marta Ribeiro; John Chodacki; Stephen Abrams; Marisa Strong.** (2016). *Roadmap: A Research Data Management Advisory Platform*. [Source](https://riojournal.com/article/8649/), [DOI](https://doi.org/10.3897/rio.2.e8649). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-8649/anchor.yaml](rio-8649/anchor.yaml) for conversion details.

- **W. Daniel Kissling; Arie C. Seijmonsbergen; Ruud P. B. Foppen; Willem Bouten.** (2017). *eEcoLiDAR, eScience infrastructure for ecological applications of LiDAR point clouds: reconstructing the 3D ecosystem structure for animals at regional to continental scales*. [Source](https://riojournal.com/article/14939/), [DOI](https://doi.org/10.3897/rio.3.e14939). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-14939/anchor.yaml](rio-14939/anchor.yaml) for conversion details.

- **Kristina Ek; Susana Goytia; Carina Lundmark; Soili Nysten-Haarala; Maria Pettersson; Annica Sandström; Johanna Söderasp; Jesper Stage.** (2017). *Challenges in Swedish hydropower – politics, economics and rights*. [Source](https://riojournal.com/article/21305/), [DOI](https://doi.org/10.3897/rio.3.e21305). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-21305/anchor.yaml](rio-21305/anchor.yaml) for conversion details.

- **Steren Chabert; Tomás Mardones; Rodrigo Riveros; Maximiliano Godoy; Alejandro Veloz; Rodrigo Salas; Pablo Cox.** (2017). *Applying machine learning and image feature extraction techniques to the problem of cerebral aneurysm rupture*. [Source](https://riojournal.com/article/11731/), [DOI](https://doi.org/10.3897/rio.3.e11731). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-11731/anchor.yaml](rio-11731/anchor.yaml) for conversion details.

- **Gregory Valatin; Jens Abildtrup; Cristian Accastello; Abdel Rahman Mohammad Said Al-Tawaha; Maria-Beatrice Andreucci; Silvia Atanasova; Mersudin Avdibegović; Nikolina Baksic; Kazimierz Banasik; Jose Barquin; Johan Barstad; Viera Bastakova; Dzenan Becirovic; Santiago Begueria; Uldis Bethers; Maria Bihunova; Bosko Blagojevic; Matthias Bösch; Thomas Bournaris; Yiying Cao; Claudia Carvalho-Santos; Alexander Chikalanov; Maria A. Cunha e Sá; Krzysztof Czyżyk; Hamed Daly; Helen Davies; Antonio Del Campo; Rudolf de Groot; Rik De Vreese; Tomáš Dostál; Abdelmohssin El Mokaddem; Leena Finér; Rhys Evans; Julien Fiquepron; Magdalena Frac; Martyn Futter; Serge Garcia; Paola Gatto; Davide Geneletti; Veronika Gezik; Carlo Giupponi; María González-Sanchís; Fernando Gordillo; Elena Gorriz; Yulia Grigorova; Katrin Heinsoo; Eduard Hochbichler; Lars Högbom; Mike Image; Jette Bredahl Jacobsen; Anže Japelj; Sreten Jelic; Jürgen Junk; Csaba Juhasz; Ifigenia Kagalou; Mary Kelly-Quinn; Anna Klamerus-Iwan; Tatiana Kluvankova; Roland Koeck; Iskra Konovska; Silvija Krajter Ostoic; Janez Krc; Vasyl Lavnyy; Alessandro Leonardi; Zane Libiete; Declan Little; Antonio Lo Porto; Athanasios Loukas; Mariyana Ivanova Lyubenova; Bruno Maric; Javier Martínez-López; Inazio Martinez; Alexandru Maxim; Marek Metslaid; Alison Melvin; Mihai Costică; Ivan Mincev; Zymantas Morkvenas; Radovan Nevenic; Tom Nisbet; Daire O'hUallachain; Roland Olschewski; Johan Östberg; Karolina Oszust; Paola Ovando; Alessandro Paletto; Taras Parpan; Davide Pettenella; Špela Pezdevšek Malovrh; Špela Planinšek; Radka Podlipná; Stjepan Posavec; Kristina Potočki; Irina Prokofieva; Paula Quinteiro; Laszlo Radocz; Ratko Ristic; Nicolas Robert; Benedetto Rugani; Jelena Sabanovic; Zuzana Sarvasova; Snezana Savoska; Patrick Schleppi; Gebhard Schueler; Margaret Shannon; Martyn Silgram; Bojan Srdjevic; Gavril Stefan; Aleksandar Stijovic; Niels Strange; Sirkka Tattari; Aco Teofilovski; Mette Termansen; Bo Jellesmark Thorsen; Attila Toth; Ivonne Trebs; Novica Tmušić; Lampros Vasiliades; Suzanne Elizabeth Vedel; Kateřina Ventrubová; Dijana Vuletic; Georg Winkel; Richard Yao; Sarah Young; Rasoul Yousefpour; Lyudmyla Zahvoyska; Daowei Zhang; Jianhua Zhou; Eva Žižková.** (2017). *PESFOR-W: Improving the design and environmental effectiveness of woodlands for water Payments for Ecosystem Services*. [Source](https://riojournal.com/article/13828/), [DOI](https://doi.org/10.3897/rio.3.e13828). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [rio-13828/anchor.yaml](rio-13828/anchor.yaml) for conversion details.

- **Oscar Rincón-Cardeño; Nicolás Guarín-Zapata; Silvana Montoya-Noguera.** (2025). *Aprendizaje automático en el modelado de la propagación de ondas: De los métodos numéricos estándar a las redes neuronales informadas por la física en sismología*. [Source](https://zenodo.org/records/17726004), [DOI](https://doi.org/10.5281/zenodo.17726004). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: converted to Markdown; layout removed. See [zenodo-17726004/anchor.yaml](zenodo-17726004/anchor.yaml) for conversion details.

Each `anchor.yaml` contains a `licence_evidence` object with the exact source URL,
metadata location, value and source digest. For RIO this is the article-specific
`front/article-meta/permissions/license/@xlink:href`; for Zenodo it is
`metadata.license.id`, tied to the exact PDF filename and repository checksum.
