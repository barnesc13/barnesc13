from datetime import date, timedelta
from pathlib import Path
import sys
import re
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from calendar_layout import calendar_layout
from generate_questlog import build_data
from questlog_art import render


class CalendarLayoutTests(unittest.TestCase):
    def data(self, end):
        counts = {end-timedelta(days=i): i % 9 for i in range(182)}
        return build_data(counts, 'barnesc13', end)

    def test_current_window_uses_native_github_weekdays_without_losing_days(self):
        data = self.data(date(2026, 10, 14))
        layout = calendar_layout(data['last26Weeks'])
        self.assertEqual(layout['weekStart'], '2026-04-12')
        self.assertEqual(layout['columns'], 27)
        self.assertEqual((layout['cells'][0]['column'], layout['cells'][0]['row']), (0, 4))
        self.assertEqual((layout['cells'][-1]['column'], layout['cells'][-1]['row']), (26, 3))
        self.assertEqual([cell['day'] for cell in layout['cells']], data['last26Weeks'])
        occupied = {(c['column'], c['row']) for c in layout['cells']}
        blank = {(col, row) for col in range(27) for row in range(7)} - occupied
        self.assertEqual(blank, {(0,0),(0,1),(0,2),(0,3),(26,4),(26,5),(26,6)})

    def test_every_weekday_and_leap_year_keeps_exact_dates(self):
        for end in [date(2026, 10, 11)+timedelta(days=i) for i in range(7)] + [date(2028, 3, 1)]:
            data = self.data(end)
            layout = calendar_layout(data['last26Weeks'])
            self.assertEqual(layout['columns'], 26 if end.weekday() == 5 else 27)
            self.assertEqual(len(layout['cells']), 182)
            start = date.fromisoformat(layout['weekStart'])
            for cell in layout['cells']:
                actual = date.fromisoformat(cell['day']['date'])
                self.assertEqual(cell['row'], (actual.weekday()+1) % 7)
                self.assertEqual(start+timedelta(days=7*cell['column']+cell['row']), actual)

    def test_rendered_positions_and_counts_are_calendar_aligned(self):
        data = self.data(date(2026, 10, 14))
        root = ET.fromstring(render(data))
        cells = root.findall('.//{http://www.w3.org/2000/svg}g[@data-date]')
        self.assertEqual(len(cells), 182)
        self.assertEqual(sum(int(c.get('data-count')) for c in cells), data['requestedWindow']['total'])
        expected = {c['day']['date']: c for c in calendar_layout(data['last26Weeks'])['cells']}
        for cell in cells:
            want = expected[cell.get('data-date')]
            self.assertEqual(int(cell.get('data-calendar-column')), want['column'])
            self.assertEqual(int(cell.get('data-calendar-row')), want['row'])
            self.assertEqual(int(cell.get('data-count')), want['day']['count'])
            # Verify geometry too, not just the explanatory data attributes.
            n=want['day']['count']
            level=0 if n==0 else 1 if n<=3 else 2 if n<=7 else 3 if n<=15 else 4 if n<=31 else 5
            height=[.8,4,7,11,16,21][level]
            x0=(want['column']+.09)*(26/27)
            row=want['row']+.12
            top_face=list(cell)[3]
            point=re.match(r'M(-?[\d.]+) (-?[\d.]+)',top_face.get('d'))
            self.assertIsNotNone(point)
            self.assertAlmostEqual(float(point[1]),251+x0*35.5-row*4,places=2)
            self.assertAlmostEqual(float(point[2]),337+row*30.5-height,places=2)

    def test_gaps_duplicates_and_reversed_dates_are_rejected(self):
        for dates in (['2026-01-01', '2026-01-03'], ['2026-01-01', '2026-01-01'], ['2026-01-02', '2026-01-01']):
            with self.assertRaises(ValueError):
                calendar_layout([{'date': day, 'count': 1} for day in dates])


if __name__ == '__main__':
    unittest.main()
