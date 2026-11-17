"""Расчёт серий и процентов. Работает со строками дат формата YYYY-MM-DD."""

from datetime import date, timedelta


def _to_dates(date_strings):
    return {date.fromisoformat(s) for s in date_strings}


def current_streak(date_strings):
    """Сколько дней подряд привычка выполнена до сегодня."""
    days = _to_dates(date_strings)
    today = date.today()
    start = today if today in days else today - timedelta(days=1)
    streak = 0
    d = start
    while d in days:
        streak += 1
        d -= timedelta(days=1)
    return streak


def record_streak(date_strings):
    days = sorted(_to_dates(date_strings))
    if not days:
        return 0
    best = 1
    cur = 1
    for prev, nxt in zip(days, days[1:]):
        cur = cur + 1 if (nxt - prev).days == 1 else 1
        best = max(best, cur)
    return best


def month_percent(habit, date_strings):
    today = date.today()
    days = _to_dates(date_strings)
    month_days = [date(today.year, today.month, d) for d in range(1, today.day + 1)]
    done = sum(1 for d in month_days if d in days)
    if habit.get("freq_type") == "weekly":
        weeks = (today.day + 6) // 7
        expected = max(1, weeks * (habit.get("freq_target") or 1))
    else:
        expected = max(1, today.day)
    return min(100, round(100 * done / expected))
