"""Meal tracking logic - breakfast=0.5, lunch=1, dinner=1
Saturdays: lunch=2 (double), dinner=0 (none)
"""
import configparser
import json
from calendar import monthrange
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

APP_NAME = "bhu_meal_tracker"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
DATA_DIR = Path.home() / ".local" / "share" / APP_NAME
STATE_FILE = DATA_DIR / "state.json"
HISTORY_FILE = DATA_DIR / "history.json"

DEFAULT_CONFIG = """\
[settings]
remind_breakfast = true
remind_lunch = true
remind_dinner = true
notification_timeout_seconds = 10
poll_interval_minutes = 15
nag_until = 23:30
price_breakfast = 27.61
price_lunch = 50.48
price_dinner = 50.48
tax_percent = 5
allowed_misses_per_month = 25
"""

MEALS = ["breakfast", "lunch", "dinner"]

def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cfg = CONFIG_DIR / "config.ini"
    if not cfg.exists():
        cfg.write_text(DEFAULT_CONFIG)
    if not HISTORY_FILE.exists():
        # empty history
        save_history({})

def load_config():
    cfg = configparser.ConfigParser()
    cfg_path = CONFIG_DIR / "config.ini"
    if cfg_path.exists():
        cfg.read(cfg_path)
    s = cfg["settings"] if "settings" in cfg else {}
    return {
        "remind_breakfast": s.getboolean("remind_breakfast", True),
        "remind_lunch": s.getboolean("remind_lunch", True),
        "remind_dinner": s.getboolean("remind_dinner", True),
        "notification_timeout_seconds": s.getint("notification_timeout_seconds", 10),
        "poll_interval_minutes": s.getint("poll_interval_minutes", 15),
        "nag_until": s.get("nag_until", "23:30"),
        "price_breakfast": s.getfloat("price_breakfast", 27.61),
        "price_lunch": s.getfloat("price_lunch", 50.48),
        "price_dinner": s.getfloat("price_dinner", 50.48),
        "tax_percent": s.getfloat("tax_percent", 5.0),
        "allowed_misses_per_month": s.getint("allowed_misses_per_month", 25),
    }

def _hhmm(value: str, fallback=(23, 30)):
    try:
        hh, mm = value.strip().split(":")[:2]
        return int(hh), int(mm)
    except Exception:
        return fallback

