#!/usr/bin/env python3
"""Meal tracker GUI: TODAY, LOG / EDIT, INSIGHTS.

The Mess Ledger: a bound paper journal. Entry mastheads with margin
notes, rubber-stamp states, a ruled miss allowance, hand-drawn
margin ticks, edition numbering and page folios. All domain rules and
storage live in meal_common; this file only renders and dispatches user
actions.
"""
import random
import sys
import tkinter as tk
from calendar import monthrange
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meal_charts as charts
import meal_common as mc
import meal_theme as th

APP_TITLE = "Mess Ledger"
BAND_H = 140
DOW3 = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
GUTTER = (84, 28)  # clear of the spine + margin rule, like a real page


def rupees(v):
    return f"\u20b9{v:,.2f}"


def meal_key_chip(meal):
    return {"breakfast": "[B]", "lunch": "[L]", "dinner": "[D]"}[meal]


def cycle_edition(cs):
    """Which cycle number this is since logging began (Field Notes style)."""
    keys = sorted(mc.load_history())
    if not keys:
        return 1
    first = mc.cycle_start(datetime.strptime(keys[0], "%Y-%m-%d"))
    return max(1, (cs.year - first.year) * 12 + (cs.month - first.month)
               + 1)


def day_complete(d, e):
    """Every offered meal eaten: the leaf earns its wax seal."""
    if not e:
        return False
    if d.weekday() == 5:
        return bool(e.get("breakfast")) and bool(e.get("lunch"))
    return all(bool(e.get(m)) for m in mc.MEALS)


# ------------------------------------------------------------ meal cards
class MealCard(tk.Frame):
    """One entry melted into the paper: eyebrow, rubber stamp, ruled
    meta. Eaten entries ink the heading; the stamp does the talking."""

    def __init__(self, master, app, meal):
        super().__init__(master, bg=th.CARD, bd=0, highlightthickness=1,
                         highlightbackground=th.RULE)
        self.app = app
        self.meal = meal
        self._blocks_doodles = True
        self.date = mc.today()
        self._enabled = True

        self.body = tk.Frame(self, bg=th.CARD, bd=0, highlightthickness=0)
        self.body.pack(fill="both", expand=True, padx=4, pady=4)

        self.head = tk.Frame(self.body, bg=th.CARD)
        self.head.pack(fill="x", padx=16, pady=(14, 0))
        self.name = tk.Label(self.head, bg=th.CARD, fg=th.INK_SOFT,
                             font=th.mono(11))
        self.name.pack(side="left")
        self.key = tk.Label(self.head, bg=th.CARD, fg=th.PENCIL,
                            font=th.mono(11))
        self.key.pack(side="right")

        self.stamp = th.Stamp(self.body, height=44, bg=th.CARD)
        self.stamp.pack(anchor="w", padx=16, pady=(12, 12))

        self.rule = tk.Frame(self.body, bg=th.RULE, height=1, bd=0)
        self.rule.pack(fill="x", padx=16)

        self.foot = tk.Frame(self.body, bg=th.CARD)
        self.foot.pack(fill="x", padx=16, pady=(10, 14))
        self.meta_l = tk.Label(self.foot, bg=th.CARD, fg=th.INK_SOFT,
                               font=th.mono(12))
        self.meta_l.pack(side="left")
        self.meta_r = tk.Label(self.foot, bg=th.CARD, fg=th.INK_SOFT,
                               font=th.mono(12))
        self.meta_r.pack(side="right")

        self._widgets = [self, self.body, self.head, self.name, self.key,
                         self.stamp, self.rule, self.foot, self.meta_l,
                         self.meta_r]
        self._bind_all()

    # -- interaction ------------------------------------------------
    def _bind_all(self):
        for w in self._widgets:
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)

    def _enter(self, _e=None):
        if not self._enabled:
            return
        self.configure(highlightbackground=th.RULE_DK, cursor="hand2")
        self.name.configure(fg=th.INK)
        self.rule.configure(bg=th.RULE_DK)

    def _leave(self, _e=None):
        self.name.configure(fg=th.INK_SOFT)
        self.rule.configure(bg=th.RULE)
        self._paint()
        self.configure(cursor="")

    def _click(self, _e=None):
        if not self._enabled:
            return
        e = mc.peek_day(self.date)
        mc.toggle_meal(self.date, self.meal, not e.get(self.meal, False))
        self.app.refresh_active()
        self.pulse()

    def pulse(self):
        """Replay the stamp landing if the meal now stands eaten."""
        e = mc.peek_day(self.date)
        if bool(e.get(self.meal, False)) and self._enabled:
            self.stamp.strike()

    def _paint(self):
        e = mc.peek_day(self.date)
        eaten = bool(e.get(self.meal, False)) and self._enabled
        self.configure(highlightbackground=th.INK if eaten else th.RULE)

    # -- content ----------------------------------------------------
    def set_day(self, date):
        self.date = date
        e = mc.peek_day(date)
        is_sat = date.weekday() == 5
        eaten = bool(e.get(self.meal, False))

        title = self.meal.upper()
        if self.meal == "lunch" and is_sat:
            title += "  \u00b7  DOUBLE"
        self.name.configure(text=title)
        self.key.configure(text=meal_key_chip(self.meal),
                           fg=th.INK if eaten else th.PENCIL)

        if self.meal == "dinner" and is_sat:
            self._enabled = False
            self.stamp.set("KITCHEN CLOSED", "closed")
            if self.app.detail_mode:
                self.meta_l.configure(text="0.0 / 0.0", fg=th.PENCIL)
            else:
                self.meta_l.configure(text="0.0 meal", fg=th.PENCIL)
            self.meta_r.configure(text=rupees(0), fg=th.PENCIL)
        else:
            self._enabled = True
            self.stamp.set("EATEN" if eaten else "NOT EATEN",
                           "eaten" if eaten else "pending")
            v = mc.meal_value(self.meal, date)
            n = mc.servings(self.meal, date)
            unit = mc.unit_price(self.meal)
            if self.app.detail_mode:
                got = v if eaten else 0.0
                self.meta_l.configure(text=f"{got:g} / {v:g}",
                                      fg=th.INK if eaten else th.INK_SOFT)
                self.meta_r.configure(
                    text=rupees(unit * n) if eaten else rupees(0),
                    fg=th.INK if eaten else th.INK_SOFT)
            else:
                note = "  \u00b7  Double" if v == 2.0 else ""
                self.meta_l.configure(
                    text=f"{v:.1f} meal{'s' if v > 1 else ''}{note}",
                    fg=th.INK if eaten else th.INK_SOFT)
                self.meta_r.configure(text=rupees(unit * n),
                                      fg=th.INK if eaten else th.INK_SOFT)
        self._paint()


class CardRow(tk.Frame):
    """The three entry sheets shared by TODAY and LOG / EDIT."""

    def __init__(self, master, app):
        super().__init__(master, bg=th.PAPER)
        self.cards = {}
        for i, meal in enumerate(mc.MEALS):
            self.columnconfigure(i, weight=1, uniform="card")
            card = MealCard(self, app, meal)
            card.grid(row=0, column=i, sticky="nsew",
                      padx=(0, 16) if i < 2 else 0)
            self.cards[meal] = card
        self.rowconfigure(0, weight=1)

    def set_day(self, date):
        for card in self.cards.values():
            card.set_day(date)


# ----------------------------------------------------------------- app
def _parse_date(raw):
    """Accept 11, 11/10 or 2026-10-11 and return a datetime, or None."""
    now = mc.today()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m", "%d"):
        try:
            got = datetime.strptime(raw, fmt)
        except ValueError:
            continue
        if fmt == "%d":
            return now.replace(day=int(raw), hour=0, minute=0, second=0,
                                microsecond=0)
        if fmt == "%d/%m":
            return now.replace(year=now.year, month=int(raw.split("/")[1]),
                               day=int(raw.split("/")[0]), hour=0, minute=0,
                               second=0, microsecond=0)
        return got
    return None


