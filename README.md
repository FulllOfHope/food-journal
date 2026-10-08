# Mess Ledger

A meal tracker styled as a bound paper journal. It nags you at login until
the day's meals are logged.

## Rules

- Breakfast = 0.5 meal
- Lunch = 1.0 meal (Saturdays = 2.0, double)
- Dinner = 1.0 meal (Saturdays = not offered, worth 0)

## Install

The app runs from `~/bhu_meal_tracker` with system Python. Needs `pystray`,
`pillow`, `tkinter`, `zenity` and `notify-send`:

```bash
sudo apt install -y python3-tk zenity
pip install --user pystray pillow
```

Optional system-wide install (`/opt` + `/usr/local/bin/bhu-meal-tracker`,
with its own venv):

```bash
cd ~/bhu_meal_tracker && ./install.sh
```

## Usage

- `bhu-meal-tracker gui` — the Mess Ledger journal GUI
- `bhu-meal-tracker remind` — prompt once for today's meals
- `bhu-meal-tracker analytics` — week/month/year summary
- `bhu-meal-tracker tray` — system tray menu
- `bhu-meal-tracker watch` — the nag loop (normally autostarted, see below)

## GUI

Three views on dot-grid journal paper (stitched spine, margin rule):

- **TODAY** — the day's entry: three sheets stamped EATEN / NOT EATEN
  (click a sheet or press `B` / `L` / `D`). `MARK ALL EATEN` / `CLEAR`.
  The masthead shows the date, a handwritten margin note, the page folio
  and the cycle edition stamp.
- **LOG / EDIT** — correct a past day with the same three sheets, stepping
  with `< YESTERDAY` / `TOMORROW >` (or arrow keys). Below, the leaves of
  the current cycle carry hand-drawn margin ticks; the cycle opening is
  marked and earlier days are flagged `(Previous Cycle)`.
- **INSIGHTS** — the 25-miss pencil box (X per miss, slash per half-miss,
  red once over), the cycle bill split by batch, and meals entered per day
  on graph paper.

Saturday rules apply everywhere: lunch counts double and dinner is not
offered, so the dinner sheet reads KITCHEN CLOSED and is inert.

Keyboard: `B` / `L` / `D` stamps the meal on TODAY (or on the selected day
in LOG / EDIT); `←` / `→` steps days in LOG / EDIT.

## Billing

| Meal | Base | +5% tax | Per serving |
|------|-----:|--------:|------------:|
| Breakfast | 27.61 | 1.38 | **28.99** |
| Lunch | 50.48 | 2.52 | **53.00** |
| Dinner | 50.48 | 2.52 | **53.00** |

Tax is rounded per serving, then summed, so a day of all three meals comes to
`134.99`. Billing uses *servings*, not meal credits: Saturday lunch is two
servings (`106.00`) and Saturday dinner is none. Bill figures appear in the
LOG day total, the history leaves, the TODAY summary, the INSIGHTS bill
block, and `bhu-meal-tracker analytics`.

## Billing cycle and batches

The mess does **not** bill on calendar months. Its cycle runs from the **3rd of
one month to the 2nd of the next**, and each cycle is billed as two batches:

| Batch | Covers | Length |
|-------|--------|--------|
| 1 | 3rd – 17th | always 15 days |
| 2 | 18th – 2nd | 13–16 days, so the batches always total the cycle |

A cycle is exactly as long as the month it starts in, so February cycles are
shorter. Every range that follows the cycle — the STATS ranges, the cycle bill
panel, the allowance and `analytics` — uses these boundaries. The two batch
bills always sum exactly to the cycle total.

Note that days 1st and 2nd belong to the *previous* cycle, so at the start of a
cycle the bill only covers what has elapsed.

## Missed-meal allowance

You may miss up to **25 meals per cycle**. The INSIGHTS pencil box shows
misses struck so far and how many remain; overflow is stamped red, and the
lines under it break the misses down per batch.

Misses are counted in **meal credits**, not servings:

| Meal | Credit |
| --- | --- |
| Breakfast | 0.5 |
| Lunch | 1.0 (2.0 on Saturday) |
| Dinner | 1.0 (0.0 on Saturday — not served) |

So skipping breakfast alone costs half a miss, the pencil box draws that as
a single slash, and the totals can be fractional such as `23.5 remaining`.

Billing is separate and still charges whole servings, because that is what the
mess actually serves you.

Only elapsed days count, and counting starts at your first recorded day, so
installing mid-cycle does not count earlier days against you.

## Theme

`meal_theme.py` holds the journal system (paper/grain/dot-grid canvas,
rubber stamps, pencil boxes, letterpress buttons) and `meal_charts.py`
the canvas charts. Fonts are detected at startup, preferring Playfair
Display (mastheads), Outfit (body), DM Mono (metadata) and Caveat (margin
notes), falling back to installed serif/sans/mono families:

```bash
# optional: journal fonts (all OFL), user-local install
mkdir -p ~/.fonts/meal-tracker
cd ~/.fonts/meal-tracker
# Playfair Display / Outfit: static instances via fonttools from the
# variable fonts at github.com/google/fonts (ofl/playfairdisplay,
# ofl/outfit); DM Mono + Caveat ship static:
#   ofl/dmmono/DMMono-{Light,Regular,Medium}.ttf
#   fontsource latin-{500,600,700}-normal.ttf for Caveat
fc-cache -f ~/.fonts
```

## Reminders

`~/.config/autostart/bhu-meal-tracker-reminder.desktop` runs `watch` at every
graphical login. While any meal offered today is unticked, it reopens the log
dialog every `poll_interval_minutes`. Once the day is complete it goes quiet.
The loop holds a lock in `~/.local/share/bhu_meal_tracker/watcher.lock`, so a
second copy exits instead of stacking dialogs. Activity is recorded in
`watcher.log` next to it.

## Config

`~/.config/bhu_meal_tracker/config.ini`

```ini
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
```

Change `price_*` to update the bill everywhere, `tax_percent` to change the tax
rate, and `allowed_misses_per_month` to change the allowance.

`nag_until` stops the nagging overnight — past that time the watcher sleeps
until 00:01 and resumes on the new day. Set a meal's `remind_*` to `false` to
drop it from the prompt entirely (its value stays in the history).

## Data

Stored in `~/.local/share/bhu_meal_tracker/history.json`.