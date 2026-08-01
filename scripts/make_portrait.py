"""Push a photo through a character ramp to produce ascii.svg.

Run this locally whenever the source photo changes; the result is committed.
The daily action does not run it, because the output only changes when the
photo does.

    python scripts/make_portrait.py                 # picks a photo out of assets/
    python scripts/make_portrait.py path/to/pic.png
    python scripts/make_portrait.py --invert        # override the polarity guess

With no photo on disk it falls back to a stacked-initials monogram drawn
through the same ramp, so the page never renders a broken image.

Density has to mean "the subject", not "the bright half of the frame". Which
end of the ramp does that depends on the picture: a dark figure against a pale
wall needs shadows dense, a lit face against a dark backdrop needs highlights
dense. The polarity is measured off the image rather than assumed, and one
mapping then serves both GitHub themes — the ink colour flips with the theme,
so the subject stays drawn either way.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps, ImageStat

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import svgdoc, typeface

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "ascii.svg"
SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

WIDTH = 460
COLUMNS = 104
ASPECT = (4, 5)
"""Every photo is centre-cropped to this, so the page layout never shifts."""

RAMP = " " + svgdoc.RAMP
LINE_HEIGHT = 1.0
"""In em. With a 0.600 em advance this makes each cell a 0.6:1 rectangle."""


def find_photo() -> Path | None:
    """A file called portrait.* wins; failing that, whatever image assets/ holds."""
    if not ASSETS.is_dir():
        return None
    named = sorted(path for path in ASSETS.glob("portrait.*") if path.suffix.lower() in SUFFIXES)
    if named:
        return named[0]
    images = sorted(path for path in ASSETS.iterdir() if path.suffix.lower() in SUFFIXES)
    return images[0] if images else None


def crop_to_aspect(image: Image.Image, aspect: tuple[int, int]) -> Image.Image:
    target = aspect[0] / aspect[1]
    width, height = image.size
    if width / height > target:
        keep = round(height * target)
        left = (width - keep) // 2
        return image.crop((left, 0, left + keep, height))
    keep = round(width / target)
    top = (height - keep) // 3  # bias upward: faces sit above centre
    return image.crop((0, top, width, top + keep))


def subject_is_dark(image: Image.Image) -> bool:
    """Is the middle of the frame darker than the edges around it?

    The bottom edge is left out of the comparison: a subject usually runs off
    the bottom of a portrait, so that strip is rarely background.
    """
    grey = image.convert("L")
    width, height = grey.size
    strip = max(4, width // 10)

    def mean(region: Image.Image) -> float:
        return ImageStat.Stat(region).mean[0]

    centre = mean(grey.crop((width // 4, height // 6, width * 3 // 4, height * 5 // 6)))
    edges = [
        grey.crop((0, 0, strip, height)),
        grey.crop((width - strip, 0, width, height)),
        grey.crop((0, 0, width, strip)),
    ]
    return centre < sum(mean(edge) for edge in edges) / len(edges)


def monogram(initials: str = "EKA") -> Image.Image:
    """Stacked initials, drawn in the page's own typeface."""
    width, height = 800, 1000
    image = Image.new("L", (width, height), 255)  # dark letters on a light field
    font = ImageFont.truetype(str(typeface.FONT_DIR / "JetBrainsMono-Bold.ttf"), 400)

    # A monospace glyph is only 0.6 em wide, so stacked initials left to their
    # natural proportions read as a thin ribbon. Each is cropped to its own ink
    # and stretched to fill its band instead.
    band = height // len(initials)
    target = (round(width * 0.80), round(band * 0.74))

    for index, letter in enumerate(initials):
        tile = Image.new("L", (600, 800), 255)
        ImageDraw.Draw(tile).text((300, 400), letter, font=font, fill=0, anchor="mm")
        glyph = tile.crop(ImageOps.invert(tile).getbbox()).resize(target, Image.LANCZOS)
        image.paste(glyph, ((width - target[0]) // 2, index * band + (band - target[1]) // 2))
    return image


def to_cells(image: Image.Image, columns: int) -> list[list[int]]:
    """Resample to a character grid and return per-cell luminance, 0-255."""
    image = ImageOps.autocontrast(image.convert("L"), cutoff=2)
    image = ImageEnhance.Sharpness(image).enhance(1.6)

    width, height = image.size
    rows = max(1, round(height / width * columns * typeface.ADVANCE / LINE_HEIGHT))
    resized = image.resize((columns, rows), Image.LANCZOS)
    pixels = resized.tobytes()  # one byte per pixel in "L" mode
    return [list(pixels[row * columns : (row + 1) * columns]) for row in range(rows)]


def to_rows(cells: list[list[int]], *, dense_when_bright: bool) -> list[str]:
    steps = len(RAMP) - 1
    rows = []
    for row in cells:
        rows.append(
            "".join(
                RAMP[round((value if dense_when_bright else 255 - value) / 255 * steps)]
                for value in row
            )
        )
    return rows


def render(cells: list[list[int]], *, dense_when_bright: bool = False) -> str:
    size = WIDTH / (COLUMNS * typeface.ADVANCE)
    line = size * LINE_HEIGHT
    height = round(len(cells) * line)
    rows = to_rows(cells, dense_when_bright=dense_when_bright)

    body = f"<style>text{{font-size:{size:.3f}px}}</style>" + "".join(
        f'<text x="0" y="{(index + 0.82) * line:.2f}">'
        f"{svgdoc.escape(row)}"
        f"{svgdoc.fade_in(0.02 * index, 0.5)}</text>"
        for index, row in enumerate(rows)
    )

    return svgdoc.document(
        WIDTH,
        height,
        body,
        title="Eduard King Anterola",
        chars=RAMP,
        weights=("regular",),
    )


def main() -> None:
    arguments = [value for value in sys.argv[1:] if not value.startswith("-")]
    override = "--invert" in sys.argv

    photo = Path(arguments[0]) if arguments else find_photo()

    if photo and photo.exists():
        source = crop_to_aspect(Image.open(photo), ASPECT)
        origin = photo.relative_to(ROOT) if photo.is_relative_to(ROOT) else photo
    else:
        source = monogram()
        origin = f"monogram placeholder (drop a photo in {ASSETS.relative_to(ROOT)} to replace)"

    dense_when_bright = not subject_is_dark(source)
    if override:
        dense_when_bright = not dense_when_bright

    OUTPUT.write_text(
        render(to_cells(source, COLUMNS), dense_when_bright=dense_when_bright), encoding="utf8"
    )
    ink = "highlights" if dense_when_bright else "shadows"
    print(f"wrote {OUTPUT.relative_to(ROOT)} from {origin} (ink follows {ink})")


if __name__ == "__main__":
    main()