DOODLE_KINDS = ["tangerine", "lemon", "slice", "sprig", "wheat", "leaf",
                "chili", "star", "daisy", "butterfly", "bee", "cloud",
                "sun", "bird", "heart", "bow", "tape", "stamp"]


def _overlaps(a, b, pad=0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0]
                or a[3] + pad <= b[1] or b[3] + pad <= a[1])



class SettingsSheet(tk.Toplevel):
    """Prices, timings and the miss allowance, edited in place.

    Writes back through meal_common.save_config, so the file stays the
    single source of truth and hand-added keys survive."""

    FIELDS = [
        ("price_breakfast", "Price per breakfast", float, "0.01"),
        ("price_lunch", "Price per lunch", float, "0.01"),
        ("price_dinner", "Price per dinner", float, "0.01"),
        ("tax_percent", "Tax percent", float, "0.1"),
        ("allowed_misses_per_month", "Misses allowed per cycle", int, "1"),
        ("nag_until", "Nightly nudge at (HH:MM)", str, None),
        ("poll_interval_minutes", "Reminder poll (minutes)", int, "1"),
        ("notification_timeout_seconds", "Reminder timeout (s)", int, "1"),
    ]
    TOGGLES = [
        ("remind_breakfast", "Remind me at breakfast"),
        ("remind_lunch", "Remind me at lunch"),
        ("remind_dinner", "Remind me at dinner"),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Mess Ledger \u2014 Settings")
        self.configure(bg=th.PAPER)
        self.transient(app)
        self.vars = {}
        cfg = mc.load_config()
        outer = tk.Frame(self, bg=th.PAPER, padx=26, pady=20)
        outer.pack(fill="both", expand=True)
        tk.Label(outer, text="SETTINGS", bg=th.PAPER, fg=th.INK,
                 font=th.display(18)).pack(anchor="w", pady=(0, 4))
        tk.Label(outer, text=f"stored in {mc.CONFIG_DIR / 'config.ini'}",
                 bg=th.PAPER, fg=th.PENCIL, font=th.mono(9)).pack(
                     anchor="w", pady=(0, 16))

        grid = tk.Frame(outer, bg=th.PAPER)
        grid.pack(fill="x")
        for row, (key, label, kind, step) in enumerate(self.FIELDS):
            tk.Label(grid, text=label, bg=th.PAPER, fg=th.INK_SOFT,
                     font=th.body(11)).grid(row=row, column=0, sticky="w",
                                            pady=5, padx=(0, 14))
            var = tk.StringVar(value=str(cfg.get(key)))
            self.vars[key] = (var, kind)
            entry = tk.Entry(grid, textvariable=var, width=12,
                             bg=th.CARD_HI, fg=th.INK, font=th.mono(12),
                             justify="right", relief="flat", bd=0,
                             highlightthickness=1,
                             highlightbackground=th.RULE_DK)
            entry.grid(row=row, column=1, sticky="e", pady=5)
            if step:
                tk.Label(grid, text=step, bg=th.PAPER, fg=th.PENCIL_LT,
                         font=th.mono(9)).grid(row=row, column=2, sticky="w",
                                               padx=(8, 0))

        base = len(self.FIELDS) + 1
        for i, (key, label) in enumerate(self.TOGGLES):
            var = tk.BooleanVar(value=bool(cfg.get(key)))
            self.vars[key] = (var, bool)
            cb = tk.Checkbutton(grid, text=label, variable=var,
                                bg=th.PAPER, fg=th.INK_SOFT,
                                font=th.body(11), anchor="w",
                                highlightthickness=0, bd=0,
                                selectcolor=th.CARD_HI,
                                activebackground=th.PAPER,
                                activeforeground=th.INK_SOFT)
            cb.grid(row=base + i, column=0, columnspan=2, sticky="w",
                    pady=5)

        self.msg = tk.Label(outer, text="", bg=th.PAPER, fg=th.STAMP,
                            font=th.mono(10), anchor="w")
        self.msg.pack(fill="x", pady=(14, 0))
        bar = tk.Frame(outer, bg=th.PAPER)
        bar.pack(fill="x", pady=(10, 0))
        th.RoundedButton(bar, "CANCEL", self.destroy,
                      kind="ghost").pack(side="right")
        th.RoundedButton(bar, "SAVE", self._save,
                      kind="primary").pack(side="right", padx=(0, 10))
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._save())

    def _save(self):
        out = {}
        for key, (var, kind) in self.vars.items():
            raw = var.get()
            if kind is bool:
                out[key] = bool(raw)
                continue
            raw = str(raw).strip()
            try:
                if kind is int:
                    out[key] = int(raw)
                elif kind is float:
                    out[key] = float(raw)
                else:
                    out[key] = raw
            except (TypeError, ValueError):
                self.msg.configure(text=f"{key}: {raw!r} is not valid")
                return
        try:
            mc.save_config(out)
        except Exception as exc:
            self.msg.configure(text=f"could not save: {exc}")
            return
        self.app.refresh_all()
        self.app.flash("settings saved")
        self.destroy()


