"""Reproduce the curated ProposalBench anchor snapshot (not benchmark tasks).

    uv run python tools/authoring/collect_anchors.py
    uv run python tools/authoring/collect_anchors.py --offline
    uv run python tools/authoring/collect_anchors.py --check

Uses httpx/PyYAML from the project and Poppler's pdftotext (24.02.0 at collection).
Downloads are cached under seeds_raw/anchors. Source hashes are pinned: changed source
bytes require another human rights/content review, never an automatic silent refresh.
The Spanish PDF has document-specific layout rules; these are not a general PDF parser.
No reference is corrected, completed from an index, or generated. No evaluation is run.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
import yaml

from proposalbench.parse.references import parse_references
from proposalbench.parse.sections import count_words, parse_proposal

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "seeds_raw" / "anchors"
OUT = ROOT / "data" / "anchors"
XLINK = "{http://www.w3.org/1999/xlink}href"
SNAPSHOT_DATE = "2026-10-30"
LICENCE_URL = "https://creativecommons.org/licenses/by/4.0/"

# Status concerns this application, not unrelated grants mentioned in the text.
# Unknown is deliberately different from an unsuccessful application.
RIO = [
    (
        7576,
        "German Research Foundation (DFG)",
        "DFG research grant",
        "computing / software engineering",
        65,
        "unknown",
        "Published as DFG Grant Proposal; the source does not establish an award.",
    ),
    (
        8816,
        "National Institutes of Health (NIH)",
        (
            "BD2K Advancing Biomedical Science Using Crowdsourcing and Interactive "
            "Digital Media (UH2)"
        ),
        "life sciences / neuroinformatics",
        27,
        "unknown",
        "JATS back/notes/Call identifies the UH2 call, but does not establish an award.",
    ),
    (
        10610,
        "National Science Foundation (NSF)",
        "Advances in Biological Informatics (ABI Development)",
        "ecology / biodiversity informatics",
        118,
        "unknown",
        (
            "JATS back/notes/Funding program and Grant title identify the "
            "application, but do not establish an award."
        ),
    ),
    (
        31430,
        (
            "Swiss National Science Foundation (SNSF); Swiss Agency for "
            "Development and Cooperation (SDC)"
        ),
        "Swiss Programme for Research on Global Issues for Development (r4d)",
        "social science / environmental governance",
        106,
        True,
        (
            "JATS back/ack: Funding for this project has been granted by the Swiss "
            "Programme for Research on Global Issues for Development (r4d "
            "programme)."
        ),
    ),
    (
        34564,
        "European Research Council (ERC)",
        "ERC Starting Grant / Horizon 2020, grant 677232 (ECOWORM)",
        "ecology / ecosystem functioning",
        88,
        True,
        (
            "JATS acknowledgements acknowledge ERC funding under Horizon 2020, "
            "grant agreement 677232; CORDIS project 677232 confirms ERC-STG / "
            "ERC-2015-STG."
        ),
    ),
    (
        8649,
        "Wellcome Trust; National Institutes of Health (NIH); Howard Hughes Medical Institute",
        "Open Science Prize",
        "computing / research data management",
        21,
        "unknown",
        (
            "JATS funding-group names the Open Science Prize and its three "
            "sponsors; no award is established."
        ),
    ),
    (
        14939,
        "Netherlands eScience Center (NLeSC)",
        "Accelerating Scientific Discovery (ASDI), ASDI.2016.014",
        "ecology / remote sensing",
        58,
        True,
        (
            "JATS back/notes/Funding program explicitly records an ASDI grant "
            "(ASDI.2016.014) from NLeSC."
        ),
    ),
    (
        21305,
        "Swedish Research Council for Sustainable Development (Formas)",
        "Formas open call 2017",
        "social science / energy policy",
        17,
        "unknown",
        (
            "JATS funding-group: submitted to Formas open call 2017; no decision "
            "had been made. Acknowledged Luleå support for writing is not evidence "
            "that Formas funded the application."
        ),
    ),
    (
        11731,
        "Fondo Nacional de Desarrollo Científico y Tecnológico (FONDECYT), Chile",
        "FONDECYT research proposal",
        "life sciences / biomedical engineering",
        18,
        "unknown",
        ("JATS funding-group identifies FONDECYT; publication alone does not establish an award."),
    ),
    (
        13828,
        "European Cooperation in Science and Technology (COST)",
        "COST Action PESFOR-W (CA15206)",
        "ecology / environmental economics",
        20,
        True,
        (
            "COST official Action CA15206 page confirms approval on 26 February "
            "2016 and operation from 18 October 2016 to 17 April 2021."
        ),
    ),
]

# Filled from the downloaded, individually reviewed source documents.
SOURCE_HASHES = {
    "rio-7576.xml": "19b1c8359f7ef6c2da876c42383fc517bff9383b1f5b9d9cac1c3661b80d5f30",
    "rio-8816.xml": "f834cef7cc8311c43e3978d2c8058b0bea70d79eea002061fbb9ea645a8ba5fb",
    "rio-10610.xml": "3f09271318a60033339bb03323c8f67e692635509e5e4c8d22e6f524271371a9",
    "rio-31430.xml": "6ed576a02dc6772a907c98b71903d099b430467ee6f09010e02baf4b32bf04f4",
    "rio-34564.xml": "d89aa3a7081f193a961c8b5a7909a413a5625e67058a5d6b43b3b7dfbe309816",
    "rio-8649.xml": "c1ffef1ca28bc86a168d3bac637dbda2514a18d3fd425c2c6290e6f7a7aed6f8",
    "rio-14939.xml": "a219d7c9fbd3615a4ea633f2055d5ac6cd9332b5bdb2fc2c24a05fa8c0b8cd44",
    "rio-21305.xml": "33c315381cbd5393ec93bc4cd71f824e4c74c866652c79f6f10fbfd77023b8fe",
    "rio-11731.xml": "7caf9e4f82aa84d791a528675028464528a1a90c176f019a5505a15aa27b8ece",
    "rio-13828.xml": "b86961ef517cf518030fcf980d0e25471e839ed02cb7eeed677a82a8b11b7059",
    "zenodo-17726004.pdf": "6d530850302e9993249763d99df7fab9d51b6a7f38ddc573581d4ad0e3871712",
}

REJECTED = [
    (
        "RIO 7479 — HeQuCoG",
        "https://riojournal.com/article/7479/",
        (
            "CC BY 4.0 verified, 26 references, funded. Excluded because the full "
            "proposal includes extensive academic CVs and personal career "
            "histories; prefer an intact scientific narrative without those "
            "privacy-sensitive appendices."
        ),
    ),
    (
        "RIO 9115 — Widening the circle of care (v2)",
        "https://riojournal.com/article/9115/",
        (
            "CC BY 4.0 verified and funded, but the retrieved JATS has no ref-list "
            "(0 entries). Not used as a reference-checking anchor."
        ),
    ),
    (
        "RIO 7573 — Wiki4R",
        "https://riojournal.com/article/7573/",
        "CC BY 4.0 verified; no structured reference list in downloaded JATS (0 entries).",
    ),
    (
        "RIO 8424 — ContentMine/Hypothes.is",
        "https://riojournal.com/article/8424/",
        "CC BY 4.0 verified; only 1 reference, below the preferred minimum.",
    ),
    (
        "RIO 8834 — Visual Parkinson’s Disease Rating Scale",
        "https://riojournal.com/article/8834/",
        "CC BY 4.0 verified; only 9 references, below the preferred minimum.",
    ),
    (
        "RIO 8880 — Open research strategies in development institutions",
        "https://riojournal.com/article/8880/",
        "CC BY 4.0 verified; only 6 references, below the preferred minimum.",
    ),
    (
        "RIO 11321 — DNAqua-Net",
        "https://riojournal.com/article/11321/",
        ("CC BY 4.0 verified; 13 references. PESFOR-W provides a COST proposal with at least 15."),
    ),
    (
        "RIO 11624 — BBSRC data management plan",
        "https://riojournal.com/article/11624/",
        "A data management plan, not a full research proposal; only 5 references.",
    ),
    (
        "Open Grants — Rebecca Zhu 2018",
        "https://github.com/ethanwhite/ogrants/blob/main/proposals/zhu_rebecca_2018.pdf",
        (
            "Only file in proposals/ in the inspected current repository. No "
            "document-specific CC BY 4.0 statement found in the PDF. Current "
            "LICENSE.md licenses catalogue data CC0, while README says proposals "
            "are linked, not hosted. This is insufficient to establish the PDF's "
            "licence. Also contains an applicant identifier and extensive personal "
            "CV material."
        ),
    ),
]
# These were screened and left out to avoid excess size or concentration in one author/field.
SCREENED_NOT_SELECTED = [
    (8815, "23 references; biographical narrative; NIH represented by 8816"),
    (8817, "30 references; overlapping NIH author/topic with 8816"),
    (8835, "32 references; biographical narrative and overlapping NIH topic"),
    (8848, "26 references; overlapping NIH author/topic"),
    (8814, "23 references; biographical sketch; NSF represented by 10610"),
    (57036, "59 references; large consortium narrative; bounded initial set"),
    (
        8865,
        (
            "25 references; autobiographical preliminary-work narrative; software "
            "engineering represented by 7576"
        ),
    ),
    (9232, "21 references; bounded initial set"),
    (14944, "59 references; ecology already represented"),
    (21774, "16 references; COST already represented"),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(name: str, url: str, *, offline: bool) -> bytes:
    path = RAW / name
    if not path.exists():
        if offline:
            raise FileNotFoundError(f"Missing cached source: {path}")
        response = httpx.get(url, follow_redirects=True, timeout=90)
        response.raise_for_status()
        data = response.content
        if name in SOURCE_HASHES and sha(data) != SOURCE_HASHES[name]:
            raise ValueError(f"Source changed: {url}; review before updating the pin")
        path.write_bytes(data)
    data = path.read_bytes()
    if name in SOURCE_HASHES and sha(data) != SOURCE_HASHES[name]:
        raise ValueError(f"Source hash mismatch: {path}")
    return data


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u200b", "").replace("\xad", "")).strip()


def plain(node: ET.Element | None) -> str:
    return clean("".join(node.itertext())) if node is not None else ""


def inline(node: ET.Element) -> str:
    parts = [node.text or ""]
    for child in node:
        value = inline(child)
        if child.tag == "italic":
            value = f"*{value}*" if value else ""
        elif child.tag == "bold":
            value = f"**{value}**" if value else ""
        elif child.tag in {"sub", "sup"}:
            value = f"<{child.tag}>{value}</{child.tag}>"
        elif child.tag == "ext-link":
            url = child.get(XLINK, "")
            if url and not url.startswith("mailto:") and value != url:
                value = f"[{value}]({url})"
        elif child.tag in {"email", "contrib-id"}:
            raise ValueError("Unexpected personal identifier in retained content")
        elif child.tag == "break":
            value = " "
        parts.extend([value, child.tail or ""])
    return clean("".join(parts))


def blocks(node: ET.Element, level: int = 2) -> str:
    """Render narrative recursively; never drop an unfamiliar content-bearing tag."""
    result = []
    for child in node:
        tag = child.tag
        if tag == "title":
            result.append(f"{'#' * min(level, 6)} {plain(child)}")
        elif tag == "sec":
            result.append(blocks(child, level + (1 if node.tag == "sec" else 0)))
        elif tag == "p":
            # Author-supplied bold subheadings are promoted, without rewording.
            if (
                len(child) == 1
                and child[0].tag == "bold"
                and not clean(child.text or "")
                and not clean(child[0].tail or "")
            ):
                result.append(f"{'#' * min(level + 1, 6)} {plain(child[0])}")
            else:
                result.append(inline(child))
        elif tag == "list":
            ordered = child.get("list-type") in {"order", "ordered"}
            for n, item in enumerate(child.findall("list-item"), 1):
                value = blocks(item, level).replace("\n\n", "\n  ")
                result.append(f"{str(n) + '.' if ordered else '-'} {value}")
        elif tag in {"fig", "table-wrap"}:
            result.append(render_float(child))
        elif tag in {"label", "caption", "fn", "def-list", "disp-quote"}:
            result.append(blocks(child, level) if len(child) else inline(child))
        elif tag in {"graphic", "supplementary-material"}:
            # Captions only; no embedded images or supplementary files.
            if child.find("caption") is not None:
                result.append(blocks(child.find("caption"), level))
        else:
            raise ValueError(f"Unreviewed block tag: {tag}")
    return "\n\n".join(x for x in result if x.strip())


def render_float(node: ET.Element) -> str:
    parts = [plain(node.find("label"))]
    caption = node.find("caption")
    if caption is not None:
        parts.append(blocks(caption, 4))
    # A caption is sufficient under the anchor contract. Prefer tables when possible.
    table = node.find(".//table")
    if table is not None:
        rows = []
        occupied = {}
        for row_index, row in enumerate(table.findall(".//tr")):
            cells = []
            column = 0
            for cell in row:
                if cell.tag not in {"td", "th"}:
                    continue
                while occupied.get((row_index, column), False):
                    cells.append("")
                    column += 1
                colspan = int(cell.get("colspan", "1"))
                rowspan = int(cell.get("rowspan", "1"))
                cells.append(inline(cell).replace("|", r"\|"))
                cells.extend([""] * (colspan - 1))
                for future_row in range(row_index + 1, row_index + rowspan):
                    for future_col in range(column, column + colspan):
                        occupied[future_row, future_col] = True
                column += colspan
            rows.append(cells)
        width = max((len(r) for r in rows), default=0)
        if width:
            formatted = ["| " + " | ".join(r + [""] * (width - len(r))) + " |" for r in rows]
            formatted.insert(1, "| " + " | ".join(["---"] * width) + " |")
            parts.append("\n".join(formatted))
    for foot in node.findall("table-wrap-foot"):
        parts.append(blocks(foot, 4))
    return "\n\n".join(x for x in parts if x)


def reference(ref: ET.Element) -> str:
    mixed = ref.find("mixed-citation")
    if mixed is not None:
        return plain(mixed)
    citation = ref.find("element-citation")
    if citation is None:
        raise ValueError("Reference has no supported citation node")
    pieces = []
    seen_urls = set()
    for e in citation:
        if e.tag == "person-group":
            people = []
            for person in e:
                if person.tag == "name":
                    people.append(
                        " ".join(
                            filter(
                                None,
                                [plain(person.find("surname")), plain(person.find("given-names"))],
                            )
                        )
                    )
                else:
                    people.append(plain(person))
            pieces.append(", ".join(people))
        elif e.tag == "pub-id" and e.get("pub-id-type") == "doi":
            doi_url = "https://doi.org/" + plain(e)
            if doi_url not in seen_urls:
                pieces.append(doi_url)
                seen_urls.add(doi_url)
        elif e.tag in {"uri", "ext-link"}:
            url = plain(e) or e.get(XLINK, "")
            if url not in seen_urls:
                pieces.append(url)
                seen_urls.add(url)
        else:
            pieces.append(plain(e))
    # JATS element-citation has no prose punctuation: only separators are supplied.
    return ". ".join(p.rstrip(".") for p in pieces if p).strip()


def rio_anchor(spec: tuple, offline: bool) -> tuple[str, dict]:
    number, funder, scheme, field, expected, funded, evidence = spec
    ident = f"rio-{number}"
    url = f"https://riojournal.com/article/{number}/"
    xml_url = url + "download/xml/"
    data = fetch(f"{ident}.xml", xml_url, offline=offline)
    root = ET.fromstring(data)
    meta = root.find("./front/article-meta")
    licence = meta.find("./permissions/license")
    licence_url = licence.get(XLINK, "") if licence is not None else ""
    if licence_url.rstrip("/").replace("http:", "https:") != LICENCE_URL.rstrip("/"):
        raise ValueError(f"{ident}: unapproved document licence {licence_url}")
    article_type = plain(meta.find("./article-categories/subj-group/subject"))
    if "Grant Proposal" not in article_type:
        raise ValueError(f"{ident}: not a grant proposal: {article_type}")
    title = plain(meta.find("./title-group/article-title"))
    authors = []
    for author in meta.findall('./contrib-group/contrib[@contrib-type="author"]'):
        name = author.find("name")
        authors.append(
            " ".join(filter(None, [plain(name.find("given-names")), plain(name.find("surname"))]))
            if name is not None
            else plain(author.find("collab"))
        )
    pieces = [f"# {title}"]
    for abstract in meta.findall("abstract"):
        pieces.append("## Abstract\n\n" + "\n\n".join(inline(e) for e in abstract if e.tag == "p"))
    pieces.append(blocks(root.find("body")))
    # Retain non-bibliographic back matter before the final reference block. Pensoft
    # exports some notes twice; exact repeated sections are emitted once.
    seen = set()
    for container in root.findall("./back/*"):
        if container.tag == "ref-list":
            continue
        children = list(container) if container.tag == "notes" else [container]
        for child in children:
            key = plain(child)
            if key in seen:
                continue
            seen.add(key)
            if child.tag == "sec" or child.tag in {"ack", "fn-group"}:
                pieces.append(blocks(child))
            else:
                raise ValueError(f"Unreviewed back matter {child.tag}")
    floats = root.find("floats-group")
    if floats is not None:
        for child in floats:
            if child.tag in {"fig", "table-wrap"}:
                pieces.append(render_float(child))
            elif child.tag == "fig-group":
                pieces.append(render_float(child))
                pieces.extend(render_float(fig) for fig in child.findall("fig"))
            elif child.tag != "supplementary-material":
                raise ValueError(f"Unreviewed float {child.tag}")
    refs = root.findall("./back/ref-list/ref")
    if len(refs) != expected:
        raise ValueError(f"{ident}: expected {expected} JATS references, got {len(refs)}")
    pieces.append("## References\n\n" + "\n\n".join(reference(r) for r in refs))
    text = "\n\n".join(p for p in pieces if p.strip()) + "\n"
    for paragraph in root.findall("./body//p"):
        if inline(paragraph) not in text and plain(paragraph) not in text:
            raise ValueError(f"{ident}: source body paragraph lost during conversion")
    notes = [
        (
            "Converted publisher JATS XML to Markdown; layout removed. "
            "Front-matter affiliations, correspondence/email, ORCID, licence and "
            "publication-history boilerplate omitted; published authors retained "
            "in metadata."
        ),
        (
            "Scientific narrative, source spelling, citations and reference "
            "metadata are not corrected. JATS structured references rendered in "
            "source order, one paragraph per entry; punctuation supplied between "
            "metadata fields, identical DOI URL repetitions suppressed."
        ),
        (
            "Figures retained as captions; tables rendered as Markdown where "
            "encoded as JATS tables. Floats and non-reference back matter precede "
            "the final References heading. Supplementary files are outside this "
            "published narrative snapshot."
        ),
        (
            "Exact duplicated publisher back-note sections emitted once. Bold-only "
            "source paragraphs promoted to subheadings. Zero-width spaces and "
            "discretionary soft hyphens removed."
        ),
    ]
    if root.findall(".//td[@colspan]"):
        notes.append(
            "Table spans expanded into empty cells to preserve column alignment; "
            "cell text retained once. Table shading and visual scheduling bars are "
            "not reproduced."
        )
    metadata = dict(
        id=ident,
        title=title,
        authors=authors,
        year=int(meta.findtext('./pub-date[@pub-type="epub"]/year')),
        funder=funder,
        scheme=scheme,
        funded=funded,
        funded_source={"url": xml_url, "evidence": evidence},
        language="en",
        field=field,
        source_url=url,
        doi=meta.findtext('./article-id[@pub-id-type="doi"]'),
        licence="CC-BY-4.0",
        licence_evidence={
            "url": xml_url,
            "location": "front/article-meta/permissions/license/@xlink:href",
            "value": licence_url,
            "statement": plain(licence),
        },
        retrieved=SNAPSHOT_DATE,
        raw_path=f"seeds_raw/anchors/{ident}.xml",
        raw_sha256=sha(data),
        article_type=article_type,
        source_reference_count=expected,
        conversion_notes=notes,
    )
    if number == 34564:
        metadata["funded_source"]["corroborating_url"] = (
            "https://cordis.europa.eu/project/id/677232"
        )
    if number == 13828:
        metadata["funded_source"]["url"] = "https://www.cost.eu/actions/CA15206/"
    return text, metadata


def dehyphenate(text: str) -> str:
    # Only line-end hyphenation, never hyphens within an extracted line.
    # These lexical compounds were checked in the source; retain their hyphens.
    for left, right in [("domain", "specific"), ("finite", "difference"), ("semi", "infinitos")]:
        text = re.sub(rf"\b{left}-\n\s*{right}\b", f"{left}-{right}", text)
    return re.sub(r"(?<=\w)-\n\s*(?=\w)", "", text)


def spanish_pdf(data: bytes) -> str:
    """Document-specific conversion of the 26-page, single-column EAFIT PDF."""
    path = RAW / "zenodo-17726004.pdf"
    if path.read_bytes() != data:
        raise ValueError("PDF cache changed")
    output = RAW / "zenodo-17726004-layout.txt"
    subprocess.run(["pdftotext", "-layout", str(path), str(output)], check=True)
    pages = output.read_text(encoding="utf-8").split("\f")
    if len(pages) != 27:
        raise ValueError("Unexpected PDF pagination")
    captions = []
    abstract = pages[1].split("Resumen", 1)[1]
    abstract = re.sub(r"\n(?=La investigación|Si bien|Como avance|En etapas)", "\n\n", abstract)
    retained = [abstract]
    for index in range(3, 26):  # cover and contents are layout; abstract retained above
        page = pages[index]
        page = re.sub(
            (
                "^\\s*(?:\\d+ / Propuesta de tesis|(?:Planteamiento del "
                "problema|Justificación|Estado del arte|References) / \\d+)\\s*\\n"
            ),
            "",
            page,
        )
        # Plot labels and timetable shading are graphics, represented by captions.
        if index in {4, 20}:
            page = page[page.index("Figura 1." if index == 4 else "Tabla 1.") :]
        elif index == 8:
            start = page.index("             Fracción de publicaciones")
            end = page.index("Figura 4.")
            page = page[:start] + page[end:]
        elif index == 16:
            start = page.index("                                      60 puntos")
            end = page.index("Figura 8.", start)
            page = page[:start] + page[end:]
        lines = page.splitlines()
        keep = []
        pos = 0
        while pos < len(lines):
            if re.match(r"^\s*(?:Figura [1-9]|Tabla 1)\. ", lines[pos]):
                cap = [lines[pos].strip()]
                pos += 1
                while pos < len(lines) and lines[pos].strip():
                    cap.append(lines[pos].strip())
                    pos += 1
                captions.append(clean(dehyphenate("\n".join(cap))))
            else:
                keep.append(lines[pos])
                pos += 1
        retained.append("\n".join(keep).strip("\n"))
    if len(captions) != 10:
        raise ValueError(
            f"Expected nine figure captions and one table caption, got {len(captions)}"
        )
    raw = "\n".join(retained)
    # Display equations transcribed in LaTeX from the source, including its original
    # Helmholtz coefficient. Do not "fix" mathematical inconsistencies in an anchor.
    equations = [
        (
            r"\s*\n.*?en ∂Ω\.",
            (
                "\\begin{cases}\\nabla^2 f + (5\\pi)^2 f = 0, &\\text{en }\\Omega,\\\\ f = 0, "
                "&\\text{en }\\partial\\Omega.\\end{cases}\\tag{1}"
            ),
        ),
        (r"^\s+f \(x, y\) = sin\(5πx\) sin\(5πy\)\.", r"f(x,y)=\sin(5\pi x)\sin(5\pi y)."),
        (r"^\s+f \(x\) = x3 \+ x2 − x − 1\.", r"f(x)=x^3+x^2-x-1."),
        (
            r"^\s+gi \(x\) = wi ReLU\(x − x∗i \) \+ yioffset ,",
            r"g_i(x)=w_i\operatorname{ReLU}(x-x_i^*)+y_i^{\mathrm{offset}},",
        ),
        (
            r"^\s+ReLU\(x − x∗i \) = máx\(0, x − x∗i \),",
            r"\operatorname{ReLU}(x-x_i^*)=\operatorname{máx}(0,x-x_i^*),",
        ),
        (
            r"^\s+N\n\s+X\n\s+f \(x\) ≈ fˆi \(x\) =\s+gi \(x\)\.\n\s+i=1",
            r"f(x)\approx\hat f_i(x)=\sum_{i=1}^N g_i(x).",
        ),
        (
            r"^\s+N \[u\(x, t\); λ\] = 0,\s+x ∈ Ω,\s+t ∈ \[0, T \],",
            r"\mathcal{N}[u(\mathbf{x},t);\lambda]=0,\quad \mathbf{x}\in\Omega,\quad t\in[0,T],",
        ),
        (
            r"^\s+B\[u\(x, t\)\] = 0, x ∈ Γ, t ∈ \[0, T \],",
            r"\mathcal{B}[u(\mathbf{x},t)]=0,\quad \mathbf{x}\in\Gamma,\quad t\in[0,T],",
        ),
        (
            r"^\s+u\(x, 0\) = u0 \(x\),\s+x ∈ Ω\.",
            r"u(\mathbf{x},0)=u_0(\mathbf{x}),\quad \mathbf{x}\in\Omega.",
        ),
        (
            r"^\s+L = LΩ \+ LΓ \+ LIC ,",
            r"L=L_{\Omega}+L_{\Gamma}+L_{\mathrm{IC}},",
        ),
        (
            r"^\s+fˆθ \(x, y\) = x\(1 − x\) y\(1 − y\) fθ \(x, y\),",
            r"\hat f_\theta(x,y)=x(1-x)y(1-y)f_\theta(x,y),",
        ),
    ]
    rendered = {}
    for n, (pattern, equation) in enumerate(equations):
        token = f"@@EQUATION{n}@@"
        flags = re.M | (re.S if n == 0 else 0)
        raw, count = re.subn(pattern, "\n\n" + token + "\n\n", raw, count=1, flags=flags)
        if count != 1:
            raise ValueError(f"Equation {n} no longer matches reviewed PDF extraction")
        rendered[token] = "$$\n" + equation + "\n$$"
    # Algorithm is a literal block, preserving nesting and mathematical roles.
    start = raw.index("Algoritmo 1. Red Neuronal Informada")
    end = raw.index("    Se consideran dos enfoques.", start)
    algorithm = raw[start:end].strip()
    algorithm = (
        algorithm.replace("θ(k+1)", "θ⁽ᵏ⁺¹⁾")
        .replace("θ(k)", "θ⁽ᵏ⁾")
        .replace("αk", "αₖ")
        .replace("LΩ", "L_Ω")
        .replace("LΓ", "L_Γ")
        .replace("LIC", "L_IC")
    )
    rendered["@@ALGORITHM@@"] = "```text\n" + algorithm + "\n```"
    raw = raw[:start] + "\n\n@@ALGORITHM@@\n\n" + raw[end:]
    body, refs = re.split(r"\n\s*Referencias\s*\n", raw, maxsplit=1)
    # Restore display-level superscripts and inline mathematical indices lost by
    # pdftotext; replacements are exact source strings, not scientific revisions.
    for old, new in [
        ("x∗i", "xᵢ*"),
        ("wi es", "wᵢ es"),
        ("yioffset", "yᵢᵒᶠᶠˢᵉᵗ"),
        ("[0, 1]2", "[0, 1]²"),
        ("101 s", "10¹ s"),
        ("102 s", "10² s"),
        ("10−2", "10⁻²"),
        ("10−1 s", "10⁻¹ s"),
    ]:
        body = body.replace(old, new)
    heading = re.compile(r"^(?:[1-7]\. [A-ZÁÉÍÓÚ]|[34]\.[12]\. )")
    paragraphs = []
    current = []

    def flush() -> None:
        if current:
            paragraphs.append(clean(dehyphenate("\n".join(current))))
            current.clear()

    for line in body.splitlines():
        value = line.strip()
        if not value:
            flush()
        elif value.startswith("@@"):
            flush()
            paragraphs.append(rendered[value])
        elif heading.match(value):
            flush()
            paragraphs.append(("### " if re.match(r"^[34]\.[12]\.", value) else "## ") + value)
        elif value.startswith(
            ("Comparative Analysis of Wave Scattering", "Evaluación de estrategias de aprendizaje")
        ):
            flush()
            current.append("### " + value)
        elif value.startswith("▶"):
            flush()
            current.append("- " + value[1:].strip())
        elif re.match(r"^\d\. (?:¿|Comparación:|Evaluación:|Escalamiento:)", value):
            flush()
            current.append(value)
        elif re.match(r"^ {3,4}\S", line) and current:
            # Normal first-line paragraph indentation in this document.
            flush()
            current.append(value)
        else:
            current.append(value)
    flush()
    refs = re.sub(r"\n(?=[A-ZÁÉÍÓÚ][^\n]*\((?:19|20)\d{2}\))", "\n\n", refs)
    entries = [clean(dehyphenate(r)) for r in re.split(r"\n\s*\n", refs) if r.strip()]
    if len(entries) != 60:
        raise ValueError(f"Expected 60 PDF references, extracted {len(entries)}")
    title = (
        "Aprendizaje automático en el modelado de la propagación de ondas: "
        "De los métodos numéricos estándar a las redes neuronales informadas "
        "por la física en sismología"
    )
    return (
        "# "
        + title
        + "\n\n## Resumen\n\n"
        + "\n\n".join(paragraphs + captions)
        + "\n\n## References\n\n"
        + "\n\n".join(entries)
        + "\n"
    )


def zenodo_anchor(offline: bool) -> tuple[str, dict]:
    import json

    url = "https://zenodo.org/records/17726004"
    api = "https://zenodo.org/api/records/17726004"
    record_bytes = fetch("zenodo-17726004.txt", api, offline=offline)
    record = json.loads(record_bytes)
    meta = record["metadata"]
    if meta["license"]["id"] != "cc-by-4.0" or meta["resource_type"]["subtype"] != "proposal":
        raise ValueError("Zenodo record no longer has the reviewed licence/resource type")
    source = record["files"][0]
    data = fetch("zenodo-17726004.pdf", source["links"]["self"], offline=offline)
    text = spanish_pdf(data)
    metadata = dict(
        id="zenodo-17726004",
        title=text.splitlines()[0][2:],
        authors=["Oscar Rincón-Cardeño", "Nicolás Guarín-Zapata", "Silvana Montoya-Noguera"],
        year=2025,
        funder="Not stated (Universidad EAFIT doctoral proposal)",
        scheme="Doctorado en Ingeniería — thesis research proposal",
        funded="unknown",
        funded_source={
            "url": url,
            "evidence": (
                "Published Zenodo proposal; neither the record nor the PDF establishes "
                "a funding award."
            ),
        },
        language="es",
        field="engineering / computational seismology",
        source_url=url,
        doi=meta["doi"],
        licence="CC-BY-4.0",
        licence_evidence={
            "url": api,
            "location": "metadata.license.id",
            "value": meta["license"]["id"],
            "resource_type": meta["resource_type"],
            "file": source["key"],
            "file_checksum": source["checksum"],
        },
        retrieved=SNAPSHOT_DATE,
        raw_path="seeds_raw/anchors/zenodo-17726004.pdf",
        raw_sha256=sha(data),
        metadata_raw_sha256=sha(record_bytes),
        article_type="Published doctoral research proposal",
        source_reference_count=60,
        conversion_notes=[
            (
                "Converted to Markdown; layout removed. Poppler pdftotext 24.02.0 "
                "-layout with document-specific, fail-closed equation and caption "
                "checks."
            ),
            (
                "Author names and full title follow the PDF cover. Zenodo shortens the "
                "title and lists the first creator as Rincón, Oscar A.; PDF roles are "
                "student, director and codirectora, respectively. No ORCIDs or cover "
                "qualifications retained."
            ),
            (
                "Cover, contents page and running headers removed. Nine figures and "
                "the shaded timetable retained as their ten source captions, collected "
                "before References; graphic labels removed. Body and source "
                "bibliography retained; Spanish Referencias heading renamed References."
            ),
            (
                "Display equations transcribed as LaTeX; algorithm retained in a "
                "literal block. Inline indices/powers restored where pdftotext loses "
                "vertical positioning. Source mathematical inconsistencies and "
                "typographical errors are not corrected."
            ),
            (
                "Line-break hyphenation removed; paragraphs reflowed. Abstracts of "
                "preliminary outputs in English and Spanish remain in the "
                "predominantly Spanish source. No reference metadata completed or "
                "repaired."
            ),
        ],
    )
    return text, metadata


def validate(text: str, metadata: dict, *, stored: bool = False) -> None:
    parsed = parse_proposal(text)
    if not parsed.references_block or not parsed.references_section:
        raise ValueError(f"{metadata['id']}: missing reference block")
    if parsed.sections[-1] is not parsed.references_section:
        raise ValueError("References must be the final heading")
    refs = parse_references(parsed.references_block)
    if len(refs) != metadata["source_reference_count"] or len(refs) < 15:
        raise ValueError(f"{metadata['id']}: reference count mismatch: {len(refs)}")
    # Ensure paragraph boundaries survived: no two bibliographic entries merged.
    if len(re.split(r"\n\s*\n", parsed.references_block)) != len(refs):
        raise ValueError("Reference paragraphs do not map one-to-one to parsed entries")
    words = count_words(parsed.body_text())
    if words < 300:
        raise ValueError("Too little narrative")
    privacy = re.compile(
        (
            "[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}|mailto:|orcid\\.org/|\\b(?:date of "
            "birth|born on|passport|social security "
            "number)\\b|\\b(?:Tel(?:ephone)?|Fax|Phone)\\s*:\\s*\\+?\\d"
        ),
        re.I,
    )
    if privacy.search(text):
        raise ValueError(f"{metadata['id']}: personal identifier needs review")
    if re.search(r"\w-\n\w", text) or "\f" in text or "\ufffd" in text:
        raise ValueError("Unresolved extraction artefact")
    if stored:
        if metadata["sha256"] != sha(text.encode("utf-8")):
            raise ValueError("Markdown checksum mismatch")
        if metadata["words"] != words or metadata["reference_count"] != len(refs):
            raise ValueError("Stored parser counts differ")
    else:
        metadata.update(sha256=sha(text.encode("utf-8")), words=words, reference_count=len(refs))
        metadata["privacy_review"] = (
            "Published scholarly names and institutional affiliations retained; "
            "correspondence, email, ORCID and front-matter contact blocks omitted. "
            "Retained narrative reviewed for contact identifiers, applicant "
            "identifiers, private biographical and participant-level personal "
            "data; none retained."
        )


def attribution(metadata: dict) -> str:
    return (
        f"- **{'; '.join(metadata['authors'])}.** ({metadata['year']}). "
        f"*{metadata['title']}*. [Source]({metadata['source_url']}), "
        f"[DOI](https://doi.org/{metadata['doi']}). "
        f"[CC BY 4.0]({LICENCE_URL}). Changes: converted to Markdown; layout removed. "
        f"See [{metadata['id']}/anchor.yaml]({metadata['id']}/anchor.yaml) for conversion details."
    )


def readme(records: list[dict]) -> str:
    rows = [
        "| id | Funder / scheme | Field | Language | Words | References | Licence |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for m in records:
        rows.append(
            f"| [{m['id']}]({m['id']}/proposal.md) | {m['funder']} / {m['scheme']} | "
            f"{m['field']} | {m['language']} | {m['words']} | {m['reference_count']} | CC BY 4.0 |"
        )
    funded = sum(m["funded"] is True for m in records)
    total = sum(m["reference_count"] for m in records)
    text = f"""# Anchor proposals

