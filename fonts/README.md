# Fonts

Bundled so the journal looks the same on every machine.

| Family | Use | Licence |
| --- | --- | --- |
| Playfair Display | display serif (dates, titles) | SIL OFL 1.1 — `OFL-playfairdisplay.txt` |
| Outfit | body sans | SIL OFL 1.1 — `OFL-outfit.txt` |
| DM Mono | metadata, folios, labels | SIL OFL 1.1 — `OFL-dmmono.txt` |
| Caveat | handwritten margin notes | SIL OFL 1.1 — `OFL-caveat.txt` |

All four are SIL Open Font License 1.1, which permits redistribution
provided the licence travels with the files. Upstream:
<https://github.com/google/fonts>

`./install.sh` copies these into your user font directory and refreshes
the font cache. Without them the app still runs, but falls back to a
plain bitmap font and loses the whole typographic character — it warns
on startup when that happens.
