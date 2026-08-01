"""Shared chrome for every graphic on the profile page.

One palette, one type scale, one document wrapper. Colours are declared as CSS
custom properties with a `prefers-color-scheme` override so a single file reads
correctly against both GitHub themes — GitHub renders these through <img>, so
the SVG is its own document and picks up the viewer's colour scheme directly.
"""

from __future__ import annotations

from . import typeface

PALETTE = {
    #  name       light      dark
    "ink": ("#1f2328", "#e6edf3"),
    "dim": ("#59636e", "#8b949e"),
    "faint": ("#d8dee4", "#2b3138"),
    "accent": ("#1a7f37", "#3fb950"),
}

RAMP = ":+#@"
"""Quiet to loud. Shared by the portrait and the contribution year."""


def _variables(index: int) -> str:
    return "".join(f"--{name}:{values[index]};" for name, values in PALETTE.items())


def stylesheet(chars: str, weights: tuple[str, ...] = ("regular", "bold")) -> str:
    return (
        typeface.font_face(chars, weights)
        + f":root{{{_variables(0)}}}"
        + f"@media (prefers-color-scheme:dark){{:root{{{_variables(1)}}}}}"
        + f"text{{font-family:'{typeface.FAMILY}',ui-monospace,monospace;"
        "white-space:pre;fill:var(--ink)}"
        ".dim{fill:var(--dim)}"
        ".faint{fill:var(--faint)}"
        ".accent{fill:var(--accent)}"
        ".b{font-weight:700}"
    )


def escape(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fade_in(delay: float, duration: float = 0.45) -> str:
    """SMIL opacity fade. GitHub strips <script>, so animation has to be declarative.

    Attach this to an element left at its *final* opacity. A browser that never
    starts the timeline — which is what happens to an <img> still below the fold
    — falls back to the static attribute, so the content is visible either way.
    Animating away from a static `opacity="0"` would leave it blank instead.
    """
    return (
        f'<animate attributeName="opacity" from="0" to="1" '
        f'dur="{duration}s" begin="{delay:.2f}s" fill="freeze"/>'
    )


def document(
    width: int,
    height: int,
    body: str,
    *,
    title: str,
    chars: str,
    weights: tuple[str, ...] = ("regular", "bold"),
) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>"
        f"<style>{stylesheet(chars, weights)}</style>"
        f"{body}"
        "</svg>\n"
    )
