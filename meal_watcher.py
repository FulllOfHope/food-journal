#!/usr/bin/env python3
"""Nag the daily meal log until the day is fully logged.

Launched on graphical login. It opens the log dialog at most once per day
while meals are pending; once the day is fully logged it goes quiet and only
wakes to handle the date rolling over. The once-per-day marker lives in
state.json so restarting the watcher does not re-prompt.
"""
import fcntl
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meal_common as mc

LOCK_FILE = mc.DATA_DIR / "watcher.lock"
LOG_FILE = mc.DATA_DIR / "watcher.log"

def log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass

def acquire_lock():
    """Single instance guard: returns the held file object, or None if already running."""
    f = open(LOCK_FILE, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    f.write(str(os.getpid()))
    f.flush()
    return f

def sleep_until(target: datetime):
    while True:
        remaining = (target - datetime.now()).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 300))

def next_day_start(now: datetime) -> datetime:
    return (now + timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)

import json

def _last_nag_date():
    try:
        return json.load(open(mc.STATE_FILE)).get("last_nag")
    except Exception:
        return None

def _set_last_nag_date(key):
    try:
        mc.ensure_dirs()
        tmp = mc.STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps({"last_nag": key}))
        tmp.replace(mc.STATE_FILE)
    except Exception:
        pass

def main():
    lock = acquire_lock()
    if lock is None:
        log("watcher already running, exiting")
        return
    mc.ensure_dirs()
    cfg = mc.load_config()
    interval = max(1, cfg["poll_interval_minutes"]) * 60
    log(f"watcher started (pid {os.getpid()}), poll every {interval // 60}min, "
        f"nag until {cfg['nag_until']}")

    state = None
    while True:
        now = mc.today()
        try:
            pending = mc.pending_meals(now)
        except Exception as ex:
            log(f"error reading state: {ex}")
            time.sleep(interval)
            continue

        if not pending:
            if state != "done":
                log(f"{mc._date_key(now)}: all meals logged, idling")
                state = "done"
            time.sleep(interval)
            continue

        if not mc.in_nag_window(now):
            if state != "quiet":
                log(f"{mc._date_key(now)}: {len(pending)} meal(s) pending but past "
                    f"{cfg['nag_until']}, pausing until tomorrow")
                state = "quiet"
            sleep_until(next_day_start(now))
            continue

        if state != "prompting":
            log(f"{mc._date_key(now)}: {len(pending)} meal(s) pending: {', '.join(pending)}")
            state = "prompting"
        if _last_nag_date() != mc._date_key(now):
            mc.prompt_meal_log(now)
            _set_last_nag_date(mc._date_key(now))
            log(f"{mc._date_key(now)}: prompted once, going quiet until tomorrow")
        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("watcher interrupted")