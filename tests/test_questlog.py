"""Offline regression tests; the scheduled job fetches fresh data after these pass."""
from datetime import date, timedelta
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_questlog import build_data, fetch_counts, parse_calendar, summarize, validate_svg
from questlog_art import render


class CalendarTests(unittest.TestCase):
    def test_current_github_markup_exact_counts_not_color_levels(self):
        html = '''<table><td id="day-1" data-date="2026-10-13" data-level="4"></td>
        <td id="day-2" data-date="2026-10-14" data-level="0"></td></table>
        <tool-tip for="day-2">No contributions on October 14th.</tool-tip>
        <tool-tip for="day-1">1,234 contributions on October 13th.</tool-tip>'''
        self.assertEqual(parse_calendar(html), {date(2026,10,13): 1234, date(2026,10,14): 0})

    def test_aria_label_and_old_svg_markup(self):
        html = '''<td data-date="2026-10-12" aria-label="1 contribution on October 12th."></td>
        <rect data-date="2026-10-13" data-count="12" />'''
        self.assertEqual(parse_calendar(html), {date(2026,10,12): 1, date(2026,10,13): 12})

    def test_fail_closed_on_missing_counts(self):
        with self.assertRaises(ValueError):
            parse_calendar('<td data-date="2026-10-14" data-level="4"></td>')
        with self.assertRaises(ValueError):
            parse_calendar('<html>Sign in</html>')
        with self.assertRaises(ValueError):
            build_data({date(2026,10,14): 0}, "barnesc13", date(2026,10,14))

    def test_conflicting_duplicates_and_negative_counts_rejected(self):
        for html in ('<td data-date="2026-10-14" data-count="-1"></td>',
                     '<td data-date="2026-10-14" data-count="1"></td><td data-date="2026-10-14" data-count="2"></td>'):
            with self.assertRaises(ValueError):
                parse_calendar(html)

    def test_streaks_treat_today_as_pending_but_not_yesterday(self):
        def stats(counts):
            return summarize([{"date": (date(2026,10,1)+timedelta(days=i)).isoformat(), "count": n} for i,n in enumerate(counts)])
        result = stats([1,1,0,3,4,5,0])
        self.assertEqual((result['total'],result['activeDays'],result['bestStreak'],result['currentStreakAllowTodayPending']), (14,5,3,3))
        self.assertEqual(result['currentStreakEnd'], '2026-10-06')
        self.assertEqual(result['currentStreakStrictThroughToday'], 0)
        self.assertEqual(stats([1,1,0,0])['currentStreakAllowTodayPending'], 0)
        self.assertIsNone(stats([0,0])['currentStreakEnd'])
        self.assertEqual(stats([1,1,1])['currentStreakAllowTodayPending'], 3)

    def test_cross_year_and_leap_year_windows(self):
        for end in (date(2027,1,4), date(2028,3,1)):
            counts = {end-timedelta(days=i): 1 for i in range(182)}
            data = build_data(counts, "barnesc13", end)
            self.assertEqual(data['requestedWindow']['days'], 182)
            self.assertEqual(data['requestedWindow']['bestStreak'], 182)
            svg = render(data)
            validate_svg(svg, data)
            self.assertIn(str(end.year), svg)

    def test_fetches_each_intersecting_calendar_year(self):
        # The live endpoint returns only `to`'s year, ignoring a `from` in the
        # preceding year. Reproduce that behavior, including exact tooltips.
        def github_calendar(request, timeout):
            query = parse_qs(urlparse(request.full_url).query)
            end = date.fromisoformat(query['to'][0])
            start = date(end.year, 1, 1)
            days = (date(end.year + 1, 1, 1) - start).days
            html = []
            for offset in range(days):
                day = start + timedelta(days=offset)
                count = day.toordinal() % 5
                label = f'{count} contributions' if count else 'No contributions'
                html.append(f'<td id="day-{day}" data-date="{day}" data-level="4"></td>'
                            f'<tool-tip for="day-{day}">{label} on this day.</tool-tip>')
            return BytesIO(''.join(html).encode())

        for end in (date(2026, 1, 4), date(2024, 3, 1), date(2026, 10, 14)):
            with self.subTest(end=end), patch('generate_questlog.urlopen', side_effect=github_calendar) as fetch:
                counts = fetch_counts('barnesc13', end)
                data = build_data(counts, 'barnesc13', end)
                start = end - timedelta(days=181)
                expected = {start + timedelta(days=i): (start + timedelta(days=i)).toordinal() % 5
                            for i in range(182)}
                self.assertEqual(counts, expected)
                self.assertEqual(data['requestedWindow']['total'], sum(expected.values()))
                self.assertEqual(fetch.call_count, end.year - start.year + 1)
                for call in fetch.call_args_list:
                    query = parse_qs(urlparse(call.args[0].full_url).query)
                    self.assertEqual(date.fromisoformat(query['from'][0]).year,
                                     date.fromisoformat(query['to'][0]).year)

    def test_cross_year_fetch_does_not_invent_missing_dates(self):
        pages = [BytesIO(b'<td data-date="2025-12-31" data-count="2"></td>'),
                 BytesIO(b'<td data-date="2026-01-01" data-count="3"></td>')]
        with patch('generate_questlog.urlopen', side_effect=pages):
            counts = fetch_counts('barnesc13', date(2026, 1, 1))
        self.assertEqual(counts, {date(2025, 12, 31): 2, date(2026, 1, 1): 3})
        with self.assertRaisesRegex(ValueError, 'missing 180 dates'):
            build_data(counts, 'barnesc13', date(2026, 1, 1))

    def test_failed_second_year_does_not_return_partial_counts(self):
        pages = [BytesIO(b'<td data-date="2025-12-31" data-count="2"></td>'),
                 URLError('offline'), URLError('offline'), URLError('offline')]
        with patch('generate_questlog.urlopen', side_effect=pages) as fetch, \
                patch('generate_questlog.time.sleep'):
            with self.assertRaises(URLError):
                fetch_counts('barnesc13', date(2026, 1, 1))
        self.assertEqual(fetch.call_count, 4)

    def test_real_snapshot_reproducibility_and_daily_tiles(self):
        snapshot = json.loads((ROOT/'assets/questlog-data.json').read_text())
        counts = {date.fromisoformat(d['date']): d['count'] for d in snapshot['last26Weeks']}
        data = build_data(counts, snapshot['username'], date.fromisoformat(snapshot['requestedWindow']['end']))
        self.assertEqual(data, snapshot)
        svg = render(data)
        validate_svg(svg, data)
        self.assertEqual(svg, render(data))
        self.assertEqual(svg+'\n', (ROOT/'assets/questlog.svg').read_text())
        root = ElementTree.fromstring(svg)
        ns = {'s':'http://www.w3.org/2000/svg'}
        labels = [g.attrib['data-ui-text'] for g in root.findall('.//s:g[@data-ui-text]', ns)]
        self.assertIn(f"{data['requestedWindow']['total']:,}", labels)
        self.assertIn('Quest List', labels)


if __name__ == '__main__':
    unittest.main()
