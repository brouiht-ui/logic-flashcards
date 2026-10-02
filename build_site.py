"""Builds index.html from site.template.html with the card data from make_flashcards.py."""
import json
import os

import make_flashcards as m

here = os.path.dirname(os.path.abspath(__file__))
data = {
    "sets": m.SET_NAMES,
    "cards": [dict(set=c[0], q=c[1], title=c[2], a=c[3], check=c[4]) for c in m.CARDS],
}
with open(os.path.join(here, "site.template.html"), encoding="utf-8") as f:
    html = f.read().replace("__DATA__", json.dumps(data, ensure_ascii=False))
with open(os.path.join(here, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("wrote index.html")
