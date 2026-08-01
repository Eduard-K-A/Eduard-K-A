"""Unit tests for the profile generators.

    python -m unittest discover -s scripts -p 'test_*.py'

Everything here runs offline; the network paths are exercised by the workflow.
"""

from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_headings
import make_portrait
import make_stats
from lib import svgdoc, typeface


def calendar(pairs: dict[str, int]) -> dict[str, int]:
    return pairs


class Streaks(unittest.TestCase):
    today = date(2026, 8, 2)

    def test_counts_a_run_ending_today(self):
        days = {(self.today - timedelta(days=n)).isoformat(): 3 for n in range(5)}
        self.assertEqual(make_stats.streaks(days, self.today)["current"], 5)

    def test_today_being_empty_does_not_break_the_streak(self):
        days = {(self.today - timedelta(days=n)).isoformat(): 3 for n in range(1, 5)}
        days[self.today.isoformat()] = 0
        self.assertEqual(make_stats.streaks(days, self.today)["current"], 4)

    def test_two_empty_days_do_break_it(self):
        days = {(self.today - timedelta(days=n)).isoformat(): 3 for n in range(2, 6)}
        self.assertEqual(make_stats.streaks(days, self.today)["current"], 0)

    def test_longest_ignores_gaps(self):
        days = {}
        for offset in list(range(20, 27)) + list(range(2, 5)):
            days[(self.today - timedelta(days=offset)).isoformat()] = 1
        result = make_stats.streaks(days, self.today)
        self.assertEqual(result["longest"], 7)
        self.assertEqual(result["active"], 10)

    def test_empty_history(self):
        self.assertEqual(
            make_stats.streaks({}, self.today), {"current": 0, "longest": 0, "active": 0}
        )


class LanguageShare(unittest.TestCase):
    def test_folds_the_tail_into_other(self):
        totals = {name: 10 for name in "abcdefghij"}
        rows = make_stats.share(totals, limit=6)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[-1][0], "other")
        self.assertAlmostEqual(rows[-1][1], 0.4)

    def test_fractions_sum_to_one(self):
        rows = make_stats.share({"a": 3, "b": 1}, limit=6)
        self.assertAlmostEqual(sum(fraction for _, fraction in rows), 1.0)

    def test_no_other_segment_when_nothing_is_left_over(self):
        rows = make_stats.share({"a": 1, "b": 1}, limit=6)
        self.assertEqual([name for name, _ in rows], ["a", "b"])

    def test_empty(self):
        self.assertEqual(make_stats.share({}), [])

    def test_aggregates_bytes_and_repos_separately(self):
        repositories = [
            {
                "primaryLanguage": {"name": "Python", "color": "#3572A5"},
                "languages": {"edges": [{"size": 900, "node": {"name": "Python", "color": "#3572A5"}}]},
            },
            {
                "primaryLanguage": {"name": "Python", "color": "#3572A5"},
                "languages": {
                    "edges": [
                        {"size": 100, "node": {"name": "Python", "color": "#3572A5"}},
                        {"size": 400, "node": {"name": "CSS", "color": "#663399"}},
                    ]
                },
            },
        ]
        stats = make_stats.languages(repositories)
        self.assertEqual(stats["bytes"], {"Python": 1000, "CSS": 400})
        self.assertEqual(stats["repos"], {"Python": 2})
        self.assertEqual(stats["colors"]["CSS"], "#663399")


class Ramp(unittest.TestCase):
    def test_zero_is_always_level_zero(self):
        self.assertEqual(make_stats.level(0, [1, 4, 9]), 0)

    def test_levels_climb_with_the_cut_offs(self):
        cuts = [1, 4, 9]
        self.assertEqual([make_stats.level(n, cuts) for n in (1, 3, 6, 20)], [1, 2, 3, 4])

    def test_thresholds_adapt_to_the_account(self):
        self.assertEqual(len(make_stats.thresholds([0, 0, 1, 2, 3, 4, 5, 6, 7, 8])), 3)

    def test_thresholds_survive_a_silent_year(self):
        self.assertEqual(make_stats.level(0, make_stats.thresholds([0, 0, 0])), 0)