def _date_key(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def _day_name(d: datetime) -> str:
    return d.strftime("%A")  # e.g. Saturday

def meal_value(meal: str, d: datetime) -> float:
    day = _day_name(d)
    is_sat = (day == "Saturday")
    if meal == "breakfast":
        return 0.5
    if meal == "lunch":
        return 2.0 if is_sat else 1.0
    if meal == "dinner":
        return 0.0 if is_sat else 1.0
    return 0.0

def load_history():
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_history(h):
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(h, f, indent=2)
        os.replace(tmp, HISTORY_FILE)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass

def get_day_entry(d: datetime) -> dict:
    h = load_history()
    k = _date_key(d)
    if k not in h:
        h[k] = {
            "date": k,
            "weekday": _day_name(d),
            "breakfast": False,
            "lunch": False,
            "dinner": False,
            "meals_counted": 0.0,
        }
    # recompute counted
    e = h[k]
    total = 0.0
    for m in MEALS:
        if e.get(m, False):
            total += meal_value(m, d)
    e["meals_counted"] = round(total, 2)
    e["weekday"] = _day_name(d)
    save_history(h)
    return e

def toggle_meal(d: datetime, meal: str, value: bool):
    h = load_history()
    k = _date_key(d)
    if k not in h:
        h[k] = {"date": k, "weekday": _day_name(d), "breakfast": False, "lunch": False, "dinner": False}
    h[k][meal] = bool(value)
    # recompute
    total = 0.0
    for m in MEALS:
        if h[k].get(m, False):
            total += meal_value(m, d)
    h[k]["meals_counted"] = round(total, 2)
    h[k]["weekday"] = _day_name(d)
    save_history(h)
    return h[k]

def servings(meal: str, d: datetime) -> int:
    """Portions of a meal the mess provides on day `d`.

    Billing uses servings, not the meal-credit weights: Saturday lunch is two
    portions and Saturday dinner is none.
    """
    if meal == "lunch":
        return 2 if _day_name(d) == "Saturday" else 1
    if meal == "dinner":
        return 0 if _day_name(d) == "Saturday" else 1
    return 1

def unit_price(meal: str) -> float:
    """Tax-inclusive price of one portion, rounded to paise."""
    cfg = load_config()
    rate = cfg.get(f"price_{meal}", 0.0)
    return round(rate * (1.0 + cfg["tax_percent"] / 100.0), 2)

def day_bill(e, d: datetime):
    """(total, lines) for one day. `lines` is [(meal, servings, unit, subtotal)]."""
    lines = []
    total = 0.0
    if e:
        for meal in MEALS:
            if not e.get(meal):
                continue
            n = servings(meal, d)
            if n <= 0:
                continue
            unit = unit_price(meal)
            sub = round(unit * n, 2)
            total += sub
            lines.append((meal, n, unit, sub))
    return round(total, 2), lines

def bill_between(start: datetime, end: datetime):
    """Totals for a range: subtotal, tax, grand total, and spend per meal."""
    cfg = load_config()
    rate = {m: cfg[f"price_{m}"] for m in MEALS}
    subtotal = tax = total = 0.0
    by_meal = {m: 0.0 for m in MEALS}
    portions = {m: 0 for m in MEALS}
    days = 0
    for d, e in entries_between(start, end):
        if not e:
            continue
        day_total, lines = day_bill(e, d)
        if day_total:
            days += 1
        total += day_total
        for meal, n, unit, sub in lines:
            by_meal[meal] = round(by_meal[meal] + sub, 2)
            portions[meal] += n
            pre = round(rate[meal] * n, 2)
            subtotal += pre
            tax += round(sub - pre, 2)
    return {
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "total": round(total, 2),
        "by_meal": by_meal,
        "portions": portions,
        "days": days,
    }

def allowance_status(d=None, scope="cycle"):
    """Missed-meal allowance for the billing cycle containing `d`.

    Misses are counted in meal credits, not servings: breakfast is worth 0.5,
    Saturday lunch 2.0 and Saturday dinner 0. So skipping breakfast alone costs
    half a miss. (Billing still uses whole servings, since that is what is
    charged.) Only elapsed days count, and counting starts at the first day you
    have a record for. `scope` picks the whole cycle or just batch 1 / 2.
    """
    d = d or today()
    cfg = load_config()
    allowed = cfg["allowed_misses_per_month"]
    if scope in (1, "1", "batch1", "BATCH 1"):
        start, end = batch_range(1, d)
        label = "BATCH 1"
    elif scope in (2, "2", "batch2", "BATCH 2"):
        start, end = batch_range(2, d)
        label = "BATCH 2"
    else:
        start, end = cycle_start(d), cycle_end(d)
        label = "CYCLE"

    days_total = (end - start).days + 1

    keys = sorted(load_history())
    anchor = datetime.strptime(keys[0], "%Y-%m-%d") if keys else d
    start = max(start, anchor)
    last = min(end, d.replace(hour=23, minute=59, second=59, microsecond=0))

    missed = 0.0
    elapsed = 0
    for day, e in entries_between(start, last) if last >= start else []:
        elapsed += 1
        expected = sum(meal_value(m, day) for m in MEALS)
        got = sum(meal_value(m, day) for m in MEALS if e and e.get(m))
        missed += max(0.0, expected - got)
    missed = round(missed, 2)
    return {
        "allowed": allowed,
        "missed": missed,
        "remaining": round(allowed - missed, 2),
        "over": round(max(0.0, missed - allowed), 2),
        "elapsed_days": elapsed,
        "cycle_days": days_total,
        "tracking_from": start,
        "scope": label,
    }

def peek_day(d: datetime):
    """Read a day's entry WITHOUT creating or saving one.

    Viewing history must not count as logging a day, otherwise browsing to a
    past date would add a phantom 0-meal entry and skew the stats.
    """
    k = _date_key(d)
    e = load_history().get(k)
    if e:
        e = dict(e)
        # Recompute rather than trusting the stored total: it can be stale if a
        # day was written before a rule change, and every reader would show it.
        e["meals_counted"] = round(
            sum(meal_value(m, d) for m in MEALS if e.get(m, False)), 2)
        return e
    return {"date": k, "weekday": _day_name(d), "breakfast": False,
            "lunch": False, "dinner": False, "meals_counted": 0.0}

def today():
    return datetime.now()

def meal_label(meal: str, d: datetime) -> str:
    v = meal_value(meal, d)
    note = " - Sat double" if v == 2.0 else ""
    return f"{meal.title()} ({v}{note})"

def offered_meals(d=None):
    """Meals applicable on day `d`, as (key, label), after Saturday rules and config flags."""
    d = d or today()
    e = get_day_entry(d)
    cfg = load_config()
    flags = {
        "breakfast": "remind_breakfast",
        "lunch": "remind_lunch",
        "dinner": "remind_dinner",
    }
    out = []
    for m in MEALS:
        if not cfg.get(flags[m], True):
            continue
        if meal_value(m, d) <= 0:
            continue
        out.append((m, meal_label(m, d)))
    return out

def pending_meals(d=None):
    """Subset of offered_meals not yet ticked off today."""
    d = d or today()
    e = get_day_entry(d)
    return [m for m, _ in offered_meals(d) if not e.get(m, False)]

def in_nag_window(d=None) -> bool:
    d = d or today()
    hh, mm = _hhmm(load_config()["nag_until"])
    return (d.hour, d.minute) < (hh, mm)

def daterange(start: datetime, end: datetime):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def week_start(d=None):
    d = d or today()
    return (d - timedelta(days=d.weekday())).replace(hour=0, minute=0,
                                                    second=0, microsecond=0)

def month_start(d=None):
    d = d or today()
    return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def month_end(d=None):
    start = month_start(d)
    nxt = (start.replace(year=start.year + 1, month=1)
           if start.month == 12 else start.replace(month=start.month + 1))
    return nxt - timedelta(days=1)
def year_start(d=None):
    d = d or today()
    return d.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def year_end(d=None):
    return year_start(d).replace(month=12, day=31)


# The mess does not bill on calendar months. Its cycle runs from the 3rd of one
# month to the 2nd of the next, and each cycle is billed as two batches:
# batch 1 covers the 3rd-17th, batch 2 covers the 18th-2nd.
CYCLE_START_DAY = 3
BATCH1_LAST_DAY = 17
BATCH1_LENGTH = BATCH1_LAST_DAY - CYCLE_START_DAY + 1      # always 15 days


def _add_months(d, n):
    """Shift by whole months, clamping the day to the target month's length."""
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    return d.replace(year=y, month=m, day=min(d.day, monthrange(y, m)[1]))


def cycle_start(d=None):
    """First day (the 3rd, midnight) of the billing cycle containing `d`."""
    d = d or today()
    anchor = d.replace(day=CYCLE_START_DAY, hour=0, minute=0, second=0, microsecond=0)
    if d < anchor:
        anchor = _add_months(anchor, -1)
    return anchor


def cycle_end(d=None):
    """Last day (the 2nd of the next month, 23:59:59) of `d`'s cycle."""
    start = _add_months(cycle_start(d), 1)
    return start - timedelta(seconds=1)


def cycle_days(d=None):
    return (cycle_end(d) - cycle_start(d)).days + 1


def batch_of(d):
    """1 for the 3rd-17th, 2 for the 18th-2nd."""
    offset = (d - cycle_start(d)).days
    return 1 if offset < BATCH1_LENGTH else 2


def batch_range(n, d=None):
    """(start, end) of batch 1 or 2 of `d`'s cycle."""
    start = cycle_start(d)
    if n == 1:
        return start, start + timedelta(days=BATCH1_LENGTH - 1)
    return start + timedelta(days=BATCH1_LENGTH), cycle_end(d)


def batch_label(d=None):
    return f"BATCH {batch_of(d or today())}"

def entries_between(start: datetime, end: datetime):
    """(date, entry_or_None) for every day in the range, logged or not."""
    h = load_history()
    out = []
    for d in daterange(start, end):
        e = h.get(_date_key(d))
        out.append((d, e if e else None))
    return out

def summary(start: datetime, end: datetime):
    """Totals for a range. Days with no entry count as unlogged, not zero."""
    rows = entries_between(start, end)
    total = 0.0
    logged = 0
    meals = {"breakfast": 0, "lunch": 0, "dinner": 0}
    best = (0.0, None)
    for d, e in rows:
        if not e:
            continue
        logged += 1
        t = float(e.get("meals_counted", 0.0))
        total += t
        for m in MEALS:
            if e.get(m):
                meals[m] += 1
        if t > best[0]:
            best = (t, d)
    span = len(rows)
    return {
        "total": round(total, 2),
        "logged": logged,
        "span": span,
        "avg": round(total / logged, 2) if logged else 0.0,
        "avg_span": round(total / span, 2) if span else 0.0,
        "missing": span - logged,
        "meals": meals,
        "best_value": round(best[0], 2),
        "best_date": best[1],
    }

def weekday_averages(start: datetime, end: datetime):
    """(averages, counts) indexed Monday..Sunday."""
    sums = [0.0] * 7
    counts = [0] * 7
    for d, e in entries_between(start, end):
        if not e:
            continue
        i = d.weekday()
        sums[i] += float(e.get("meals_counted", 0.0))
        counts[i] += 1
    avgs = [round(sums[i] / counts[i], 2) if counts[i] else 0.0 for i in range(7)]
    return avgs, counts

def cumulative(start: datetime, end: datetime):
    running = 0.0
    series = []
    for d, e in entries_between(start, end):
        running += float(e.get("meals_counted", 0.0)) if e else 0.0
        series.append(round(running, 2))
    return series

def set_meals(d: datetime, **flags):
    """Set several meals at once and recompute the day."""
    for meal, value in flags.items():
        if meal in MEALS:
            toggle_meal(d, meal, bool(value))
    return get_day_entry(d)

def prompt_meal_log(d=None):
    """Show the zenity checklist for day `d` and persist the result.

    Returns True if the day ended up fully logged, False if the dialog was
    cancelled or the day still has meals outstanding.
    """
    d = d or today()
    e = get_day_entry(d)
    items = offered_meals(d)
    if not items:
        return True
    import subprocess
    cmd = ["zenity", "--list", "--checklist", "--title", "Meal Log", "--text",
           f"Log meals for {e['date']} ({e['weekday']})", "--column", "Tick",
           "--column", "Meal", "--separator", "\n"]
    for key, label in items:
        cmd.append("TRUE" if e.get(key, False) else "FALSE")
        cmd.append(label)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as ex:
        notify("Meal Reminder", "Could not show meal log dialog")
        return False
    if res.returncode != 0:
        return not pending_meals(d)
    selected = set(s.strip() for s in res.stdout.splitlines() if s.strip())
    for key, label in items:
        toggle_meal(d, key, label in selected)
    return not pending_meals(d)

def notify(title, msg):
    try:
        import subprocess
        timeout = load_config().get("notification_timeout_seconds", 10)
        subprocess.run(["notify-send", "-a", "Meal Tracker", title, msg], timeout=timeout)
    except Exception:
        pass
