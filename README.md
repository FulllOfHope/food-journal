# Mess Ledger

A meal journal that looks like paper.

Breakfast, lunch and dinner recorded as struck-through rows, ticked
allowance cells, a fruiting tree and wandering doodles. Your history is
one plain JSON file you can read, back up and move.

Also serves itself to your phone over your own Wi-Fi, so logging a meal
from the sofa doesn't mean walking to the laptop.

---

## Install

You need **Python 3.9 or newer**. Nothing else is required — no root, no
system packages, and your data never leaves the machine.

### Linux

```bash
git clone https://github.com/FulllOfHope/food-journal.git
cd food-journal
./install.sh
```

### macOS

```bash
git clone https://github.com/FulllOfHope/food-journal.git
cd food-journal
./install.sh
```

### Windows

Git Bash or WSL, then the same two commands. (Tkinter ships with the
official python.org installer — pick the *tcl/tk and IDLE* option.)

### Install without launching

```bash
./install.sh --no-launch
```

### Options

```bash
./install.sh --uninstall     # remove the app (your data is kept)
./install.sh --help
```

### What the installer does

Everything lands under `~/.local` — no `sudo`, nothing outside your home:

| | |
| --- | --- |
| app | `~/.local/share/mess-ledger/` |
| command | `~/.local/bin/mess-ledger` |
| menu entry | `~/.local/share/applications/mess-ledger.desktop` |
| fonts | `~/.local/share/fonts/meal-tracker/` |

Afterwards:

```bash
mess-ledger            # open the journal
mess-ledger phone      # serve it to your phone
```

If `mess-ledger: command not found`, add the folder to your PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

It appears in your application menu as **Mess Ledger**.

It does **not** open by itself at login — a journal window you didn't ask
for is just an annoyance. If you want it to:

```bash
./install.sh --autostart          # start it every login
rm ~/.config/autostart/mess-ledger.desktop   # or just undo it
```

### The fonts matter

The journal is typeset in Playfair Display, Outfit, DM Mono and Caveat.
The installer copies them in. **Skip that step and the app still runs,
but falls back to a plain bitmap font and stops looking like itself** —
it warns you on startup when that happens. All four are SIL OFL 1.1
(`fonts/OFL-*.txt`).

### Pillow is optional

Without Pillow the photographs, doodles and paper grain are replaced by
flat colour. To get them back:

```bash
python3 -m pip install --user pillow
```

### Build a standalone binary

One file that runs on a machine with no Python:

```bash
python3 -m pip install --user pyinstaller
./build.sh
./dist/MessLedger          # double-click it
```

`--onedir` builds a folder that starts faster. `--clean` removes
`build/` and `dist/`.

---

## Your phone

The phone page is a **PWA** — a web app that installs to your home
screen and opens fullscreen with no browser bars. It talks only to your
own laptop over your home Wi-Fi. There is no cloud, no account and no
server anywhere but your machine.

### On the laptop

```bash
mess-ledger phone          # or: python3 meal_web.py
```

It prints something like:

```
Mess Ledger is on your Wi-Fi

  http://192.168.1.24:8137/?k=3f9a…

  phone: same Wi-Fi network, open the link above
  the key changes if you reinstall
```

Leave that terminal open.

### On the phone

**Both phones must be on the same Wi-Fi as the laptop.**

<details>
<summary><b>Android (Chrome)</b></summary>

1. Open the link from your laptop in Chrome
2. Menu (⋮) → **Add to Home screen** → **Install**
3. Open **Mess Ledger** from your home screen
4. Tap the tiles to log a meal
5. Anything you tap while the laptop is off is queued and sent
   automatically when it comes back

</details>

<details>
<summary><b>iPhone (Safari)</b></summary>

1. Open the link from your laptop in **Safari**
2. Tap the **Share** button (square with an arrow)
3. Scroll and tap **Add to Home Screen** → **Add**
4. Open **Mess Ledger** from your home screen
5. Tap the tiles to log a meal
6. Queued entries sync automatically when the laptop returns

</details>

### What the sync does

- Laptop → phone: whatever you log on the laptop appears on the phone
- Phone → laptop: tapping a tile writes straight to the same journal
- Laptop off: taps are queued on the phone and replayed when it returns
- Replaying is safe — a meal never gets logged twice
- The link's key is the password. Anyone who has it can log meals.

### If the phone can't connect

| Symptom | Cause |
| --- | --- |
| page won't load | different Wi-Fi — phones on mobile data can't reach a LAN address |
| "invalid key" | reinstall, or copy the whole URL including `?k=` |
| laptop IP changed | close and rerun `mess-ledger phone` for a new link |
| not offered "Install" | iOS: use **Share → Add to Home Screen**, not a bookmark |

Find your IP with `ip addr` (Linux) or `ipconfig getifaddr en0` (macOS).

### Using the phone away from home

The link above only works on your home network, because `192.168.x.x`
means nothing out in the world. **Tailscale** fixes that without putting
anything on the internet: your laptop and phone join a private network,
and the phone reaches the laptop through it as if you were both at home.

Free for personal use, and the server is still yours.

