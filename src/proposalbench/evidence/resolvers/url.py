from __future__ import annotations

from html.parser import HTMLParser

from proposalbench.evidence.cache import safe_url
from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.records import WorkRecord


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.inside = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self.inside = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.inside = False

    def handle_data(self, data: str) -> None:
        if self.inside:
            self.parts.append(data)


def resolve_url(url: str, client: EvidenceClient) -> list[WorkRecord]:
    # A weak signal at the end of the cascade: one attempt, so dead hosts cannot stall a run.
    response = client.request(
        "GET", url, source="url", timeout=10, follow_redirects=True, retries=0
    )
    if response.status_code >= 500 or response.status_code == 429:
        response.raise_for_status()
    final_url = safe_url(str(response.url))
    parser = _TitleParser()
    if response.is_success:
        parser.feed(response.text)
    return [
        WorkRecord(
            "url",
            final_url,
            title=" ".join("".join(parser.parts).split()) or None,
            kind="web",
            url=final_url,
            raw_ref={"url": final_url, "status": response.status_code},
        )
    ]
