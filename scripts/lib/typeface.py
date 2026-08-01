"""Inline JetBrains Mono, subset to the characters a graphic actually draws.

GitHub strips <link> tags and external CSS out of README-embedded SVG, so the
only way to guarantee this page's typeface is to carry the font inside each
file. Subsetting keeps that payload at a few kilobytes instead of 270 of them.

It is not only a matter of looks: every graphic here lays glyphs out by hand on
the assumption that one character advances exactly 0.600 em. A viewer whose
default monospace is narrower would see the portrait squeezed.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
FACES = {"regular": ("JetBrainsMono-Regular.ttf", 400), "bold": ("JetBrainsMono-Bold.ttf", 700)}

FAMILY = "JBM"
ADVANCE = 0.600
"""Advance width of one glyph, in em. Verified against the shipped TTF."""


def width(text: str, size: float) -> float:
    """Rendered width of `text` at `size` px, in px."""
    return len(text) * size * ADVANCE


def _normalise(chars: str) -> str:
    return "".join(sorted(set(chars) | {" "}))


@lru_cache(maxsize=None)
def _encode(weight: str, chars: str) -> str:
    filename, _ = FACES[weight]
    font = TTFont(FONT_DIR / filename)

    options = Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.layout_features = []  # coding ligatures would break the glyph grid
    options.notdef_outline = False
    options.drop_tables += ["GSUB", "GPOS"]

    subsetter = Subsetter(options=options)
    subsetter.populate(text=chars)
    subsetter.subset(font)

    buffer = BytesIO()
    font.save(buffer)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def font_face(chars: str, weights: tuple[str, ...] = ("regular", "bold")) -> str:
    """A @font-face block per weight, each subset to `chars` and base64 inlined."""
    normalised = _normalise(chars)
    blocks = []
    for weight in weights:
        _, css_weight = FACES[weight]
        payload = _encode(weight, normalised)
        blocks.append(
            f"@font-face{{font-family:'{FAMILY}';font-style:normal;"
            f"font-weight:{css_weight};"
            f"src:url(data:font/woff2;base64,{payload}) format('woff2')}}"
        )
    return "".join(blocks)
