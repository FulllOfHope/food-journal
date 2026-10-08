#!/usr/bin/env python3
"""Meal tracker GUI: TODAY, LOG / EDIT, INSIGHTS.

The Mess Ledger: a bound paper journal. Entry mastheads with margin
notes, rubber-stamp meal states, pencil-box allowance marks, hand-drawn
margin ticks, edition numbering and page folios. All domain rules and
storage live in meal_common; this file only renders and dispatches user
actions.
"""
import sys
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meal_charts as charts
import meal_common as mc
import meal_theme as th

APP_TITLE = "Mess Ledger"
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


# ------------------------------------------------------------ meal cards
class MealCard(tk.Frame):
    """One entry sheet: eyebrow, rubber stamp, ruled meta."""

    def __init__(self, master, app, meal):
        super().__init__(master, bg=th.CARD, bd=0, highlightthickness=1,
                         highlightbackground=th.RULE)
        self.app = app
        self.meal = meal
        self.date = mc.today()
        self._enabled = True

        self.head = tk.Frame(self, bg=th.CARD)
        self.head.pack(fill="x", padx=16, pady=(14, 0))
        self.name = tk.Label(self.head, bg=th.CARD, fg=th.INK_SOFT,
                             font=th.mono(11))
        self.name.pack(side="left")
        self.key = tk.Label(self.head, bg=th.CARD, fg=th.PENCIL,
                            font=th.mono(11))
        self.key.pack(side="right")

        self.stamp = th.Stamp(self, height=54, bg=th.CARD)
        self.stamp.pack(anchor="w", padx=16, pady=(20, 20))

        self.rule = tk.Frame(self, bg=th.RULE, height=1, bd=0)
        self.rule.pack(fill="x", padx=16)

        self.foot = tk.Frame(self, bg=th.CARD)
        self.foot.pack(fill="x", padx=16, pady=(10, 14))
        self.meta_l = tk.Label(self.foot, bg=th.CARD, fg=th.INK_SOFT,
                               font=th.mono(12))
        self.meta_l.pack(side="left")
        self.meta_r = tk.Label(self.foot, bg=th.CARD, fg=th.INK_SOFT,
                               font=th.mono(12))
        self.meta_r.pack(side="right")

        self._widgets = [self, self.head, self.name, self.key, self.foot,
                         self.meta_l, self.meta_r]
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

    def _leave(self, _e=None):
        self._paint()
        self.configure(cursor="")

    def _click(self, _e=None):
        if not self._enabled:
            return
        e = mc.peek_day(self.date)
        mc.toggle_meal(self.date, self.meal, not e.get(self.meal, False))
        self.app.refresh_all()

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
class MealApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.configure(bg=th.PAPER)
        th.init_theme(self)
        self.detail_mode = False
        self.log_date = mc.today()
        self.active_view = "TODAY"
        self._fit_to_screen()

        self.paper = th.PaperCanvas(self)
        self.paper.pack(fill="both", expand=True)

        self._build()
        self.bind("<Key-b>", lambda e: self._key_meal("breakfast"))
        self.bind("<Key-l>", lambda e: self._key_meal("lunch"))
        self.bind("<Key-d>", lambda e: self._key_meal("dinner"))
        self.bind("<Key-B>", lambda e: self._key_meal("breakfast"))
        self.bind("<Key-L>", lambda e: self._key_meal("lunch"))
        self.bind("<Key-D>", lambda e: self._key_meal("dinner"))
        self.bind("<Left>", lambda e: self._key_step(-1))
        self.bind("<Right>", lambda e: self._key_step(1))
        self.refresh_all()

    # ------------------------------------------------------------ layout
    def _fit_to_screen(self):
        try:
            sw = max(640, self.winfo_screenwidth())
            sh = max(480, self.winfo_screenheight())
        except Exception:
            sw, sh = 1280, 800
        w = max(780, min(1180, int(sw * 0.94)))
        h = max(660, min(800, int(sh * 0.9)))
        x = max(0, (sw - w) // 2)
        y = max(0, min(40, (sh - h) // 8))
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(min(780, w), min(660, h))

    def _build(self):
        # -- header: ledger brand left, mono tabs right, double rule
        head = tk.Frame(self.paper, bg=th.PAPER)
        head.pack(fill="x", padx=GUTTER, pady=(18, 0))
        brand = tk.Label(head, text=APP_TITLE, bg=th.PAPER, fg=th.INK,
                         font=th.display(16))
        brand.pack(side="left")
        tabs = tk.Frame(head, bg=th.PAPER)
        tabs.pack(side="right")
        self.tab_ui = {}
        for name in ("TODAY", "LOG / EDIT", "INSIGHTS"):
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

        # -- entry masthead with margin note + folio
        mast = tk.Frame(self.paper, bg=th.PAPER)
        mast.pack(fill="x", padx=GUTTER, pady=(16, 0))
        left = tk.Frame(mast, bg=th.PAPER)
        left.pack(side="left")
        self.mast_eb = th.eyebrow(left, "")
        self.mast_eb.pack(anchor="w")
        self.mast_date = tk.Label(left, bg=th.PAPER, fg=th.INK,
                                  font=th.display(34), anchor="w")
        self.mast_date.pack(anchor="w", pady=(2, 0))
        self.mast_note = tk.Label(left, bg=th.PAPER, fg=th.INK_SOFT,
                                  font=th.hand(16), anchor="w")
        self.mast_note.pack(anchor="w", pady=(2, 0))
        right = tk.Frame(mast, bg=th.PAPER)
        right.pack(side="right", anchor="n")
        self.mast_folio = tk.Label(right, bg=th.PAPER, fg=th.PENCIL,
                                   font=th.mono(12), anchor="e")
        self.mast_folio.pack(anchor="e")
        self.mast_ed = th.Stamp(right, height=40, bg=th.PAPER,
                                font=("Outfit", 11, "bold"))
        self.mast_ed.pack(anchor="e", pady=(8, 0))

        # -- views
        self.views = {}
        for name, builder in (("TODAY", self._build_today),
                              ("LOG / EDIT", self._build_log),
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

        self._show("TODAY")
        if len(sys.argv) > 1 and sys.argv[1].lower().startswith("log"):
            self._show("LOG / EDIT")
        elif len(sys.argv) > 1 and sys.argv[1].lower().startswith("ins"):
            self._show("INSIGHTS")

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
                f.pack(fill="both", expand=True, padx=GUTTER, pady=(18, 0))
            else:
                f.pack_forget()
        for n, (holder, lbl, underline) in self.tab_ui.items():
            active = n == name
            lbl.configure(fg=th.INK if active else th.PENCIL)
            underline.configure(bg=th.STAMP if active else th.PAPER)
        self.detail_mode = (name == "LOG / EDIT")
        self.refresh_all()

    # ------------------------------------------------------------ TODAY
    def _build_today(self, parent):
        self.today_cards = CardRow(parent, self)
        self.today_cards.pack(fill="x")

        row = tk.Frame(parent, bg=th.PAPER)
        row.pack(fill="x", pady=(20, 0))
        self.today_sum = tk.Label(row, bg=th.PAPER, fg=th.INK,
                                  font=th.mono(11))
        self.today_sum.pack(side="left")
        th.button(row, "CLEAR", lambda: self._set_all_today(False),
                  kind="ghost", bg=th.PAPER)[0].pack(side="right",
                                                     padx=(10, 0))
        th.button(row, "MARK ALL EATEN", lambda: self._set_all_today(True),
                  kind="primary")[0].pack(side="right")

    def _set_all_today(self, value):
        now = mc.today()
        for meal in mc.MEALS:
            if meal == "dinner" and now.weekday() == 5:
                continue
            mc.toggle_meal(now, meal, value)
        self.refresh_all()

    # ---------------------------------------------------------- LOG/EDIT
    def _build_log(self, parent):
        nav = tk.Frame(parent, bg=th.PAPER)
        nav.pack(fill="x", pady=(0, 16))
        th.button(nav, "< YESTERDAY", lambda: self._step(-1),
                  kind="ghost", bg=th.PAPER)[0].pack(side="left")
        self.log_title = tk.Label(nav, bg=th.PAPER, fg=th.INK,
                                  font=th.display(20))
        self.log_title.pack(side="left", expand=True)
        th.button(nav, "TOMORROW >", lambda: self._step(1),
                  kind="ghost", bg=th.PAPER)[0].pack(side="right")

        self.log_cards = CardRow(parent, self)
        self.log_cards.pack(fill="x")
        self.log_sum = tk.Label(parent, bg=th.PAPER, fg=th.INK_SOFT,
                                font=th.mono(11))
        self.log_sum.pack(anchor="w", pady=(14, 0))

        th.hline(parent, pady=(18, 0))
        head = tk.Frame(parent, bg=th.PAPER)
        head.pack(fill="x", pady=(10, 8))
        self.log_hist_title = tk.Label(head, bg=th.PAPER, fg=th.PENCIL,
                                       font=th.mono(10))
        self.log_hist_title.pack(side="left")
        th.button(head, "JUMP TO TODAY", self._jump_today,
                  kind="ghost", bg=th.PAPER)[0].pack(side="right")

        self.hist_scroll = th.ScrollFrame(parent, bg=th.PAPER)
        self.hist_scroll.pack(fill="both", expand=True)
        self.hist_inner = self.hist_scroll.inner

    def _step(self, delta):
        self.log_date += timedelta(days=delta)
        self.refresh_all()

    def _jump_today(self):
        self.log_date = mc.today()
        self.refresh_all()

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
        self.refresh_all()

    def _key_step(self, delta):
        if self.active_view == "LOG / EDIT":
            self._step(delta)

    # ---------------------------------------------------------- INSIGHTS
    def _build_insights(self, parent):
        self.ins_scroll = th.ScrollFrame(parent, bg=th.PAPER)
        self.ins_scroll.pack(fill="both", expand=True)
        body = tk.Frame(self.ins_scroll.inner, bg=th.PAPER)
        body.pack(fill="both", expand=True)
        self.ins_body = body

        brow = tk.Frame(body, bg=th.PAPER)
        brow.pack(fill="x", pady=(0, 4))
        tk.Label(brow, text="03 \u2014 CYCLE", bg=th.PAPER, fg=th.PENCIL,
                 font=th.mono(10)).pack(side="left")
        self.ins_cycle = tk.Label(brow, bg=th.PAPER, fg=th.INK,
                                  font=th.display(20))
        self.ins_cycle.pack(side="left", padx=(14, 0))

        allow_head = tk.Label(body, bg=th.PAPER, fg=th.PENCIL,
                              font=th.mono(10))
        allow_head.pack(anchor="w", pady=(18, 0))
        self.ins_allow_head = allow_head
        arow = tk.Frame(body, bg=th.PAPER)
        arow.pack(fill="x", pady=(6, 2))
        self.ins_allow_left = tk.Label(arow, bg=th.PAPER, fg=th.INK,
                                       font=th.display(16))
        self.ins_allow_left.pack(side="left")
        self.ins_allow_right = tk.Label(arow, bg=th.PAPER, fg=th.INK_SOFT,
                                        font=th.mono(11))
        self.ins_allow_right.pack(side="right")
        self.pencilbox = th.PencilBox(body, bg=th.PAPER)
        self.pencilbox.pack(fill="x", pady=(4, 6))
        self.ins_b1 = tk.Label(body, bg=th.PAPER, fg=th.INK_SOFT,
                               font=th.mono(11))
        self.ins_b1.pack(anchor="w")
        self.ins_b2 = tk.Label(body, bg=th.PAPER, fg=th.INK_SOFT,
                               font=th.mono(11))
        self.ins_b2.pack(anchor="w")

        th.hline(body, pady=(20, 20))
        bill_head = tk.Label(body, text="CYCLE BILL", bg=th.PAPER,
                             fg=th.PENCIL, font=th.mono(10))
        bill_head.pack(anchor="w", pady=(0, 8))
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
        self.ins_chart = charts.BarChart(body, height=190, thin=True,
                                         vgrid=False, ymax=3.0,
                                         target_ticks=6, value_fmt=False,
                                         bg=th.GRAPH_BG)
        self.ins_chart.pack(fill="x")
        self.ins_chart_note = tk.Label(body, bg=th.PAPER, fg=th.PENCIL,
                                       font=th.mono(10))
        self.ins_chart_note.pack(anchor="w", pady=(8, 0))

    # ---------------------------------------------------------- refresh
    def refresh_all(self):
        now = mc.today()
        self.detail_mode = (self.active_view == "LOG / EDIT")
        cs = mc.cycle_start(now)
        ce = mc.cycle_end(now)
        day_no = (now - cs).days + 1
        total_days = mc.cycle_days(now)
        batch = mc.batch_of(now)
        ed = cycle_edition(cs)

        a = mc.allowance_status()
        b = mc.bill_between(cs, ce)
        over = a["over"] > 0

        # entry masthead always shows today
        self.mast_eb.configure(
            text=f"ENTRY \u2014 {now.strftime('%A').upper()}")
        self.mast_date.configure(text=now.strftime("%d %B %Y"))
        self.mast_note.configure(
            text=(f"day {day_no} of {total_days} \u00b7 batch {batch} "
                  f"\u2014 {a['remaining']:g} left in the pencil box"
                  if not over else
                  f"day {day_no} of {total_days} \u00b7 batch {batch} "
                  f"\u2014 over by {a['over']:g}, mind the stamp"),
            fg=th.INK_SOFT if not over else th.STAMP)
        self.mast_folio.configure(text=f"p. {day_no:02d}")
        self.mast_ed.set(f"CYCLE No. {ed:02d}", "edition")

        # TODAY
        self.today_cards.set_day(now)
        today_e = mc.peek_day(now)
        today_bill, _ = mc.day_bill(today_e, now)
        self.today_sum.configure(
            text=f"Today \u2014 {today_e['meals_counted']:g} meals  \u00b7  "
                 f"{rupees(today_bill)}")

        self.footer_left.configure(
            text=(f"Cycle {cs.strftime('%d %b')} \u2013 "
                  f"{ce.strftime('%d %b')}  \u00b7  "
                  f"Day {day_no} of {total_days} \u00b7  "
                  f"Batch {batch}      "
                  f"Misses {a['missed']:g} / {a['allowed']:g}"
                  + (f" \u2014 OVERDUE BY {a['over']:g}" if over else "")
                  + f"      Bill {rupees(b['total'])}"),
            fg=th.STAMP if over else th.INK_SOFT)
        self.footer_right.configure(
            text=f"p. {day_no:02d}   \u00b7   B / L / D TO LOG")

        # LOG / EDIT
        self.log_cards.set_day(self.log_date)
        log_e = mc.peek_day(self.log_date)
        log_bill, _ = mc.day_bill(log_e, self.log_date)
        self.log_title.configure(
            text=self.log_date.strftime("%A, %d %b %Y"))
        self.log_sum.configure(
            text=f"Day total \u2014 {log_e['meals_counted']:g} meals  "
                 f"\u00b7  {rupees(log_bill)}")
        self._fill_history()

        # INSIGHTS
        self._fill_insights(now, a)

        for sf in (getattr(self, "hist_scroll", None),
                   getattr(self, "ins_scroll", None)):
            if sf is not None:
                self.after_idle(sf.refresh)

    def _fill_history(self):
        for w in self.hist_inner.winfo_children():
            w.destroy()
        now = mc.today()
        cs = mc.cycle_start(now)
        ce = mc.cycle_end(now)
        self.log_hist_title.configure(
            text=f"LEAVES \u2014 BATCH {mc.batch_of(now)}")

        view_start = cs - timedelta(days=2)
        today_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        for d, e in mc.entries_between(view_start, min(ce, today_day)):
            if d == cs:
                div = tk.Label(self.hist_inner, bg=th.PAPER, fg=th.PENCIL,
                               font=th.mono(10), anchor="w",
                               text=f"\u2014 {cs.strftime('%d %b')}: "
                                    f"the cycle opens \u2014")
                div.pack(fill="x", pady=8)
            prev_cycle = d < cs
            bill, _ = mc.day_bill(e, d)
            if d.weekday() == 5:
                marks = ((e.get("breakfast") if e else False),
                         (e.get("lunch") if e else False), "na")
            else:
                marks = tuple(bool(e.get(m)) if e else False
                              for m in mc.MEALS)
            total = f"{e['meals_counted']:g} meals" if e else "0.0 meals"
            selected = mc._date_key(d) == mc._date_key(self.log_date)
            tag = ""
            if prev_cycle:
                tag = "(Previous Cycle)"
            elif selected:
                tag = "< selected"
            row = tk.Frame(self.hist_inner, bg=th.PAPER, cursor="hand2")
            row.pack(fill="x", pady=1)
            marker = tk.Frame(row, bg=th.PAPER, width=2, bd=0)
            marker.pack(side="left", fill="y")

            def _pick(dd=d):
                self.log_date = dd
                self.refresh_all()

            base = th.INK if not prev_cycle else th.PENCIL
            l1 = tk.Label(row, text=d.strftime("%d %b"), width=7, anchor="w",
                          bg=th.PAPER, fg=base, font=th.mono(11))
            l1.pack(side="left")
            l2 = tk.Label(row, text=DOW3[d.weekday()], width=5, anchor="w",
                          bg=th.PAPER, fg=th.INK_SOFT, font=th.mono(11))
            l2.pack(side="left")
            mk = th.MarksCanvas(row, bg=th.PAPER)
            mk.pack(side="left", padx=(4, 2))
            mk.set(*[("yes" if m is True else ("na" if m == "na" else "no"))
                     for m in marks], dim=prev_cycle)
            l4 = tk.Label(row, text=total, width=10, anchor="w",
                          bg=th.PAPER, fg=base, font=th.mono(11))
            l4.pack(side="left")
            l5 = tk.Label(row, text=rupees(bill), width=10, anchor="w",
                          bg=th.PAPER, fg=base, font=th.mono(11))
            l5.pack(side="left")
            l6 = tk.Label(row, text=tag, anchor="w", bg=th.PAPER,
                          fg=th.STAMP if selected else th.PENCIL,
                          font=th.mono(11))
            l6.pack(side="left")
            cells = [l1, l2, l4, l5, l6]
            if selected:
                marker.configure(bg=th.INK)
                row.configure(bg=th.CARD)
                mk.configure(bg=th.CARD)
                for c in cells:
                    c.configure(bg=th.CARD)

            def _enter(ev=None, r=row, cs_=cells, m=marker, sel=selected,
                       mc_=mk):
                bg = th.CARD if sel else th.CARD_HI
                r.configure(bg=bg)
                mc_.configure(bg=bg)
                for c in cs_:
                    c.configure(bg=bg)
                if not sel:
                    m.configure(bg=th.RULE_DK)

            def _leave(ev=None, r=row, cs_=cells, m=marker, sel=selected,
                       mc_=mk):
                bg = th.CARD if sel else th.PAPER
                r.configure(bg=bg)
                mc_.configure(bg=bg)
                for c in cs_:
                    c.configure(bg=bg)
                if not sel:
                    m.configure(bg=th.PAPER)

            for w in [row] + cells:
                w.bind("<Button-1>", lambda e, dd=d: _pick(dd))
                w.bind("<Enter>", _enter)
                w.bind("<Leave>", _leave)
            mk.bind("<Button-1>", lambda e, dd=d: _pick(dd))
            mk.bind("<Enter>", _enter)
            mk.bind("<Leave>", _leave)

    def _fill_insights(self, now, a):
        cs = mc.cycle_start(now)
        ce = mc.cycle_end(now)
        over = a["over"] > 0
        self.ins_cycle.configure(
            text=f"Cycle {cs.strftime('%d %b')} \u2013 "
                 f"{ce.strftime('%d %b')}")
        self.ins_allow_head.configure(
            text=f"PENCIL BOX \u2014 {a['allowed']:g} MISSES ALLOWED")
        self.ins_allow_left.configure(
            text=(f"{a['remaining']:g} left in the box" if not over
                  else f"Over by {a['over']:g}"),
            fg=th.STAMP if over else th.INK)
        self.ins_allow_right.configure(
            text=f"{a['missed']:g} struck", fg=th.STAMP if over
            else th.INK_SOFT)
        self.pencilbox.set_value(a["missed"], a["allowed"])
        b1s, b1e = mc.batch_range(1, now)
        b2s, b2e = mc.batch_range(2, now)
        b1 = mc.allowance_status(scope=1)
        b2 = mc.allowance_status(scope=2)
        b2_upcoming = mc.batch_of(now) < 2
        self.ins_b1.configure(
            text=(f"Batch 1 ({b1s.strftime('%d %b')} \u2013 "
                  f"{b1e.strftime('%d %b')} \u00b7 "
                  f"{(b1e - b1s).days + 1} days): {b1['missed']:g} missed"))
        self.ins_b2.configure(
            text=(f"Batch 2 ({b2s.strftime('%d %b')} \u2013 "
                  f"{b2e.strftime('%d %b')} \u00b7 "
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
                                missing=missing)
        self.ins_chart_note.configure(
            text=(f"{rng_start.strftime('%d %b')}\u2013"
                  f"{(cs - timedelta(days=1)).strftime('%d %b')} previous "
                  f"cycle      |      [-- BATCH 1 START "
                  f"{cs.strftime('%d %b').upper()} --]"))


if __name__ == "__main__":
    app = MealApp()
    app.mainloop()
