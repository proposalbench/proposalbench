# Lexicon provenance

| File | Source | Licence | Use |
|---|---|---|---|
| `kobak_excess_words.csv` | Kobak, D., González-Márquez, R., Horvát, E.-Á., Lause, J. (2025). Delving into LLM-assisted writing in biomedical publications through excess vocabulary. *Science Advances*. Data from https://github.com/berenslab/llm-excess-vocab (`results/excess_words.csv`), retrieved 2026-10-30, unchanged except the dropped index column. | MIT (`LICENSE-kobak-excess-words`) | Rows typed `style` give the English excess-style-word rate (diagnostic). |
| `grant_buzzwords_en.txt`, `grant_buzzwords_es.txt` | Curated by the ProposalBench maintainers from the words flagged in grant-writing guidance and in Proposia's own writing rules. | CC BY 4.0 | Buzzword rate (diagnostic). |

Considered and not used: the slop-forensics essay lists (Paech, MIT,
https://github.com/sam-paech/slop-forensics). In the essay domain they are dominated by topic
words (e.g. names and subject terms), which would measure subject matter rather than style in
research proposals.
