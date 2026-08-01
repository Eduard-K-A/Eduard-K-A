"""Draw the section headings.

GitHub strips CSS from READMEs, so an image is the only way to set a heading in
this page's own typeface. Each heading is a label plus a rule that draws itself
across the remaining width.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import svgdoc, typeface

ROOT = Path(__file__).resolve().parent.parent

WIDTH = 620
HEIGHT = 30
SIZE = 13
BASELINE = 19
GAP = 12

SECTIONS = ["about", "stack", "projects", "stats", "about this page"]


def render(label: str) -> str:
    label_width = typeface.width(label, SIZE)
    rule_x = label_width + GAP
    rule_length = WIDTH - rule_x

    return svgdoc.document(
        WIDTH,
        HEIGHT,
        f'<text x="0" y="{BASELINE}" class="b accent" font-size="{SIZE}">'
        f"{svgdoc.escape(label)}</text>"
        f'<rect x="{rule_x}" y="{BASELINE - 4}" height="1" width="{rule_length}" '
        'fill="var(--faint)">'
        f'<animate attributeName="width" from="0" to="{rule_length}" '
        'dur="0.7s" begin="0.1s" fill="freeze"/>'
        "</rect>",
        title=label,
        chars=label,
        weights=("bold",),
    )


def slug(label: str) -> str:
    return label.replace(" ", "-")


def main() -> None:
    for label in SECTIONS:
        path = ROOT / f"hd-{slug(label)}.svg"
        path.write_text(render(label), encoding="utf8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