**On the laptop**

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
mess-ledger phone          # now prints a 100.x.y.z address too
```

**On the phone** — install Tailscale from the App Store or Play Store and
sign in with the same account. No `tailscale up` needed.

Open the `100.x` link, add to home screen as before, done. Works on
mobile data, on a café Wi-Fi, anywhere.

To stop: `sudo tailscale down`. Nothing is exposed while it's off.

**If you'd rather not install anything** — a phone on mobile data simply
can't reach a home LAN address. That is a limit of how the internet
works, not a bug. The phone is still useful at home, and anything
logged there syncs.

### Keep it private

The server listens on your network, not the internet. But anyone with
the link can use it — don't post it publicly, and don't port-forward
it. On shared or café Wi-Fi, stop the server when you're done
(`Ctrl-C`).

---

## Using it

### The pages

| Page | What it's for |
| --- | --- |
| **TODAY** | three rows, the allowance ring, your tree |
| **LOG / EDIT** | revisit any past date, tick what you actually ate |
| **MONTH** | one month at a time, previous and next |
| **INSIGHTS** | cycle totals, the cost thread, per-meal breakdown |

### Logging

Click a meal to eat it, click again to undo. A ticked row is eaten, a
struck row is missed, and both count toward the cycle.

Missed meals aren't punished — a journal that shames you stops being
truthful. The allowance is a plain running count.

### Keyboard

| Key | |
| --- | --- |
| `/` | jump to a date |
| `?` | keyboard sheet |
| `Esc` | close |
| `←` `→` | previous / next month (on MONTH) |

### Export

**EXPORT** on the TODAY page writes CSV and JSON to
`~/Documents/MessLedger` — one file per month, ready for a spreadsheet
or a backup.

### Settings

**SETTINGS** edits prices, tax, allowance and reminder times. They're
written to `~/.config/bhu_meal_tracker/config.ini`.

### Photos

Drop your own into `art/`:

| | |
| --- | --- |
| `art/insights.jpg` | the masthead on every page |
| `art/today.jpg` | header on TODAY |
| `art/log.jpg` | header on LOG / EDIT |
| `art/bg.jpg` | background paper |

Squares crop from the centre, so keep faces out of the centre of a wide
photo. Any `art/*.jpg` is also picked up as a possible sticker.

---

## Your data

```text
~/.local/share/bhu_meal_tracker/history.json   everything you've logged
~/.local/share/bhu_meal_tracker/backups/       a rotated copy, one per day
~/.config/bhu_meal_tracker/config.ini          your settings
~/.cache/mess-ledger/art/                      generated artwork (safe to delete)
```

Hand-edit `history.json` and the app reads it on next start. Back it up
by copying it. Nothing is stored anywhere else.

### Backups

The app keeps a copy of your journal **once a day, automatically**, in
`backups/`, and keeps 400 days of them. That is the only thing standing
between a bad write and a year of meals, and it stays on the machine.

To take one by hand:

```bash
mess-ledger backup
```

Or **Back up now** in the tray menu.

To restore, copy a file from `backups/` over `history.json`. It's plain
JSON — readable, and older copies are always there.

### Keeping a copy elsewhere

The backups are on the same disk, so they don't survive losing it. If
you want a copy off the machine, any of these is a couple of commands:

```bash
# a USB stick, whenever you plug it in
rsync -av ~/.local/share/bhu_meal_tracker/ /media/$USER/STICK/

# private cloud, encrypted at rest by the provider
rclone sync ~/.local/share/bhu_meal_tracker/backups/ gdrive:mess-ledger

# git, which is already there, one file per day
cd ~/.local/share/bhu_meal_tracker/backups && git init && git remote add origin ...
```

Copying it by hand to a USB stick once a month is a perfectly good
answer, too.

To move to another machine: copy that file across.

---

## The rules

Deliberately small, and deliberately boring:

| | |
| --- | --- |
| breakfast | 0.5 portions |
| lunch | 1 portion |
| Saturday lunch | 2 portions |
| Saturday dinner | closed |
| allowance | 25 per cycle |

The cycle runs from the 1st to the end of the month. Cost is computed
from the settings and applied at the month edge; the app never bills
you mid-month.

---

## If something's wrong

**The window is tiny and the text overlaps.** Resize it — the layout is
responsive down to about 820px wide.

**The fonts look wrong.** Fonts weren't installed: run
`./install.sh --no-launch`.

**The banner is flat colour.** Pillow isn't installed: see above.

**`No module named tkinter`.** Debian/Ubuntu:
`sudo apt install python3-tk`.

**The phone page 404s or won't install.** Rerun `mess-ledger phone` and
open the *whole* URL, key included, in the phone's browser.

**Nothing appears when I click a tile.** The phone is logged in as a
different token — open your original link again.

**Export is empty.** Exports are written for closed months. Try the
current month from MONTH.

---

## Layout

```text
meal_gui.py     desktop app, the four pages
meal_theme.py   paper, type, tally marks, tree, doodles, banner
meal_common.py  the rules, the JSON store, config, export
meal_web.py     the phone server
meal_charts.py  the insights thread
meal_app.py     tray icon
meal_watcher.py turns the tray into a log prompt
meal_reminder.py reminders
fonts/          OFL typefaces, bundled on purpose
art/            your photographs
```

Licence: your data is yours. The bundled fonts are OFL 1.1.