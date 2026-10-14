#!/usr/bin/env python3
"""Refresh the quest-log SVG from GitHub's public contribution calendar.

Python standard library only. No PAT, OAuth grant, GraphQL or private repo
access. Never infer counts from color levels or replace missing data with zero.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from questlog_art import render

WINDOW_DAYS = 182
COUNT_PATTERN = re.compile(r"^\s*(No|[\d,]+)\s+contributions?\b", re.I)
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})\Z")


def label_count(label: str | None) -> int | None:
    match = COUNT_PATTERN.match(label or "")
    if not match:
        return None
    return 0 if match[1].lower() == "no" else int(match[1].replace(",", ""))


class CalendarParser(HTMLParser):
    """Read both current td/tool-tip calendars and older data-count SVGs."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells = []
        self.tooltips = {}
        self._tooltip_id = None
        self._tooltip_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("data-date"):
            self.cells.append(attrs)
        if tag == "tool-tip" and attrs.get("for"):
            self._tooltip_id = attrs["for"]
            self._tooltip_text = []

    def handle_data(self, data):
        if self._tooltip_id:
            self._tooltip_text.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._tooltip_id:
            self.tooltips[self._tooltip_id] = "".join(self._tooltip_text).strip()
            self._tooltip_id = None
            self._tooltip_text = []

    def counts(self):
        result = {}
        for cell in self.cells:
            day = date.fromisoformat(cell["data-date"])
            explicit = cell.get("data-count")
            count = int(explicit.replace(",", "")) if explicit is not None else None
            if count is None:
                for label in (cell.get("aria-label"), cell.get("title"),
                              self.tooltips.get(cell.get("id"))):
                    count = label_count(label)
                    if count is not None:
                        break
            if count is None:
                raise ValueError(f"GitHub did not provide an exact contribution count for {day}")
            if count < 0:
                raise ValueError(f"Invalid negative count for {day}")
            if day in result and result[day] != count:
                raise ValueError(f"Conflicting contribution counts for {day}")
            result[day] = count
        if not result:
            raise ValueError("GitHub returned no contribution calendar cells")
        return result


def parse_calendar(html: str) -> dict[date, int]:
    parser = CalendarParser()
    parser.feed(html)
    parser.close()
    return parser.counts()


def summarize(days: list[dict]) -> dict:
    if not days:
        raise ValueError("Cannot summarize an empty calendar")
    best = streak = 0
    best_end = None
    for day in days:
        count = day["count"]
        if type(count) is not int or count < 0:
            raise ValueError("Contribution counts must be nonnegative integers")
        streak = streak + 1 if count else 0
        if streak > best:
            best, best_end = streak, day["date"]
    # A zero on the partial current day does not break yesterday's active streak.
    last = len(days) - 1 if days[-1]["count"] else len(days) - 2
    current = 0
    for index in range(last, -1, -1):
        if not days[index]["count"]:
            break
        current += 1
    return {
        "start": days[0]["date"], "end": days[-1]["date"],
        "definition": "182 consecutive GitHub calendar dates; end date selected in UTC, current day partial.",
        "total": sum(day["count"] for day in days),
        "days": len(days),
        "activeDays": sum(day["count"] > 0 for day in days),
        "bestStreak": best, "bestStreakEnd": best_end,
        "currentStreakAllowTodayPending": current,
        "currentStreakEnd": days[last]["date"] if current else None,
        "currentStreakStrictThroughToday": streak,
        "peakCount": max(day["count"] for day in days),
    }


def build_data(counts: dict[date, int], username: str, end: date) -> dict:
    start = end - timedelta(days=WINDOW_DAYS - 1)
    expected = [start + timedelta(days=offset) for offset in range(WINDOW_DAYS)]
    missing = [day.isoformat() for day in expected if day not in counts]
    if missing:
        raise ValueError(f"Incomplete GitHub calendar; missing {len(missing)} dates: {', '.join(missing[:5])}")
    days = [{"date": day.isoformat(), "count": counts[day]} for day in expected]
    return {
        "username": username,
        "sourceUrl": f"https://github.com/{username}",
        "source": "GitHub public contribution calendar, unauthenticated",
        "windowEndTimezone": "UTC",
        "countType": "Contributions, not commits",
        "coverage": "Includes only counts GitHub exposes publicly, including private contribution aggregates if enabled by the user. No private repository details are accessed.",
        "streakDefinition": "Consecutive active GitHub calendar dates within the displayed 182-day window; a zero on the partial current day is still pending.",
        "requestedWindow": summarize(days),
        "last26Weeks": days,
    }


