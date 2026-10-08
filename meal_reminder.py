#!/usr/bin/env python3
"""One-shot meal log prompt. The nag-until-done loop lives in meal_watcher.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meal_common as mc

def main():
    mc.ensure_dirs()
    d = mc.today()
    e = mc.get_day_entry(d)
    if not mc.offered_meals(d):
        mc.notify("Meal Reminder", "All meal reminders are disabled in config.ini")
        return
    done = mc.prompt_meal_log(d)
    if done:
        mc.notify("Meal Tracker", f"All meals logged for {e['date']}")

if __name__ == "__main__":
    main()