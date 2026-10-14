"""Map the rolling data window onto real Sunday-first calendar weeks."""
from datetime import date, timedelta


def calendar_layout(days):
    if not days:
        raise ValueError("A calendar needs at least one dated contribution")
    dates = [date.fromisoformat(day['date']) for day in days]
    if any(b != a + timedelta(days=1) for a, b in zip(dates, dates[1:])):
        raise ValueError("Calendar dates must be unique, consecutive and chronological")
    # Python Monday=0; GitHub's contribution graph uses Sunday=0.
    first_sunday = dates[0] - timedelta(days=(dates[0].weekday() + 1) % 7)
    columns = (dates[-1] - first_sunday).days // 7 + 1
    cells = []
    for day, actual_date in zip(days, dates):
        offset = (actual_date - first_sunday).days
        column, row = divmod(offset, 7)
        cells.append({'day': day, 'column': column, 'row': row})
    # Do not manufacture counts for dates outside the requested window.
    # Those edge slots remain unplanted ground in the renderer.
    return {'weekStart': first_sunday.isoformat(), 'columns': columns, 'cells': cells}