def fetch_calendar(username: str, start: date, end: date) -> dict[date, int]:
    """Fetch one calendar-year request, retrying only transient failures."""
    url = f"https://github.com/users/{username}/contributions?" + urlencode({"from": start.isoformat(), "to": end.isoformat()})
    request = Request(url, headers={
        "User-Agent": f"{username}-questlog/1.0 (GitHub profile SVG)",
        "Accept": "text/html", "Accept-Language": "en-US,en;q=0.9",
    })
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                html = response.read(2_000_001)
                if len(html) > 2_000_000:
                    raise ValueError("Unexpectedly large GitHub calendar response")
                return parse_calendar(html.decode("utf-8"))
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** (attempt + 1))
    raise RuntimeError("GitHub calendar request failed")


def fetch_counts(username: str, end: date) -> dict[date, int]:
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Invalid GitHub username")
    start = end - timedelta(days=WINDOW_DAYS - 1)
    counts = {}
    # GitHub returns the calendar year containing `to`, even when `from`
    # crosses New Year. Fetch every intersecting year so January-June windows
    # retain their previous-year dates instead of silently dropping them.
    for year in range(start.year, end.year + 1):
        period_start = max(start, date(year, 1, 1))
        period_end = min(end, date(year, 12, 31))
        calendar = fetch_calendar(username, period_start, period_end)
        for day, count in calendar.items():
            if period_start <= day <= period_end:
                counts[day] = count
    # build_data verifies that every required date has an exact count. Never
    # fill missing dates with zero or return a partial result after a failure.
    return counts


def validate_svg(svg: str, data: dict) -> None:
    root = ElementTree.fromstring(svg)
    ns = {"s": "http://www.w3.org/2000/svg"}
    actual = {node.attrib["data-date"]: int(node.attrib["data-count"])
              for node in root.findall(".//s:g[@data-date]", ns)}
    expected = {day["date"]: day["count"] for day in data["last26Weeks"]}
    if len(root.findall(".//s:g[@data-date]", ns)) != WINDOW_DAYS or actual != expected:
        raise ValueError("SVG daily tiles do not exactly match the contribution data")
    if root.find(".//s:g[@id='quest-log']", ns) is None:
        raise ValueError("Quest-log panel is missing")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="barnesc13")
    parser.add_argument("--output", type=Path, default=Path("assets/questlog.svg"))
    parser.add_argument("--data-output", type=Path, default=Path("assets/questlog-data.json"))
    parser.add_argument("--input", type=Path, help="Replay a saved real-data snapshot offline (never used by the scheduled workflow)")
    args = parser.parse_args()
    if args.input:
        previous = json.loads(args.input.read_text(encoding="utf-8"))
        end = date.fromisoformat(previous["requestedWindow"]["end"])
        counts = {date.fromisoformat(day["date"]): day["count"] for day in previous["last26Weeks"]}
        data = build_data(counts, args.username, end)
    else:
        end = datetime.now(timezone.utc).date()
        data = build_data(fetch_counts(args.username, end), args.username, end)
    svg = render(data)
    validate_svg(svg, data)
    # Do not touch the previous files until fetch, data validation and rendering succeed.
    for destination, content in ((args.output, svg + "\n"),
                                 (args.data_output, json.dumps(data, indent=2) + "\n")):
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(destination)
    stats = data["requestedWindow"]
    print(f"Updated {args.output}: {stats['start']} to {stats['end']}, "
          f"{stats['total']:,} contributions, {stats['activeDays']} active days, "
          f"best streak {stats['bestStreak']}, current streak {stats['currentStreakAllowTodayPending']}.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, ElementTree.ParseError) as exc:
        print(f"Quest log was not updated: {exc}", file=sys.stderr)
        sys.exit(1)