class Window(unittest.TestCase):
    def test_covers_exactly_a_year(self):
        entries = make_stats.window({}, date(2026, 8, 2))
        self.assertEqual(len(entries), 365)
        self.assertEqual(entries[-1][0], date(2026, 8, 2))

    def test_missing_days_read_as_zero(self):
        entries = make_stats.window({"2026-08-02": 4}, date(2026, 8, 2))
        self.assertEqual(entries[-1][1], 4)
        self.assertEqual(entries[0][1], 0)


class Rendering(unittest.TestCase):
    """The graphics must be well-formed and self-contained, whatever the data."""

    today = date(2026, 8, 2)

    def documents(self):
        data = make_stats.synthetic(self.today)
        return {
            "stats": make_stats.render_stats(data, self.today),
            "streak": make_stats.render_streak(data, self.today),
            "langs": make_stats.render_languages(data),
            "year": make_stats.render_year(data, self.today),
            "heading": make_headings.render("about"),
        }

    def test_every_graphic_is_parseable_xml(self):
        from xml.etree import ElementTree

        for name, markup in self.documents().items():
            with self.subTest(name=name):
                ElementTree.fromstring(markup)

    def test_nothing_loads_from_a_third_party(self):
        for name, markup in self.documents().items():
            with self.subTest(name=name):
                # The SVG namespace is an identifier, not a fetch.
                body = markup.replace('xmlns="http://www.w3.org/2000/svg"', "")
                self.assertNotIn("http://", body)
                self.assertNotIn("https://", body)

    def test_the_typeface_is_inlined(self):
        for name, markup in self.documents().items():
            with self.subTest(name=name):
                self.assertIn("@font-face", markup)
                self.assertIn("data:font/woff2;base64,", markup)

    def test_content_does_not_depend_on_the_animation_running(self):
        """An <img> below the fold may never start its SMIL timeline.

        Every animated element therefore has to sit at its finished value
        statically, so a browser that skips the timeline still shows the data.
        """
        documents = dict(self.documents(), portrait=make_portrait.render([[0, 90, 200]]))
        for name, markup in documents.items():
            with self.subTest(name=name):
                self.assertNotIn('opacity="0"', markup)
                self.assertNotIn('width="0"', markup)

    def test_language_graphic_survives_an_empty_account(self):
        empty = {"profile": {"repositories": {"nodes": []}}}
        self.assertIn("no public repositories yet", make_stats.render_languages(empty))

    def test_headings_carry_their_label(self):
        self.assertIn(">projects<", make_headings.render("projects"))


class Portrait(unittest.TestCase):
    cells = [[0, 128, 255], [255, 128, 0]]

    def test_dark_pixels_are_dense_when_ink_follows_shadow(self):
        rows = make_portrait.to_rows(self.cells, dense_when_bright=False)
        self.assertEqual(rows[0][0], "@")
        self.assertEqual(rows[0][-1], " ")

    def test_the_mapping_inverts_for_the_dark_theme(self):
        rows = make_portrait.to_rows(self.cells, dense_when_bright=True)
        self.assertEqual(rows[0][0], " ")
        self.assertEqual(rows[0][-1], "@")

    def test_a_dark_subject_on_a_pale_background_is_detected(self):
        from PIL import Image, ImageDraw

        image = Image.new("L", (200, 250), 235)
        ImageDraw.Draw(image).ellipse((60, 60, 140, 190), fill=30)
        self.assertTrue(make_portrait.subject_is_dark(image))

    def test_a_lit_subject_on_a_dark_background_is_detected(self):
        from PIL import Image, ImageDraw

        image = Image.new("L", (200, 250), 20)
        ImageDraw.Draw(image).ellipse((60, 60, 140, 190), fill=225)
        self.assertFalse(make_portrait.subject_is_dark(image))

    def test_the_grid_keeps_the_declared_advance(self):
        self.assertEqual(typeface.ADVANCE, 0.600)
        self.assertAlmostEqual(typeface.width("abcd", 10), 24.0)

    def test_cropping_reaches_the_target_aspect(self):
        from PIL import Image

        cropped = make_portrait.crop_to_aspect(Image.new("L", (1000, 400)), (4, 5))
        self.assertAlmostEqual(cropped.width / cropped.height, 0.8, places=2)


class Escaping(unittest.TestCase):
    def test_markup_characters_cannot_escape_a_label(self):
        self.assertEqual(svgdoc.escape('<a href="x">&'), "&lt;a href=&quot;x&quot;&gt;&amp;")


if __name__ == "__main__":
    unittest.main()
