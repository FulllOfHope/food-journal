#!/usr/bin/env python3
"""Tray + CLI viewer for meal analytics."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import threading
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meal_common as mc

try:
    from PIL import Image, ImageDraw
    import pystray
except Exception:
    pystray = None
    Image = None
    ImageDraw = None

def make_icon(color=(46, 204, 113)):
    if not Image:
        return None
    try:
        img = Image.new("RGBA", (64, 64), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((8,8,56,56), fill=color)
        return img
    except Exception:
        return None

def period_stats(start: datetime, end: datetime):
    h = mc.load_history()
    total_meals = 0.0
    days = 0
    by_day = []
    cur = start
    while cur <= end:
        k = mc._date_key(cur)
        if k in h:
            e = h[k]
            total_meals += float(e.get("meals_counted", 0.0))
            days += 1
            by_day.append(e)
        cur += timedelta(days=1)
    avg = round(total_meals / days, 2) if days > 0 else 0.0
    return {"total": round(total_meals,2), "days": days, "avg": avg, "by_day": by_day}

def week_range(d=None):
    d = d or mc.today()
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end

def month_range(d=None):
    d = d or mc.today()
    start = d.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year+1, month=1, day=1) - timedelta(days=1)
    else:
        end = start.replace(month=start.month+1, day=1) - timedelta(days=1)
    return start, end

def year_range(d=None):
    d = d or mc.today()
    start = d.replace(month=1, day=1)
    end = d.replace(month=12, day=31)
    return start, end

def cycle_range(d=None):
    d = d or mc.today()
    return mc.cycle_start(d), mc.cycle_end(d)


def show_analytics():
    d = mc.today()
    wstart, wend = week_range(d)
    cstart, cend = cycle_range(d)
    ystart, yend = year_range(d)
    ranges = [("This Week", wstart, wend), ("This Cycle", cstart, cend)]
    ranges.append(("Batch 1", *mc.batch_range(1, d)))
    ranges.append(("Batch 2", *mc.batch_range(2, d)))
    ranges.append(("This Year", ystart, yend))

    lines = ["Meal Analytics",
             f"Today: {mc.get_day_entry(d)['meals_counted']} meals "
             f"({d.strftime('%Y-%m-%d %A')}) - batch {mc.batch_of(d)}",
             f"Cycle: {cstart.strftime('%d %b %Y')} to {cend.strftime('%d %b %Y')} "
             f"(day {(d - cstart).days + 1}/{mc.cycle_days(d)} of {mc.cycle_days(d)})",
             ""]
    for label, start, end in ranges:
        s = mc.summary(start, end)
        b = mc.bill_between(start, end)
        lines.append(f"{label} ({start.strftime('%d %b')} - {end.strftime('%d %b')}): "
                     f"{s['total']} total, {s['logged']} days logged, avg {s['avg']}/day")
        lines.append(f"    bill Rs {b['total']:,.2f} (incl Rs {b['tax']:,.2f} tax)")

    a = mc.allowance_status()
    lines.append("")
    if a["over"]:
        lines.append(f"Missed meals this cycle: {a['missed']:g} - OVER the "
                     f"{a['allowed']:g} allowed by {a['over']:g}")
    else:
        lines.append(f"Missed meals this cycle: {a['missed']:g} of {a['allowed']:g} "
                     f"allowed - {a['remaining']:g} remaining")
    text = "\n".join(lines)
    try:
        subprocess.run(["zenity", "--info", "--title", "Meal Analytics", "--text", text], check=False)
    except Exception:
        try:
            subprocess.run(["notify-send", "-a", "Meal Tracker", "Meal Analytics", text], check=False)
        except Exception:
            print(text)

def toggle_today(meal):
    d = mc.today()
    e = mc.get_day_entry(d)
    newv = not e.get(meal, False)
    mc.toggle_meal(d, meal, newv)
    mc.notify("Meal Logged", f"{meal.title()}: {'✓' if newv else '✗'} ({e['date']})")

def tray_main():
    if pystray is None:
        # fallback to gui
        subprocess.Popen([sys.executable, str(Path(__file__).parent/"meal_gui.py")])
        return
    mc.ensure_dirs()
    app_state = {"running": True}
    icon = pystray.Icon("bhu_meal_tracker", make_icon(), "Meal Tracker")
    d = mc.today()
    e = mc.get_day_entry(d)

    def make_menu():
        items = []
        items.append(pystray.MenuItem(f"Today ({d.strftime('%a %b %d')}): {e['meals_counted']} meals", None, enabled=False))
        items.append(pystray.Menu.SEPARATOR)
        def mk_toggle(m):
            def cb(icon, item):
                toggle_today(m)
                icon.update_menu()
            return pystray.MenuItem(f"{'✓' if mc.get_day_entry(mc.today()).get(m,False) else '○'} {m.title()}", cb)
        for m in mc.MEALS:
            items.append(mk_toggle(m))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Open GUI", lambda icon,item: subprocess.Popen([sys.executable, str(Path(__file__).parent/"meal_gui.py")])))
        items.append(pystray.MenuItem("View Analytics", lambda icon,item: show_analytics()))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Quit", lambda icon,item: (app_state.update(running=False), icon.stop())))
        return pystray.Menu(*items)

    icon.menu = make_menu()
    def setup(icon):
        icon.visible = True
    icon.run(setup=setup)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("tray", "analytics", "remind", "gui"):
        if sys.argv[1] == "tray":
            tray_main()
            return
        elif sys.argv[1] == "analytics":
            show_analytics()
            return
        elif sys.argv[1] == "remind":
            subprocess.run([sys.executable, str(Path(__file__).parent/"meal_reminder.py")])
            return
        elif sys.argv[1] == "gui":
            subprocess.run([sys.executable, str(Path(__file__).parent/"meal_gui.py")])
            return
    subprocess.run([sys.executable, str(Path(__file__).parent/"meal_gui.py")])

if __name__ == "__main__":
    main()