class MealApp(tk.Tk):
    def __init__(self):
        super().__init__(className="FoodJournal")
        self.title(APP_TITLE)
        self.configure(bg=th.PAPER)
        try:
            _ic = tk.PhotoImage(
                file=str(Path(__file__).resolve().parent / "icons" /
                         "hicolor" / "48x48" / "apps" / "food-journal.png"))
            self.iconphoto(True, _ic)
            self._icon_ref = _ic
        except Exception:
            pass
        th.init_theme(self)
        self.detail_mode = False
        self.log_date = mc.today()
        self.active_view = "TODAY"
        self._fit_to_screen()

        self.paper = th.PaperCanvas(self, photo=th.art("bg.jpg",
                                                               "today.jpg"),
                                    wash=0.14)
        self.paper.pack(fill="both", expand=True)
        self.paper.bind("<Configure>", self._schedule_scatter)

        self._build()
        self.bind("<Key-b>", lambda e: self._key_meal("breakfast"))
        self.bind("<Key-l>", lambda e: self._key_meal("lunch"))
        self.bind("<Key-d>", lambda e: self._key_meal("dinner"))
        self.bind("<Key-B>", lambda e: self._key_meal("breakfast"))
        self.bind("<Key-L>", lambda e: self._key_meal("lunch"))
        self.bind("<Key-D>", lambda e: self._key_meal("dinner"))
        self.bind("<Left>", lambda e: self._key_step(-1))
        self.bind("<Right>", lambda e: self._key_step(1))
        self.bind("<slash>", lambda e: self._prompt_date())
        self.bind("<question>", lambda e: self._open_help())
        self.bind("<Escape>", lambda e: self._close_sheets())
        self.refresh_all()
        self._schedule_scatter()

    # ------------------------------------------------------------ layout
    def _fit_to_screen(self):
        try:
            sw = max(640, self.winfo_screenwidth())
            sh = max(480, self.winfo_screenheight())
        except Exception:
            sw, sh = 1280, 800
        w = max(780, min(1240, int(sw * 0.94)))
        # use the height the screen actually offers: the masthead, the
        # cards and the week strip all need vertical room, and TODAY
        # needs what is left over for its doodle band
        h = max(700, min(960, int(sh * 0.92)))
        x = max(0, (sw - w) // 2)
        y = max(0, min(40, (sh - h) // 8))
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(min(780, w), min(700, h))

    def _build(self):
        # -- header: ledger brand left, mono tabs right, double rule
        head = tk.Frame(self.paper, bg=th.PAPER)
        head.pack(fill="x", padx=GUTTER, pady=(18, 0))
        brand = tk.Label(head, text=APP_TITLE, bg=th.PAPER, fg=th.INK,
                         font=th.display(16))
        try:
            _logo = tk.PhotoImage(
                file=str(Path(__file__).resolve().parent / "icons" /
                         "hicolor" / "32x32" / "apps" / "food-journal.png"))
            mark = tk.Label(head, image=_logo, bg=th.PAPER, bd=0)
            mark.pack(side="left", padx=(0, 10))
            self._logo_ref = _logo
        except Exception:
            pass
        brand.pack(side="left")
        tabs = tk.Frame(head, bg=th.PAPER)
        tabs.pack(side="right")
        self.tab_ui = {}
        for name in ("TODAY", "LOG / EDIT", "MONTH", "INSIGHTS"):
            holder = tk.Frame(tabs, bg=th.PAPER)
            lbl = tk.Label(holder, text=name, bg=th.PAPER, fg=th.PENCIL,
                           font=th.mono(10), padx=12, pady=8,
                           cursor="hand2")
            lbl.pack()
            underline = tk.Frame(holder, bg=th.PAPER, height=2)
            underline.pack(fill="x")
            holder.pack(side="left", padx=(18, 0))
            for w in (holder, lbl):
                w.bind("<Button-1>", lambda e, n=name: self._show(n))
            for w in (holder, lbl):
                w.bind("<Enter>", lambda e, n=name: self._tab_hover(n))
                w.bind("<Leave>", lambda e, n=name: self._tab_leave(n))
            self.tab_ui[name] = (holder, lbl, underline)
        th.double_rule(self.paper, pady=4)

        # -- full-bleed photographic mastheads, one per view
        _sky = th.art("insights.jpg", "log.jpg", "bg.jpg")
        self.banners = {
            name: th.PhotoBanner(self.paper, height=BAND_H, photo=_sky,
                                 anchor=0.80)
            for name in ("TODAY", "LOG / EDIT", "MONTH", "INSIGHTS")
        }

        # -- views
        self.views = {}
        for name, builder in (("TODAY", self._build_today),
                              ("LOG / EDIT", self._build_log),
                              ("MONTH", self._build_month),
                              ("INSIGHTS", self._build_insights)):
            frame = tk.Frame(self.paper, bg=th.PAPER)
            builder(frame)
            self.views[name] = frame

        # -- colophon footer pinned to the bottom
        foot = tk.Frame(self.paper, bg=th.PAPER)
        foot.pack(fill="x", side="bottom", padx=GUTTER, pady=(10, 14))
        th.hline(foot, pady=(0, 8))
        frow = tk.Frame(foot, bg=th.PAPER)
        frow.pack(fill="x")
        self.footer_left = tk.Label(frow, bg=th.PAPER, fg=th.INK_SOFT,
                                    font=th.mono(10))
        self.footer_left.pack(side="left")
        self.footer_right = tk.Label(frow, bg=th.PAPER, fg=th.PENCIL,
                                     font=th.mono(10))
        self.footer_right.pack(side="right")
        btns = tk.Frame(frow, bg=th.PAPER)
        btns.pack(side="right", padx=(0, 16))
        th.RoundedButton(btns, "SETTINGS", self._open_settings,
                      kind="ghost").pack(side="left", padx=(8, 0))
        th.RoundedButton(btns, "EXPORT", self._do_export,
                      kind="ghost").pack(side="left")

        self._show("TODAY")
        if len(sys.argv) > 1 and sys.argv[1].lower().startswith("log"):
            self._show("LOG / EDIT")
        elif len(sys.argv) > 1 and sys.argv[1].lower().startswith("ins"):
            self._show("INSIGHTS")

    # ---------------------------------------------------- doodle scatter
    def _content_rects(self, widget, out, origin=None):
        """Rects of real content under `widget`, ignoring our own doodles.

        Every rect is measured against the top-level page origin, not the
        immediate parent, so nested cards land where they really are.
        Doodles are excluded so they never treat each other as content,
        which would make re-scattering impossible."""
        if origin is None:
            origin = (widget.winfo_rootx(), widget.winfo_rooty())
        for child in widget.winfo_children():
            try:
                if not child.winfo_ismapped():
                    continue
                x = child.winfo_rootx() - origin[0]
                y = child.winfo_rooty() - origin[1]
                w, h = child.winfo_width(), child.winfo_height()
            except Exception:
                continue
            if w <= 1 or h <= 1:
                continue
            if isinstance(child, th.Doodle) or \
                    getattr(child, "_doodle_zone", False):
                continue
            if isinstance(child, (th.ScrollFrame, th.PaperCanvas)):
                out.append((x, y, x + w, y + h))
                continue
            kids = child.winfo_children()
            container = (kids and isinstance(child, tk.Frame)
                         and not isinstance(child, (tk.Canvas, tk.Label)))
            if not container or getattr(child, "_blocks_doodles", False):
                out.append((x, y, x + w, y + h))
            if kids:
                self._content_rects(child, out, origin)
        return out

    @staticmethod
    def _largest_free_rect(blocked, w, h, cell=12, pad=8):
        """Biggest all-empty rectangle on the page, as (x, y, w, h).

        Content is rasterised into a coarse grid and a histogram scan
        finds the largest run of untouched cells, so a doodle can only
        ever land on paper nothing else is using."""
        cols, rows = max(1, w // cell), max(1, h // cell)
        padded = [(x0 - pad, y0 - pad, x1 + pad, y1 + pad)
                  for (x0, y0, x1, y1) in blocked]
        occ = []
        for r in range(rows):
            cy = r * cell
            row = []
            for c in range(cols):
                cx = c * cell
                row.append(any(not (cx + cell <= b[0] or b[2] <= cx
                                    or cy + cell <= b[1] or b[3] <= cy)
                               for b in padded))
            occ.append(row)
        best = (0, 0, 0, 0, 0)
        heights = [0] * cols
        for r in range(rows):
            for c in range(cols):
                heights[c] = 0 if occ[r][c] else heights[c] + 1
            stack = []
            for c in range(cols + 1):
                cur = heights[c] if c < cols else 0
                start = c
                while stack and stack[-1][1] > cur:
                    idx, hgt = stack.pop()
                    area = hgt * (c - idx)
                    if area > best[0]:
                        best = (area, r - hgt + 1, idx, hgt, c - idx)
                    start = idx
                stack.append((start, cur))
        area, r0, c0, rh, rw = best
        return None if area <= 0 else (c0 * cell, r0 * cell,
                                       rw * cell, rh * cell)

    def _scatter_doodles(self, container, count=6, smin=44, smax=76,
                         gap=20, min_h=40):
        """Place doodles on an even grid inside the page's emptiest patch.

        Returns (placed, widgets). The grid gives even spacing for free and
        the free-rectangle search keeps every doodle off real content."""
        try:
            container.update_idletasks()
            w, h = container.winfo_width(), container.winfo_height()
        except Exception:
            return 0, []
        if w < 140 or h < min_h:
            return 0, []

        space = self._largest_free_rect(
            self._content_rects(container, []), w, h)
        if space is None:
            return 0, []
        fx, fy, fw, fh = space
        if fw < smin or fh < smin:
            return 0, []

        max_cols = max(1, int(fw // (smin + gap)))
        max_rows = max(1, int(fh // (smin + gap)))
        grid = None
        for rows in range(1, max_rows + 1):
            cols = -(-count // rows)
            if cols > max_cols:
                continue
            cell_w, cell_h = fw / cols, fh / rows
            cap = min(smax, int(min(cell_w, cell_h)) - gap)
            if cap < smin:
                continue
            fill = count / float(cols * rows)
            if grid is None or fill > grid[0]:
                grid = (fill, cols, rows, cap)
        if grid is None:
            return 0, []
        _, cols, rows, cap = grid
        cell_w, cell_h = fw / cols, fh / rows

        cells = [(c, r) for r in range(rows) for c in range(cols)]
        random.shuffle(cells)
        kinds = random.sample(DOODLE_KINDS, min(count, len(DOODLE_KINDS)))
        made, widgets = 0, []
        for c, r in cells:
            if made >= count:
                break
            size = random.randint(smin, cap)
            jx = random.uniform(-0.22, 0.22) * (cell_w - size)
            jy = random.uniform(-0.22, 0.22) * (cell_h - size)
            x = fx + c * cell_w + (cell_w - size) / 2 + jx
            y = fy + r * cell_h + (cell_h - size) / 2 + jy
            widget = th.Doodle(container, doodle=kinds[made], size=size)
            widget.place(x=int(x), y=int(y))
            widgets.append(widget)
            made += 1
        return made, widgets

    def _doodles_clear(self, page, widgets):
        """True when nothing we drew is sitting on top of real content."""
        if not widgets:
            return True
        content = self._content_rects(page, [])
        for d in widgets:
            try:
                if not d.winfo_ismapped():
                    continue
                x, y = d.winfo_rootx() - page.winfo_rootx(), \
                    d.winfo_rooty() - page.winfo_rooty()
                box = (x, y, x + d.winfo_width(), y + d.winfo_height())
            except Exception:
                return False
            if any(_overlaps(box, c, 6) for c in content):
                return False
        return True

    def _tab_hover(self, name):
        if name != self.active_view:
            self.tab_ui[name][1].configure(fg=th.INK)

    def _tab_leave(self, name):
        if name != self.active_view:
            self.tab_ui[name][1].configure(fg=th.PENCIL)

    def _show(self, name):
        self.active_view = name
        for n, f in self.views.items():
            if n == name:
                f.pack(fill="both", expand=True, padx=GUTTER, pady=(24, 0))
            else:
                f.pack_forget()
        for n, b in self.banners.items():
            if n == name:
                b.pack(fill="x", padx=GUTTER, before=self.views[name])
            else:
                b.pack_forget()
        for n, (holder, lbl, underline) in self.tab_ui.items():
            active = n == name
            lbl.configure(fg=th.INK if active else th.PENCIL)
            underline.configure(bg=th.STAMP if active else th.PAPER)
        self.detail_mode = (name == "LOG / EDIT")
        self.refresh_active()
        self._doodled = set()
        self._schedule_scatter()

    def _schedule_scatter(self, _event=None):
        """Drop doodles as soon as the view has real geometry.

        Driven by <Configure> rather than an after() timer: re-registering
        a live Tcl command on every tab switch races with itself. A resize
        invalidates the scatter, since the paper it was placed on moved."""
        size = (self.paper.winfo_width(), self.paper.winfo_height())
        if size != getattr(self, "_page_size", None):
            self._page_size = size
            self._doodled = set()
        self._scatter_view()

    def _kicker(self, prefix, text):
        """Show a kicker only when it carries something the title and the
        section's position do not already say, and never leave a gap."""
        lbl = getattr(self, prefix + "_eb")
        text = text or ""
        lbl.configure(text=text)
        if text:
            if not lbl.winfo_ismapped():
                lbl.pack(anchor="w")
        elif lbl.winfo_ismapped():
            lbl.pack_forget()

    def _masthead(self, parent, prefix):
        """Paper title block under the banner: eyebrow, Playfair date,
        hand note left; folio right."""
        mast = tk.Frame(parent, bg=th.PAPER)
        mast.pack(fill="x", pady=(2, 0))
        left = tk.Frame(mast, bg=th.PAPER)
        left.pack(side="left")
        eb = th.eyebrow(left, "")
        eb.pack(anchor="w")
        date = tk.Label(left, bg=th.PAPER, fg=th.INK, font=th.display(25),
                        anchor="w")
        date.pack(anchor="w", pady=(8, 5))
        note = tk.Label(left, bg=th.PAPER, fg=th.INK_SOFT, font=th.hand(16),
                        anchor="w")
        note.pack(anchor="w", pady=(0, 0))
        folio = tk.Label(mast, bg=th.PAPER, fg=th.PENCIL, font=th.mono(12))
        folio.pack(side="right")
        setattr(self, prefix + "_eb", eb)
        setattr(self, prefix + "_date", date)
        setattr(self, prefix + "_note", note)
        setattr(self, prefix + "_folio", folio)
        setattr(self, prefix + "_mast", mast)
        return mast

    # ------------------------------------------------------------ TODAY
    def _build_today(self, parent):
        self._masthead(parent, "today")
        self.today_cards = CardRow(parent, self)
        self.today_cards.pack(fill="x")

        row = tk.Frame(parent, bg=th.PAPER)
        row.pack(fill="x", pady=(12, 0))
        self.today_sum = tk.Label(row, bg=th.PAPER, fg=th.INK,
                                  font=th.mono(11))
        self.today_sum.pack(side="left")
        th.RoundedButton(row, "CLEAR", lambda: self._set_all_today(False),
                      kind="ghost").pack(side="right", padx=(10, 0))
        th.RoundedButton(row, "MARK ALL EATEN",
                      lambda: self._set_all_today(True),
                      kind="primary").pack(side="right")

        self.week = th.WeekStrip(parent, bg=th.PAPER,
                                 on_pick=self._week_pick)
        self.week.pack(fill="x", pady=(14, 0))

        # scrapbook void: pure empty paper for the doodles
        self.void = tk.Frame(parent, bg=th.PAPER)
        self.void._doodle_zone = True
        self.void.pack(fill="both", expand=True, pady=(14, 0))

    def _do_export(self):
        """Write the whole ledger to ~/Documents/MessLedger."""
        try:
            files = mc.export_history("both")
            where = files[0].parent if files else mc.export_dir()
            self.flash(f"exported {len(files)} files \u00b7 {where}")
        except Exception as exc:
            self.flash(f"export failed: {exc}", bad=True)

    def flash(self, text, bad=False, ms=6000):
        """Show a short-lived note in the footer."""
        self.footer_left.configure(text=text, fg=th.STAMP if bad
                                  else th.INK_SOFT)
        prev = getattr(self, "_flash_job", None)
        if prev is not None:
            try:
                self.after_cancel(prev)
            except Exception:
                pass
        self._flash_job = self.after(ms, self._flash_clear)

    def _flash_clear(self):
        self._flash_job = None
        self.refresh_chrome()

    def _open_settings(self):
        SettingsSheet(self)

    def _week_pick(self, day):
        """Click a stamp in the week strip to edit that day."""
        self.log_date = day
        self._show("LOG / EDIT")

    def _week_data(self, now):
        """This week Monday to Sunday, with meals eaten vs expected."""
        start = now - timedelta(days=now.weekday())
        out = []
        for i in range(7):
            day = start + timedelta(days=i)
            e = mc.peek_day(day) if day <= now else {}
            eaten = sum(mc.meal_value(m, day) for m in mc.MEALS
                        if e and e.get(m))
            expected = sum(mc.meal_value(m, day) for m in mc.MEALS)
            out.append((day, eaten, expected, day > now))
        return out

    def _set_all_today(self, value):
        now = mc.today()
        for meal in mc.MEALS:
            if meal == "dinner" and now.weekday() == 5:
                continue
            mc.toggle_meal(now, meal, value)
        self.refresh_active()
        if value:
            for card in self.today_cards.cards.values():
                card.pulse()

    # ---------------------------------------------------------- LOG/EDIT
    def _build_log(self, parent):
        self._masthead(parent, "logm")
        nav = tk.Frame(parent, bg=th.PAPER)
        nav.pack(fill="x", pady=(0, 16))
        th.RoundedButton(nav, "< YESTERDAY", lambda: self._step(-1),
                      kind="ghost").pack(side="left")
        self.log_title = tk.Label(nav, bg=th.PAPER, fg=th.INK_SOFT,
                                  font=th.mono(11))
        self.log_title.pack(side="left", expand=True)
        th.RoundedButton(nav, "TOMORROW >", lambda: self._step(1),
                      kind="ghost").pack(side="right")

        self.log_cards = CardRow(parent, self)
        self.log_cards.pack(fill="x")
        sumrow = tk.Frame(parent, bg=th.PAPER)
        sumrow.pack(fill="x", pady=(14, 0))
        self.log_sealrow = sumrow
        self.log_seal = th.Seal(sumrow, bg=th.PAPER)
        self.log_seal.pack(side="left")

        th.hline(parent, pady=(18, 0))
        head = tk.Frame(parent, bg=th.PAPER)
        head.pack(fill="x", pady=(10, 8))
        self.log_hist_title = tk.Label(head, bg=th.PAPER, fg=th.PENCIL,
                                       font=th.mono(10))
        self.log_hist_title.pack(side="left")
        th.RoundedButton(head, "JUMP TO TODAY", self._jump_today,
                      kind="ghost").pack(side="right")

        self.hist_scroll = th.ScrollFrame(parent, bg=th.PAPER)
        self.hist_scroll.pack(fill="both", expand=True)
        self.hist_inner = self.hist_scroll.inner
        self.hist_preview = tk.Label(self, text="", justify="left", anchor="w",
                                     bg=th.CARD_HI, fg=th.INK_SOFT,
                                     font=th.mono(10), bd=1,
                                     relief="flat",
                                     highlightthickness=1,
                                     highlightbackground=th.RULE_DK,
                                     padx=8, pady=5)
        self.hist_thread = th.TimelineGutter(self.hist_inner, bg=th.PAPER)
        self.hist_thread.pack(side="left", fill="y")
        self.hist_list = tk.Frame(self.hist_inner, bg=th.PAPER)
        self.hist_list.pack(side="left", fill="x", expand=True)
        self._hist_rows = {}
        self._hist_keys = []
        self._hist_div = None

    # ------------------------------------------------------------ MONTH
    def _build_month(self, parent):
        self._masthead(parent, "mon")
        nav = tk.Frame(parent, bg=th.PAPER)
        nav.pack(fill="x", pady=(0, 14))
        th.RoundedButton(nav, "< EARLIER", lambda: self._month_step(-1),
                      kind="ghost").pack(side="left")
        self.month_title = tk.Label(nav, bg=th.PAPER, fg=th.INK_SOFT,
                                    font=th.mono(12))
        self.month_title.pack(side="left", expand=True)
        th.RoundedButton(nav, "LATER >", lambda: self._month_step(1),
                      kind="ghost").pack(side="right")
        self.month_grid = th.MonthGrid(parent, bg=th.PAPER,
                                       on_pick=self._month_pick)
        self.month_grid.pack(fill="both", expand=True)
        self.month_note = tk.Label(parent, bg=th.PAPER, fg=th.PENCIL,
                                   font=th.mono(10), anchor="w")
        self.month_note.pack(fill="x", pady=(12, 0))
        self._month_cursor = mc.today().replace(day=1)

    def _month_step(self, delta):
        d = self._month_cursor
        month = d.month - 1 + delta
        year = d.year + (month - 1) // 12
        self._month_cursor = d.replace(year=year,
                                       month=(month - 1) % 12 + 1, day=1)
        self.refresh_month()

    def _month_pick(self, day):
        self.log_date = day
        self._show("LOG / EDIT")

    def refresh_month(self):
        now = mc.today()
        cur = self._month_cursor
        days_in = monthrange(cur.year, cur.month)[1]
        first = cur.replace(day=1)
        lead = first.weekday()
        cells, ticks = [], []
        for i in range(lead + days_in):
            d = first + timedelta(days=i - lead)
            e = mc.peek_day(d) if d <= now else {}
            eaten = sum(mc.meal_value(m, d) for m in mc.MEALS
                        if e and e.get(m))
            expected = sum(mc.meal_value(m, d) for m in mc.MEALS)
            cells.append((d, eaten, expected))
            marks = {}
            for m in mc.MEALS:
                if mc.meal_value(m, d) <= 0:
                    marks[m] = "closed"
                else:
                    marks[m] = bool(e.get(m))
            ticks.append((d, marks))
        self.month_grid.set_month(cells, today=now, ticks=ticks)
        self.month_title.configure(
            text=cur.strftime("%B %Y").upper())
        self._kicker("mon", "")
        self.mon_date.configure(text=cur.strftime("%B %Y"))
        logged = sum(1 for d, en, ex in cells if en > 0)
        self.mon_note.configure(
            text=(f"{logged} of {days_in} days logged  \u00b7  "
                  f"each cell rules B L D: ticked when eaten, struck "
                  f"when missed, a dash when not offered"))
        self.mon_folio.configure(text=f"p. {(now - mc.cycle_start(now)).days + 1:02d}")

    def _step(self, delta):
        self.log_date += timedelta(days=delta)
        self.refresh_active()

    def _jump_today(self):
        self.log_date = mc.today()
        self.refresh_active()

    def _key_meal(self, meal):
        if self.active_view == "TODAY":
            d = mc.today()
        elif self.active_view == "LOG / EDIT":
            d = self.log_date
        else:
            return
        if meal == "dinner" and d.weekday() == 5:
            return
        e = mc.peek_day(d)
        mc.toggle_meal(d, meal, not e.get(meal, False))
        self.refresh_active()
        cards = (self.today_cards if self.active_view == "TODAY"
                 else self.log_cards).cards.get(meal)
        if cards is not None:
            cards.pulse()

    def _key_step(self, delta):
        if self.active_view == "LOG / EDIT":
            self._step(delta)
        elif self.active_view == "MONTH":
            self._month_step(delta)

    # ------------------------------------------------- keyboard helpers
    def _close_sheets(self):
        for name in ("_jump_win", "_help_win"):
            w = getattr(self, name, None)
            if w is not None and w.winfo_exists():
                try:
                    w.destroy()
                except Exception:
                    pass
                setattr(self, name, None)

    def _prompt_date(self):
        """Jump to a date: accepts 11, 11/10 or 2026-10-11."""
        old = getattr(self, "_jump_win", None)
        if old is not None and old.winfo_exists():
            old.destroy()
        win = tk.Toplevel(self)
        self._jump_win = win
        win.title("Go to date")
        win.configure(bg=th.PAPER)
        win.transient(self)
        win.resizable(False, False)
        tk.Label(win, text="GO TO DATE", bg=th.PAPER, fg=th.INK,
                 font=th.display(15), padx=22, pady=18).pack(anchor="w")
        tk.Label(win, text="day  ·  day/month  ·  yyyy-mm-dd",
                 bg=th.PAPER, fg=th.PENCIL, font=th.mono(9),
                 padx=22).pack(anchor="w")
        var = tk.StringVar()
        entry = tk.Entry(win, textvariable=var, width=18, font=th.mono(14),
                         bg=th.CARD_HI, fg=th.INK, justify="center",
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=th.RULE_DK)
        entry.pack(padx=22, pady=(12, 4), ipady=4)
        msg = tk.Label(win, text="", bg=th.PAPER, fg=th.STAMP,
                       font=th.mono(10))
        msg.pack(anchor="w", padx=22)

        def go(*_a):
            raw = var.get().strip()
            if not raw:
                return
            day = _parse_date(raw)
            if day is None:
                msg.configure(text="could not read that date")
                return
            self.log_date = day
            self._show("LOG / EDIT")
            win.destroy()
            self._jump_win = None

        bar = tk.Frame(win, bg=th.PAPER)
        bar.pack(fill="x", padx=22, pady=(12, 18))
        th.RoundedButton(bar, "CANCEL", win.destroy, kind="ghost").pack(
            side="right")
        th.RoundedButton(bar, "GO", go, kind="primary").pack(
            side="right", padx=(0, 8))
        entry.focus_set()
        entry.bind("<Return>", go)
        win.bind("<Escape>", lambda e: (win.destroy(),
                                        setattr(self, "_jump_win", None)))

    HELP = [
        ("TODAY", "stamp the meals for today"),
        ("LOG / EDIT", "edit any single day"),
        ("MONTH", "the month almanac"),
        ("INSIGHTS", "cycle stats and charts"),
        ("", ""),
        ("B  /  L  /  D", "toggle breakfast, lunch, dinner"),
        ("Left / Right", "previous or next day (or month)"),
        ("/", "jump to a date"),
        ("?", "this sheet"),
        ("Esc", "close a sheet"),
    ]

    def _open_help(self):
        old = getattr(self, "_help_win", None)
        if old is not None and old.winfo_exists():
            old.destroy()
        win = tk.Toplevel(self)
        self._help_win = win
        win.title("Keyboard")
        win.configure(bg=th.PAPER)
        win.transient(self)
        win.resizable(False, False)
        tk.Label(win, text="KEYS", bg=th.PAPER, fg=th.INK,
                 font=th.display(18), padx=26, pady=20).pack(anchor="w")
        body = tk.Frame(win, bg=th.PAPER, padx=26)
        body.pack(fill="both", expand=True)
        for i, (key, what) in enumerate(self.HELP):
            if not key:
                tk.Frame(body, bg=th.PAPER, height=8).grid(
                    row=i, column=0, columnspan=2)
                continue
            tk.Label(body, text=key, bg=th.PAPER, fg=th.INK,
                     font=th.mono(11), anchor="w", width=14).grid(
                         row=i, column=0, sticky="w", pady=3)
            tk.Label(body, text=what, bg=th.PAPER, fg=th.INK_SOFT,
                     font=th.body(11), anchor="w").grid(
                         row=i, column=1, sticky="w", pady=3)
        th.RoundedButton(win, "CLOSE", win.destroy,
                      kind="ghost").pack(pady=(14, 20))
        win.bind("<Escape>", lambda e: (win.destroy(),
                                        setattr(self, "_help_win", None)))

    # ---------------------------------------------------------- INSIGHTS
    def _build_insights(self, parent):
        self.ins_scroll = th.ScrollFrame(parent, bg=th.PAPER)
        self.ins_scroll.pack(fill="both", expand=True)
        body = tk.Frame(self.ins_scroll.inner, bg=th.PAPER)
        body.pack(fill="both", expand=True)
        self.ins_body = body

        self._masthead(body, "ins")
        allow_head = tk.Label(body, bg=th.PAPER, fg=th.PENCIL,
                              font=th.mono(10))
        allow_head.pack(anchor="w", pady=(6, 2))
        self.ins_allow_head = allow_head
        arow = tk.Frame(body, bg=th.PAPER)
        arow.pack(fill="x", pady=(6, 2))
        self.ins_allowrow = arow
        self.ins_allow_left = tk.Label(arow, bg=th.PAPER, fg=th.INK,
                                       font=th.display(16))
        self.ins_allow_left.pack(side="left")
        self.ins_allow_right = tk.Label(arow, bg=th.PAPER, fg=th.INK_SOFT,
                                        font=th.mono(11))
        self.ins_allow_right.pack(side="right")
        self.allowance = th.AllowanceBox(body, bg=th.PAPER)
        self.allowance.pack(fill="x", pady=(4, 6))
        self.ins_b1 = tk.Label(body, bg=th.PAPER, fg=th.INK_SOFT,
                               font=th.mono(11))
        self.ins_b1.pack(anchor="w")
        self.ins_b2 = tk.Label(body, bg=th.PAPER, fg=th.INK_SOFT,
                               font=th.mono(11))
        self.ins_b2.pack(anchor="w")

        th.hline(body, pady=(20, 14))
        bh = tk.Frame(body, bg=th.PAPER)
        bh.pack(fill="x", pady=(0, 6))
        tk.Label(bh, text="WHICH MEALS GET SKIPPED", bg=th.PAPER,
                 fg=th.PENCIL, font=th.mono(10)).pack(side="left")
        self.ins_break_head = tk.Label(bh, bg=th.PAPER, fg=th.PENCIL,
                                       font=th.mono(10))
        self.ins_break_head.pack(side="right")
        self.ins_break = th.MealBreakdown(body, bg=th.PAPER)
        self.ins_break.pack(fill="x")

        th.hline(body, pady=(20, 20))
        brow2 = tk.Frame(body, bg=th.PAPER)
        brow2.pack(fill="x", pady=(0, 8))
        bill_head = tk.Label(brow2, text="CYCLE BILL", bg=th.PAPER,
                             fg=th.PENCIL, font=th.mono(10))
        bill_head.pack(side="left")
        _med = th.art("today.jpg", "bg.jpg")
        if _med:
            th.Medallion(brow2, photo=_med, size=84).pack(side="right")
        trow = tk.Frame(body, bg=th.PAPER)
        trow.pack(fill="x")
        tk.Label(trow, text="Total liability to date", bg=th.PAPER,
                 fg=th.INK_SOFT, font=th.body(12)).pack(side="left")
        self.ins_bill_total = tk.Label(trow, bg=th.PAPER, fg=th.INK,
                                       font=th.display(22))
        self.ins_bill_total.pack(side="left", padx=(12, 0))
        self.ins_bill_note = tk.Label(trow, bg=th.PAPER, fg=th.PENCIL,
                                      font=th.mono(10))
        self.ins_bill_note.pack(side="left", padx=(10, 0))
        self.ins_bill_b1 = tk.Label(body, bg=th.PAPER, fg=th.INK_SOFT,
                                    font=th.mono(11))
        self.ins_bill_b1.pack(anchor="w", pady=(10, 0))
        self.ins_bill_b2 = tk.Label(body, bg=th.PAPER, fg=th.INK_SOFT,
                                    font=th.mono(11))
        self.ins_bill_b2.pack(anchor="w")

        th.hline(body, pady=(20, 20))
        self.ins_chart_head = tk.Label(body, bg=th.PAPER, fg=th.PENCIL,
                                       font=th.mono(10))
        self.ins_chart_head.pack(anchor="w", pady=(0, 8))
        self.ins_chart = charts.PinThread(body, height=190,
                                            bg=th.GRAPH_BG)
        self.ins_chart.pack(fill="x")
        self.ins_chart_note = tk.Label(body, bg=th.PAPER, fg=th.PENCIL,
                                       font=th.mono(10))
        self.ins_chart_note.pack(anchor="w", pady=(8, 0))

    # ---------------------------------------------------------- refresh
    def refresh_all(self):
        """Full pass, used once at startup. After that only the chrome
        plus the visible view refresh, so switching tabs or stamping a
        meal never rebuilds the whole window."""
        self.refresh_chrome()
        self.refresh_today()
        self.refresh_log()
        self.refresh_month()
        self.refresh_insights()

    def refresh_active(self):
        """Minimal refresh after a change: chrome plus the visible view."""
        self.refresh_chrome()
        {"TODAY": self.refresh_today,
         "LOG / EDIT": self.refresh_log,
         "MONTH": self.refresh_month,
         "INSIGHTS": self.refresh_insights}[self.active_view]()

    def _cycle_facts(self):
        now = mc.today()
        cs = mc.cycle_start(now)
        ce = mc.cycle_end(now)
        a = mc.allowance_status()
        b = mc.bill_between(cs, ce)
        return now, cs, ce, a, b

    def refresh_chrome(self):
        """Masthead + footer: today and cycle facts. Configure-only, so
        it never flickers."""
        now, cs, ce, a, b = self._cycle_facts()
        self.detail_mode = (self.active_view == "LOG / EDIT")
        day_no = (now - cs).days + 1
        total_days = mc.cycle_days(now)
        batch = mc.batch_of(now)
        over = a["over"] > 0

        # TODAY headings live on paper beneath the photo
        self._kicker("today", "")
        self.today_date.configure(text=now.strftime("%d %B %Y"))
        self.today_note.configure(
            text=(f"batch {batch} \u00b7 {a['remaining']:g} misses left"
                  if not over else
                  f"batch {batch} \u00b7 over by {a['over']:g}, "
                  f"mind the stamp"),
            fg=th.INK_SOFT if not over else th.STAMP)
        self.today_folio.configure(text=f"p. {day_no:02d}")
        self.banners["TODAY"].set_stamp(now.strftime("%d %b %Y").upper())

        self.footer_left.configure(
            text=(f"Cycle {cs.strftime('%d %b')} \u2013 "
                  f"{ce.strftime('%d %b')}  \u00b7  "
                  f"Misses {a['missed']:g} / {a['allowed']:g}"
                  + (f" \u2014 OVERDUE BY {a['over']:g}" if over else "")
                  + f"  \u00b7  Bill {rupees(b['total'])}"),
            fg=th.STAMP if over else th.INK_SOFT)
        self.footer_right.configure(text="")

    def refresh_today(self):
        now = mc.today()
        self.today_cards.set_day(now)
        today_e = mc.peek_day(now)
        today_bill, _ = mc.day_bill(today_e, now)
        self.today_sum.configure(
            text=f"Today \u2014 {today_e['meals_counted']:g} meals  \u00b7  "
                 f"{rupees(today_bill)}")
        cs = mc.cycle_start(now)
        self.week.set_days(self._week_data(now), today=now)
        self.week.set_progress((now - cs).days + 1, mc.cycle_days(now))

    def _scatter_view(self):
        """Keep the live view's doodles in free paper, evenly spaced.

        Runs on <Configure> and after a refresh. Whatever is already drawn
        is re-checked against live content: if the page re-flowed and
        something now sits under a doodle, that scatter is rebuilt until
        it comes back clean, or until the page has no room left."""
        view = self.active_view
        if view != "TODAY":
            return
        page = getattr(self, "views", {}).get(view)
        if page is None:
            return
        box = self.void
        kept = getattr(self, "_doodles", {})
        done = getattr(self, "_doodled", set())
        mine = kept.get(view, [])
        if done and mine and self._doodles_clear(box, mine):
            return

        want, gap = 8, 20
        # size the marks to the paper actually left over, so a short
        # window still gets doodles instead of an empty band
        try:
            vh = self.void.winfo_height()
        except Exception:
            vh = 120
        smin = max(26, min(44, vh // 3))
        smax = max(smin + 8, min(78, vh // 2))

        orig = kept.get(view, [])
        made, fresh = 0, []
        for _attempt in range(4):
            made, fresh = self._scatter_doodles(box, count=want, smin=smin,
                                                smax=smax, gap=gap)
            if made == 0 or self._doodles_clear(box, fresh):
                break
            for w in fresh:
                try:
                    w.destroy()
                except Exception:
                    pass
            fresh = []
        if made == 0:
            kept[view] = orig        # a cramped retry must not wipe the page
        else:
            for w in orig:
                try:
                    w.destroy()
                except Exception:
                    pass
            kept[view] = fresh
        self._doodles = kept
        self._doodled = ((done | {view}) if kept.get(view)
                         else (set(done) - {view}))

    def refresh_log(self):
        self.log_cards.set_day(self.log_date)
        log_e = mc.peek_day(self.log_date)
        log_bill, _ = mc.day_bill(log_e, self.log_date)
        _now = mc.today()
        _dno = (_now - mc.cycle_start(_now)).days + 1
        self._kicker("logm", "")
        self.logm_date.configure(text=self.log_date.strftime("%d %B %Y"))
        self.logm_note.configure(
            text=(f"{log_e['meals_counted']:g} meals \u00b7 "
                  f"{rupees(log_bill)}"))
        self.logm_folio.configure(
            text=f"p. {_dno:02d}")
        self.log_title.configure(
            text=f"Day total \u2014 {log_e['meals_counted']:g} meals  "
                 f"\u00b7  {rupees(log_bill)}")
        self.log_seal.set(day_complete(self.log_date, log_e))
        self._fill_history()
        self.after_idle(self.hist_scroll.refresh)

    def refresh_insights(self):
        now = mc.today()
        a = mc.allowance_status()
        self._fill_insights(now, a)
        self.after_idle(self.ins_scroll.refresh)

    def _fill_history(self):
        """Leaves persist across refreshes and are repainted in place;
        widgets are only rebuilt when the date range itself changes, so
        stamping a meal never flashes the list."""
        now = mc.today()
        cs = mc.cycle_start(now)
        ce = mc.cycle_end(now)
        self.log_hist_title.configure(
            text=f"LEAVES \u2014 BATCH {mc.batch_of(now)}")

        view_start = cs - timedelta(days=2)
        today_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        dates = [d for d, _ in mc.entries_between(view_start,
                                                  min(ce, today_day))]
        keys = [mc._date_key(d) for d in dates]
        if keys != self._hist_keys:
            self._rebuild_history(dates, cs)
        for key in keys:
            self._paint_hist_row(key)
        self.hist_list.update_idletasks()
        knots = []
        for key in keys:
            h = self._hist_rows[key]
            try:
                y = h["row"].winfo_y() + h["row"].winfo_height() // 2
            except Exception:
                continue
            knots.append((y, h["kind"], h["is_today"]))
        self.hist_thread.set_knots(knots)

    def _rebuild_history(self, dates, cs):
        for w in self.hist_list.winfo_children():
            w.destroy()
        self._hist_rows = {}
        self._hist_div = None
        for d in dates:
            if d == cs:
                self._hist_div = tk.Label(
                    self.hist_list, bg=th.PAPER, fg=th.PENCIL,
                    font=th.mono(10), anchor="w",
                    text=f"\u2014 {cs.strftime('%d %b')}: "
                         f"the cycle opens \u2014")
                self._hist_div.pack(fill="x", pady=8)
            self._make_hist_row(d)
        self._hist_keys = [mc._date_key(d) for d in dates]

    def _show_hist_preview(self, h, ev=None):
        """Float a small card beside a history row with that day's detail."""
        d = h["date"]
        e = mc.peek_day(d)
        eaten = sum(mc.meal_value(m, d) for m in mc.MEALS if e.get(m))
        expected = sum(mc.meal_value(m, d) for m in mc.MEALS)
        bill, _tax = mc.day_bill(e, d)
        bits = []
        for m in mc.MEALS:
            worth = mc.meal_value(m, d)
            if worth <= 0:
                bits.append(f"{m[:3]} closed")
            else:
                bits.append(f"{m[:3]} " + ("ate" if e.get(m) else "MISSED"))
        txt = (f"{d.strftime('%a %d %b')}  \u00b7  {eaten:g} of {expected:g} meals"
               f"  \u00b7  {rupees(bill)}\n"
               + "   ".join(bits))
        pv = self.hist_preview
        pv.configure(text=txt)
        try:
            x = h["row"].winfo_rootx() - self.winfo_rootx()
            y = (h["row"].winfo_rooty() - self.winfo_rooty()
                 + h["row"].winfo_height() + 4)
        except Exception:
            return
        w = max(220, pv.winfo_reqwidth() + 16)
        x = max(4, min(x, self.winfo_width() - w - 8))
        y = min(y, self.winfo_height() - pv.winfo_reqheight() - 46)
        pv.place(x=x, y=y)
        pv.lift()

    def _hide_hist_preview(self):
        try:
            self.hist_preview.place_forget()
        except Exception:
            pass

    def _make_hist_row(self, d):
        key = mc._date_key(d)
        row = tk.Frame(self.hist_list, bg=th.PAPER, cursor="hand2")
        row.pack(fill="x", pady=1)
        marker = tk.Frame(row, bg=th.PAPER, width=2, bd=0)
        marker.pack(side="left", fill="y")

        def _pick(dd=d):
            self.log_date = dd
            self.refresh_active()

        h = {"key": key, "date": d, "row": row, "marker": marker,
             "selected": False, "kind": "open", "is_today": False}
        h["l1"] = tk.Label(row, text="", width=7, anchor="w",
                            bg=th.PAPER, font=th.mono(11))
        h["l1"].pack(side="left")
        h["l2"] = tk.Label(row, text=DOW3[d.weekday()], width=5, anchor="w",
                            bg=th.PAPER, fg=th.INK_SOFT, font=th.mono(11))
        h["l2"].pack(side="left")
        h["mk"] = th.MarksCanvas(row, bg=th.PAPER)
        h["mk"].pack(side="left", padx=(4, 2))
        for tag in ("l4", "l5", "l6"):
            h[tag] = tk.Label(row, text="", anchor="w", bg=th.PAPER,
                              font=th.mono(11),
                              width=10 if tag != "l6" else 0)
            h[tag].pack(side="left")
        h["seal"] = th.Seal(row, bg=th.PAPER)
        h["seal"].pack(side="left", padx=(4, 8))
        h["cells"] = [h["l1"], h["l2"], h["l4"], h["l5"], h["l6"], h["seal"]]

        def _enter(ev=None, h=h):
            bg = th.CARD if h["selected"] else th.CARD_HI
            h["row"].configure(bg=bg)
            h["mk"].configure(bg=bg)
            for c in h["cells"]:
                c.configure(bg=bg)
            if not h["selected"]:
                h["marker"].configure(bg=th.RULE_DK)
            self._show_hist_preview(h, ev)

        def _leave(ev=None, h=h):
            bg = th.CARD if h["selected"] else th.PAPER
            h["row"].configure(bg=bg)
            h["mk"].configure(bg=bg)
            for c in h["cells"]:
                c.configure(bg=bg)
            if not h["selected"]:
                h["marker"].configure(bg=th.PAPER)
            self._hide_hist_preview()

        for w in [row] + h["cells"]:
            w.bind("<Button-1>", lambda e, dd=d: _pick(dd))
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
        h["mk"].bind("<Button-1>", lambda e, dd=d: _pick(dd))
        h["mk"].bind("<Enter>", _enter)
        h["mk"].bind("<Leave>", _leave)
        h["seal"].bind("<Button-1>", lambda e, dd=d: _pick(dd))
        h["seal"].bind("<Enter>", _enter)
        h["seal"].bind("<Leave>", _leave)
        self._hist_rows[key] = h

    def _paint_hist_row(self, key):
        h = self._hist_rows[key]
        d = h["date"]
        now = mc.today()
        cs = mc.cycle_start(now)
        e = mc.peek_day(d)
        prev_cycle = d < cs
        bill, _ = mc.day_bill(e, d)
        if d.weekday() == 5:
            marks = ((e.get("breakfast") if e else False),
                     (e.get("lunch") if e else False), "na")
        else:
            marks = tuple(bool(e.get(m)) if e else False for m in mc.MEALS)
        complete = day_complete(d, e)
        h["is_today"] = mc._date_key(d) == mc._date_key(now)
        h["selected"] = mc._date_key(d) == mc._date_key(self.log_date)
        h["kind"] = ("selected" if h["selected"]
                     else ("prev" if prev_cycle
                           else ("done" if complete else "open")))
        base = th.INK if not prev_cycle else th.PENCIL
        h["l1"].configure(text=d.strftime("%d %b"), fg=base)
        h["mk"].set(*[("yes" if m is True else ("na" if m == "na" else "no"))
                      for m in marks], dim=prev_cycle)
        h["l4"].configure(
            text=f"{e['meals_counted']:g} meals" if e else "0.0 meals",
            fg=base)
        h["l5"].configure(text=rupees(bill), fg=base)
        tag = ""
        if prev_cycle:
            tag = "(Previous Cycle)"
        elif h["selected"]:
            tag = "< selected"
        h["l6"].configure(text=tag,
                           fg=th.STAMP if h["selected"] else th.PENCIL)
        h["seal"].set(complete)
        bg = th.CARD if h["selected"] else th.PAPER
        h["row"].configure(bg=bg)
        h["mk"].configure(bg=bg)
        for c in h["cells"]:
            c.configure(bg=bg)
        h["marker"].configure(bg=th.INK if h["selected"] else th.PAPER)

    def _fill_insights(self, now, a):
        cs = mc.cycle_start(now)
        ce = mc.cycle_end(now)
        over = a["over"] > 0
        day_no = (now - cs).days + 1
        self._kicker("ins", f"No. {cycle_edition(cs):02d}")
        self.ins_date.configure(
            text=(f"{cs.strftime('%d %b')} \u2013 "
                  f"{ce.strftime('%d %b')}"))
        self.ins_note.configure(
            text=(f"day {day_no} of {mc.cycle_days(now)} \u00b7 "
                  f"batch {mc.batch_of(now)}"))
        self.ins_folio.configure(
            text=f"p. {day_no:02d}")
        self.ins_allow_head.configure(
            text=f"MISS ALLOWANCE \u2014 {a['allowed']:g} ALLOWED")
        self.ins_allow_left.configure(
            text=(f"{a['remaining']:g} remaining" if not over
                  else f"Over by {a['over']:g}"),
            fg=th.STAMP if over else th.INK)
        self.ins_allow_right.configure(
            text=f"{a['missed']:g} struck", fg=th.STAMP if over
            else th.INK_SOFT)
        self.allowance.set_value(a["missed"], a["allowed"])
        b1s, b1e = mc.batch_range(1, now)
        b2s, b2e = mc.batch_range(2, now)
        b1 = mc.allowance_status(scope=1)
        b2 = mc.allowance_status(scope=2)
        b2_upcoming = mc.batch_of(now) < 2
        self.ins_b1.configure(
            text=(f"Chapter One \u2014 Batch 1 ({b1s.strftime('%d %b')} "
                  f"\u2013 {b1e.strftime('%d %b')} \u00b7 "
                  f"{(b1e - b1s).days + 1} days): {b1['missed']:g} missed"))
        self.ins_b2.configure(
            text=(f"Chapter Two \u2014 Batch 2 ({b2s.strftime('%d %b')} "
                  f"\u2013 {b2e.strftime('%d %b')} \u00b7 "
                  f"{(b2e - b2s).days + 1} days): {b2['missed']:g} missed"
                  + (" (upcoming)" if b2_upcoming else "")))

        bill = mc.bill_between(cs, ce)
        b1bill = mc.bill_between(b1s, b1e)
        b2bill = mc.bill_between(b2s, b2e)
        portions = sum(bill["portions"].values())
        self.ins_bill_total.configure(text=rupees(bill["total"]))
        self.ins_bill_note.configure(text=f"({portions} meals billed)")
        self.ins_bill_b1.configure(text=f"Batch 1:  {rupees(b1bill['total'])}")
        self.ins_bill_b2.configure(
            text=f"Batch 2:    {rupees(b2bill['total'])}"
            + ("  (upcoming)" if b2_upcoming else ""))

        rng_start = cs - timedelta(days=2)
        self.ins_chart_head.configure(
            text=f"MEALS ENTERED PER DAY \u2014 "
                 f"{cs.strftime('%B %Y').upper()} CYCLE")
        values, labels, colors, missing = [], [], [], []
        for d, e in mc.entries_between(rng_start, ce):
            in_cycle = d >= cs
            v = float(e.get("meals_counted", 0)) if e else 0.0
            values.append(v if in_cycle or e else 0.0)
            labels.append(f"{d.strftime('%d')}\n{DOW3[d.weekday()]}")
            colors.append(th.INK if in_cycle else th.PENCIL_LT)
            missing.append(e is None)
        self.ins_chart.set_data(values, labels=labels, colors=colors,
                                missing=missing, split_at=2)
        st, days = mc.per_meal_stats(cs, now)
        self.ins_break.set_stats(st, days)
        self.ins_break_head.configure(
            text=(f"day 1-{days} of this cycle" if days
                  else "no days logged yet"))
        self.ins_chart_note.configure(
            text=(f"{rng_start.strftime('%d %b')}\u2013"
                  f"{(cs - timedelta(days=1)).strftime('%d %b')} previous "
                  f"cycle      |      [-- BATCH 1 START "
                  f"{cs.strftime('%d %b').upper()} --]"))


if __name__ == "__main__":
    app = MealApp()
    app.mainloop()
