"""Draw the stat graphics straight from the GitHub GraphQL API.

Nothing here is embedded from a third party, so nothing here can rate-limit or
go dark. Run daily by .github/workflows/stats.yml, which commits only the files
that actually changed.

    GITHUB_TOKEN=... python scripts/make_stats.py
    python scripts/make_stats.py --offline   # synthetic data, no network

Language totals cover public, non-fork repositories only.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import svgdoc, typeface

ROOT = Path(__file__).resolve().parent.parent
USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER") or "Eduard-K-A"
API = "https://api.github.com/graphql"

WIDTH = 620
WINDOW = 365
TOP_LANGUAGES = 6

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


# --------------------------------------------------------------------------- api


def query(token: str, document: str, variables: dict) -> dict:
    request = urllib.request.Request(
        API,
        data=json.dumps({"query": document, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{USERNAME}-profile",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read())

    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
    if not payload.get("data", {}).get("user"):
        raise RuntimeError(f"no such user: {variables.get('login')}")
    return payload["data"]["user"]


PROFILE_QUERY = """
query Profile($login: String!) {
  user(login: $login) {
    login
    createdAt
    followers { totalCount }
    repositories(
      first: 100
      privacy: PUBLIC
      ownerAffiliations: OWNER
      isFork: false
      orderBy: { field: PUSHED_AT, direction: DESC }
    ) {
      totalCount
      nodes {
        name
        stargazerCount
        primaryLanguage { name color }
        languages(first: 12, orderBy: { field: SIZE, direction: DESC }) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def calendar_query(years: list[int]) -> str:
    fields = "\n".join(
        f'    y{year}: contributionsCollection(from: $from{year}, to: $to{year}) {{'
        "      contributionCalendar { weeks { contributionDays { date contributionCount } } }"
        "    }"
        for year in years
    )
    arguments = " ".join(f"$from{year}: DateTime!, $to{year}: DateTime!" for year in years)
    return f"query Calendar($login: String!, {arguments}) {{\n  user(login: $login) {{\n{fields}\n  }}\n}}"


def fetch(token: str, username: str, today: date) -> dict:
    profile = query(token, PROFILE_QUERY, {"login": username})
    created = datetime.fromisoformat(profile["createdAt"].replace("Z", "+00:00")).date()

    years = list(range(created.year, today.year + 1))
    variables: dict = {"login": username}
    for year in years:
        start = max(created, date(year, 1, 1))
        end = min(today, date(year, 12, 31))
        variables[f"from{year}"] = f"{start.isoformat()}T00:00:00Z"
        variables[f"to{year}"] = f"{end.isoformat()}T23:59:59Z"

    calendars = query(token, calendar_query(years), variables)

    days: dict[str, int] = {}
    for year in years:
        for week in calendars[f"y{year}"]["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                days[day["date"]] = day["contributionCount"]

    return {"profile": profile, "days": days}


def synthetic(today: date) -> dict:
    """Deterministic stand-in so the graphics can be rendered without a token."""
    days = {}
    for offset in range(600):
        moment = today - timedelta(days=offset)
        seed = (moment.toordinal() * 7919) % 100
        days[moment.isoformat()] = 0 if seed < 32 else seed % 14
    return {
        "profile": {
            "login": USERNAME,
            "followers": {"totalCount": 0},
            "repositories": {"totalCount": 0, "nodes": []},
        },
        "days": days,
    }


# ------------------------------------------------------------------------ derive


def window(days: dict[str, int], today: date, length: int = WINDOW) -> list[tuple[date, int]]:
    start = today - timedelta(days=length - 1)
    return [
        (start + timedelta(days=offset), days.get((start + timedelta(days=offset)).isoformat(), 0))
        for offset in range((today - start).days + 1)
    ]


def streaks(days: dict[str, int], today: date) -> dict:
    active = sorted(moment for moment, count in days.items() if count > 0)

    longest = run = 0
    previous: date | None = None
    for entry in active:
        moment = date.fromisoformat(entry)
        run = run + 1 if previous and (moment - previous).days == 1 else 1
        longest = max(longest, run)
        previous = moment

    cursor = today
    if not days.get(today.isoformat()):
        cursor -= timedelta(days=1)  # today is still in progress; don't break the streak
    current = 0
    while days.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    return {"current": current, "longest": max(longest, current), "active": len(active)}


def languages(repositories: list[dict]) -> dict:
    by_bytes: dict[str, int] = {}
    by_repo: dict[str, int] = {}
    colors: dict[str, str] = {}

    for repository in repositories:
        for edge in repository.get("languages", {}).get("edges") or []:
            name = edge["node"]["name"]
            by_bytes[name] = by_bytes.get(name, 0) + edge["size"]
            colors.setdefault(name, edge["node"].get("color") or "#8b949e")
        primary = repository.get("primaryLanguage")
        if primary:
            by_repo[primary["name"]] = by_repo.get(primary["name"], 0) + 1
            colors.setdefault(primary["name"], primary.get("color") or "#8b949e")

    return {"bytes": by_bytes, "repos": by_repo, "colors": colors}


def share(totals: dict[str, int], limit: int = TOP_LANGUAGES) -> list[tuple[str, float]]:
    """Top `limit` languages as fractions, with the tail folded into `other`."""
    total = sum(totals.values())
    if not total:
        return []

    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    head = ranked[:limit]
    result = [(name, amount / total) for name, amount in head]
    tail = sum(amount for _, amount in ranked[limit:])
    if tail:
        result.append(("other", tail / total))
    return result


def thresholds(counts: list[int]) -> list[int]:
    """Quartile cut-offs over active days, so the ramp adapts to the account."""
    active = sorted(count for count in counts if count > 0)
    if not active:
        return [1, 2, 3]
    return [active[int(len(active) * fraction)] for fraction in (0.25, 0.5, 0.75)]


def level(count: int, cuts: list[int]) -> int:
    if count <= 0:
        return 0
    return 1 + sum(1 for cut in cuts if count > cut)


# ------------------------------------------------------------------------ render


def cells(entries: list[tuple[str, str]], *, width: int, size: int, top: int) -> str:
    """A row of big-number/small-label pairs, evenly divided across `width`."""
    step = width / len(entries)
    parts = []
    for index, (value, label) in enumerate(entries):
        x = round(index * step)
        parts.append(
            f"<g>{svgdoc.fade_in(0.08 * index)}"
            f'<text x="{x}" y="{top}" class="b" font-size="{size}">{svgdoc.escape(value)}</text>'
            f'<text x="{x}" y="{top + 18}" class="dim" font-size="10">{svgdoc.escape(label)}</text>'
            "</g>"
        )
    return "".join(parts)


def render_stats(data: dict, today: date) -> str:
    profile = data["profile"]
    recent = window(data["days"], today)
    total = sum(count for _, count in recent)
    repositories = profile["repositories"]["nodes"]

    entries = [
        (f"{total:,}", "contributions"),
        (f"{profile['repositories']['totalCount']:,}", "public repos"),
        (f"{sum(r['stargazerCount'] for r in repositories):,}", "stars earned"),
        (f"{profile['followers']['totalCount']:,}", "followers"),
    ]
    body = cells(entries, width=WIDTH, size=26, top=30)
    return svgdoc.document(
        WIDTH,
        58,
        body,
        title=f"{total:,} contributions in the last year",
        chars="".join(value + label for value, label in entries),
    )


def render_streak(data: dict, today: date) -> str:
    counts = streaks(data["days"], today)
    entries = [
        (f"{counts['current']:,}", "current streak"),
        (f"{counts['longest']:,}", "longest streak"),
        (f"{counts['active']:,}", "active days"),
    ]

    fraction = counts["current"] / counts["longest"] if counts["longest"] else 0
    filled = round(WIDTH * fraction)
    caption = f"current run is {round(fraction * 100)}% of the longest"

    body = (
        cells(entries, width=WIDTH, size=26, top=30)
        + f'<rect x="0" y="64" width="{WIDTH}" height="6" rx="3" fill="var(--faint)"/>'
        f'<rect x="0" y="64" width="{filled}" height="6" rx="3" fill="var(--accent)">'
        f'<animate attributeName="width" from="0" to="{filled}" dur="0.9s" '
        'begin="0.3s" fill="freeze"/></rect>'
        f'<text x="0" y="88" class="dim" font-size="10">{svgdoc.escape(caption)}</text>'
    )
    return svgdoc.document(
        WIDTH,
        94,
        body,
        title=f"{counts['current']} day current streak, {counts['longest']} day longest",
        chars="".join(value + label for value, label in entries) + caption,
    )


def _bar(rows: list[tuple[str, float]], colors: dict[str, str], y: int, index: int) -> str:
    clip = f"clip{index}"
    segments = []
    offset = 0.0
    for position, (name, fraction) in enumerate(rows):
        segment = fraction * WIDTH
        color = colors.get(name, "#8b949e")
        segments.append(
            f'<rect x="{offset:.2f}" y="{y}" width="{segment:.2f}" height="10" fill="{color}" '
            f">{svgdoc.fade_in(0.06 * position, 0.5)}</rect>"
        )
        offset += segment
    return (
        f'<clipPath id="{clip}"><rect x="0" y="{y}" width="{WIDTH}" height="10" rx="5"/></clipPath>'
        f'<rect x="0" y="{y}" width="{WIDTH}" height="10" rx="5" fill="var(--faint)"/>'
        f'<g clip-path="url(#{clip})">{"".join(segments)}</g>'
    )


def _legend(rows: list[tuple[str, float]], colors: dict[str, str], top: int) -> tuple[str, int]:
    size = 10
    parts = []
    x, y = 0.0, top
    for name, fraction in rows:
        label = f"{name.lower()} {fraction * 100:.0f}%"
        entry = 9 + 5 + typeface.width(label, size)
        if x and x + entry > WIDTH:
            x, y = 0.0, y + 17
        color = colors.get(name, "#8b949e")
        parts.append(
            f'<rect x="{x:.1f}" y="{y - 7}" width="7" height="7" rx="1.5" fill="{color}"/>'
            f'<text x="{x + 12:.1f}" y="{y}" class="dim" font-size="{size}">'
            f"{svgdoc.escape(label)}</text>"
        )
        x += entry + 12
    return "".join(parts), y


def render_languages(data: dict) -> str:
    stats = languages(data["profile"]["repositories"]["nodes"])
    colors = dict(stats["colors"], other="#8b949e")
    by_bytes = share(stats["bytes"])
    by_repo = share(stats["repos"])

    if not by_bytes and not by_repo:
        body = '<text x="0" y="20" class="dim" font-size="11">no public repositories yet</text>'
        return svgdoc.document(
            WIDTH, 30, body, title="Top languages", chars="no public repositories yet"
        )

    # Each bar carries its own legend: the two share a colour per language but
    # not a ranking, so one shared set of percentages would misdescribe one of them.
    sections = [("by bytes", by_bytes), ("by repo", by_repo)]
    parts, chars, baseline = [], "", 10

    for index, (caption, rows) in enumerate(sections):
        parts.append(f'<text x="0" y="{baseline}" class="dim" font-size="10">{caption}</text>')
        parts.append(_bar(rows, colors, baseline + 8, index))
        legend, baseline = _legend(rows, colors, baseline + 34)
        parts.append(legend)
        chars += caption + "".join(f"{name.lower()} {f * 100:.0f}%" for name, f in rows)
        baseline += 30

    return svgdoc.document(
        WIDTH,
        baseline - 22,
        "".join(parts),
        title="Top languages by bytes and by repository",
        chars=chars,
    )


def render_year(data: dict, today: date) -> str:
    recent = window(data["days"], today)
    counts = {moment: count for moment, count in recent}
    cuts = thresholds([count for _, count in recent])

    start = recent[0][0]
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back to the preceding Sunday
    weeks = []
    cursor = start
    while cursor <= today:
        weeks.append([cursor + timedelta(days=offset) for offset in range(7)])
        cursor += timedelta(days=7)

    gutter = 32
    size = round((WIDTH - gutter) / len(weeks) / typeface.ADVANCE, 2)
    advance = size * typeface.ADVANCE
    line = size * 1.16
    top = 26

    opacity = {1: 0.38, 2: 0.58, 3: 0.79, 4: 1.0}
    rows = []
    for weekday in range(7):
        runs, current, text = [], None, ""
        for week in weeks:
            moment = week[weekday]
            value = 0 if moment > today or moment < recent[0][0] else counts.get(moment, 0)
            step = level(value, cuts)
            if step != current and text:
                runs.append((current, text))
                text = ""
            current, text = step, text + (svgdoc.RAMP[step - 1] if step else "·")
        runs.append((current, text))

        spans = "".join(
            f'<tspan class="faint">{svgdoc.escape(text)}</tspan>'
            if step == 0
            else f'<tspan class="accent" opacity="{opacity[step]}">{svgdoc.escape(text)}</tspan>'
            for step, text in runs
        )
        rows.append(
            f'<text x="{gutter}" y="{top + (weekday + 0.8) * line:.2f}" '
            f'font-size="{size}">{spans}'
            f"{svgdoc.fade_in(0.05 * weekday, 0.6)}</text>"
        )

    labels = []
    for weekday, name in ((1, "mon"), (3, "wed"), (5, "fri")):
        labels.append(
            f'<text x="0" y="{top + (weekday + 0.8) * line:.2f}" class="dim" font-size="9">'
            f"{name}</text>"
        )

    # Label a month at the first column that actually opens it, so the leading
    # partial week doesn't claim the slot its own month never fills.
    months = [
        (index, MONTHS[week[0].month - 1])
        for index, week in enumerate(weeks)
        if week[0].day <= 7 and index < len(weeks) - 1
    ]
    month_labels = "".join(
        f'<text x="{gutter + index * advance:.2f}" y="14" class="dim" font-size="9">{name}</text>'
        for index, name in months
    )

    legend_y = round(top + 7 * line + 18)
    scale = "".join(
        f'<tspan class="accent" opacity="{opacity[step]}">{svgdoc.RAMP[step - 1]}</tspan>'
        for step in range(1, 5)
    )
    legend = (
        f'<text x="{WIDTH - 108}" y="{legend_y}" class="dim" font-size="10">less '
        f'<tspan class="faint">·</tspan>{scale}<tspan class="dim"> more</tspan></text>'
    )

    total = sum(count for _, count in recent)
    return svgdoc.document(
        WIDTH,
        legend_y + 6,
        month_labels + "".join(labels) + "".join(rows) + legend,
        title=f"{total:,} contributions over the last year, one character per day",
        chars=svgdoc.RAMP + "·" + "".join(MONTHS) + "monwedfrilessmore",
    )


# -------------------------------------------------------------------------- main


def main() -> None:
    today = datetime.now(timezone.utc).date()
    offline = "--offline" in sys.argv
    token = os.environ.get("GITHUB_TOKEN")

    if offline or not token:
        if not offline:
            print("GITHUB_TOKEN is not set; rendering synthetic data", file=sys.stderr)
        data = synthetic(today)
    else:
        try:
            data = fetch(token, USERNAME, today)
        except (urllib.error.URLError, RuntimeError, TimeoutError) as error:
            print(f"GitHub sync failed: {error}", file=sys.stderr)
            raise SystemExit(1) from error

    outputs = {
        "stats.svg": render_stats(data, today),
        "streak.svg": render_streak(data, today),
        "langs.svg": render_languages(data),
        "year.svg": render_year(data, today),
    }
    for name, markup in outputs.items():
        (ROOT / name).write_text(markup, encoding="utf8")
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
