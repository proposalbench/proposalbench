"""Export the system-facing input bundle of a task.

Every system receives exactly these files and nothing else: ``call.md``, the dossier
Markdown files, the optional ``brief.md`` and ``instructions.md``. The YAML answer keys
never leave the repository.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from proposalbench.tasks.loader import ResolvedTask

LANGUAGE_NAMES = {"en": "English", "es": "Spanish", "de": "German", "fr": "French"}

INSTRUCTIONS_TEMPLATE = """\
# Instructions

Prepare the complete proposal for the funding call in `call.md`, on behalf of the applicant \
described in the files under `dossier/`.{brief_clause}

Deliver one Markdown document that contains the full proposal text the call asks applicants \
to write.

1. Follow the structure, required sections and evaluation criteria set out in the call.
2. Write in {language}.
3. The counted text must not exceed {max_words} words. The call's length note says what is \
counted.
4. End with a section headed "References" (or its equivalent in {language}) that lists every \
work cited in the text. Any consistent citation style is acceptable.
5. State only facts about the applicant, team, partners, prior results and resources that \
appear in the provided files. Where the proposal needs information that is not provided, \
insert a clearly marked placeholder such as `[[TO COMPLETE: number of PhD students \
supervised]]` instead of inventing it.
6. Output only the proposal document.
"""


def render_instructions(rt: ResolvedTask) -> str:
    brief_clause = (
        " The applicant's own notes on what they want to propose are in `brief.md`."
        if rt.brief_text
        else ""
    )
    return INSTRUCTIONS_TEMPLATE.format(
        brief_clause=brief_clause,
        language=LANGUAGE_NAMES.get(rt.call.language, rt.call.language),
        max_words=f"{rt.call.length_contract.max_words:,}",
    )


def export_bundle(rt: ResolvedTask, out_dir: Path) -> list[Path]:
    """Write the system-facing files of ``rt`` into ``out_dir`` and return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = [out_dir / "call.md", out_dir / "instructions.md"]
    shutil.copyfile(rt.call_dir / "call.md", written[0])
    written[1].write_text(render_instructions(rt), encoding="utf-8")
    for f in rt.dossier.files:
        dest = out_dir / "dossier" / f.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rt.dossier_dir / f.path, dest)
        written.append(dest)
    if rt.brief_text:
        dest = out_dir / "brief.md"
        dest.write_text(rt.brief_text, encoding="utf-8")
        written.append(dest)
    return written