This is a curated set of **{len(records)} real, published research proposals**, containing
**{total} source reference entries**. {funded} have affirmative funding evidence; the other
{len(records) - funded} have unknown award status. All meet the published-proposal inclusion route.
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

Snapshot retrieved {SNAPSHOT_DATE}. Include a real, full published proposal narrative under
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

{chr(10).join(rows)}

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

"""
    text += "\n".join(f"- [{name}]({url}): {reason}" for name, url, reason in REJECTED)
    text += "\n\nAdditional JATS candidates screened but not selected (not licence rejections):\n\n"
    text += "\n".join(
        f"- [RIO {n}](https://riojournal.com/article/{n}/): {reason}."
        for n, reason in SCREENED_NOT_SELECTED
    )
    text += "\n\n## Attribution and document-level licence evidence\n\n"
    text += "\n\n".join(attribution(m) for m in records)
    text += (
        "\n\nEach `anchor.yaml` contains a `licence_evidence` object with the "
        "exact source URL,\nmetadata location, value and source digest. For RIO "
        "this is the article-specific\n`front/article-meta/permissions/license/@"
        "xlink:href`; for Zenodo it is\n`metadata.license.id`, tied to the "
        "exact PDF filename and repository checksum.\n"
    )
    return text


def write_attribution(records: list[dict]) -> None:
    path = ROOT / "data" / "ATTRIBUTION.md"
    before = path.read_text(encoding="utf-8")
    start = "<!-- proposalbench-anchors:start -->"
    end = "<!-- proposalbench-anchors:end -->"
    content = (
        start + "\n## Anchor proposals\n\n"
        "These published proposals are calibration anchors, not synthetic tasks. "
        "See [anchors/README.md](anchors/README.md) for purposes, licence "
        "evidence and limitations.\n\n"
        + "\n\n".join(
            attribution(m).replace(f"]({m['id']}/anchor.yaml)", f"](anchors/{m['id']}/anchor.yaml)")
            for m in records
        )
        + "\n"
        + end
    )
    if start in before:
        left, rest = before.split(start, 1)
        _, right = rest.split(end, 1)
        after = left + content + right
    else:
        after = before.rstrip() + "\n\n" + content + "\n"
    path.write_text(after, encoding="utf-8")


def handoff(records: list[dict]) -> str:
    text = "# ProposalBench anchor handoff\n\n"
    text += (
        f"Retrieved {SNAPSHOT_DATE}; {len(records)} anchors, "
        f"{sum(m['words'] for m in records):,} counted body words, "
        f"{sum(m['reference_count'] for m in records)} source references. No commit created.\n\n"
    )
    text += (
        "All 10 RIO items are published Grant Proposals; one Spanish Zenodo "
        "item is a published doctoral research proposal. "
    )
    text += (
        f"Funding is affirmative for {sum(m['funded'] is True for m in records)} items "
        "and unknown for the remainder. "
        "No unknown outcome was relabelled as funded or rejected.\n\n"
    )
    text += (
        "Sources searched and the complete rejection/selection log are in "
        "[data/anchors/README.md](../data/anchors/README.md). Raw downloaded "
        "XML, PDF, catalogue metadata, browse pages and extraction previews "
        "are in gitignored seeds_raw/anchors/. The collector pins the selected "
        "document bytes and validates each licence on conversion.\n\n"
    )
    text += "## Per-anchor checks and licence evidence\n\n"
    for m in records:
        e = m["licence_evidence"]
        text += (
            f"- **{m['id']}**: {m['words']} words; {m['reference_count']} parsed references = "
            f"{m['source_reference_count']} source entries. [Licence evidence]({e['url']}): "
            f"`{e['location']}` = `{e['value']}`. Markdown SHA-256 `{m['sha256']}`.\n"
        )
    text += "\n## Conversion and validation\n\n"
    text += (
        "Ran the project proposal and reference parsers on every output; final "
        "References headings found, source/parsed counts agree, body counts "
        "and SHA-256 values agree with YAML. Privacy identifier scans pass; "
        "retained narrative reviewed. Full raw provenance, author names, "
        "funding evidence and conversion notes are in each anchor.yaml.\n\n"
    )
    text += (
        "JATS figures, grouped panels and table captions retained; tables "
        "preserve text. Duplicated publisher back notes emitted once. "
        "Scientific prose and source reference defects are preserved. No "
        "external bibliography enrichment was performed. Spanish PDF equations "
        "and algorithm were checked against rendered pages; 60 source "
        "author-year reference starts were counted independently, including "
        "entries adjacent to page breaks. Its 9 figures and shaded timetable "
        "are represented by captions. Source typos and inconsistent equations "
        "were not repaired.\n\n"
    )
    text += (
        "Reproduction: `uv run python tools/authoring/collect_anchors.py "
        "--offline`; verification: `uv run python "
        "tools/authoring/collect_anchors.py --check`. Poppler pdftotext "
        "24.02.0 is required for the PDF. See README for the collection "
        "command that downloads uncached sources.\n\n"
    )
    text += (
        "Remaining limits: this is an English/RIO-heavy convenience sample; "
        "only one Spanish item. Published versions are not necessarily "
        "original submitted forms. No reference-checker FPR, EV1 threshold or "
        "call-conditioned admissibility score has been calculated; the "
        "collector does not change scoring. Source spelling, metadata errors "
        "and conversion layout effects remain relevant to downstream "
        "calibration.\n"
    )
    text += "\n## Rejected documents\n\n"
    text += "\n".join(f"- [{name}]({url}): {reason}" for name, url, reason in REJECTED)
    text += (
        "\n\nThe README also lists ten screened JATS candidates left out "
        "for size, privacy or topic concentration.\n\n"
        "Final verification included fresh downloads of every selected XML/PDF, "
        "byte-for-byte Markdown reproduction, a second offline run with no output "
        "changes, Ruff, and the requested `uv run python -c` parser checks. "
        "All source JATS body paragraphs are checked for retention by the collector.\n"
    )
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use only cached downloads")
    parser.add_argument(
        "--check", action="store_true", help="Validate existing anchors without writing"
    )
    args = parser.parse_args()
    if args.check:
        paths = sorted(OUT.glob("*/anchor.yaml"))
        if len(paths) != len(RIO) + 1:
            raise ValueError("Unexpected anchor set size")
        for path in paths:
            metadata = yaml.safe_load(path.read_text())
            validate(path.with_name("proposal.md").read_text(), metadata, stored=True)
            print(
                f"{metadata['id']}: {metadata['words']} words, "
                f"{metadata['reference_count']} references; OK"
            )
        return
    RAW.mkdir(parents=True, exist_ok=True)
    outputs = [rio_anchor(spec, args.offline) for spec in RIO]
    outputs.append(zenodo_anchor(args.offline))
    # Validate the complete collection before writing any public outputs.
    for text, metadata in outputs:
        validate(text, metadata)
    records = []
    for text, metadata in outputs:
        path = OUT / metadata["id"]
        path.mkdir(parents=True, exist_ok=True)
        (path / "proposal.md").write_text(text, encoding="utf-8")
        (path / "anchor.yaml").write_text(
            yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8",
        )
        records.append(metadata)
        print(
            f"{metadata['id']}: {metadata['words']} words, {metadata['reference_count']} references"
        )
    (OUT / "README.md").write_text(readme(records), encoding="utf-8")
    write_attribution(records)
    handoff_path = ROOT / ".codex-handoff" / "anchors.md"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(handoff(records), encoding="utf-8")


if __name__ == "__main__":
    main()
