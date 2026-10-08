"""Physical-journal theme for the Meal Tracker: the Mess Ledger.

Replicates the feel of a bound paper journal (Baron Fig / Field Notes /
Day One lineage): warm paper with grain and dot-grid ruling, a stitched
spine, a red margin rule, Playfair entry mastheads, Caveat margin notes,
rubber-stamp states, pencil-box allowance marks and letterpress buttons.

Domain rules and storage live in meal_common; this file is presentation.
"""
import math
import random
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

# ---------------------------------------------------------------- palette
PAPER     = "#f4f1ea"   # journal page
PAPER_DK  = "#ece7d9"   # aged edges
CARD      = "#faf8f2"   # fresh entry sheets
CARD_HI   = "#fffdf7"   # sheet hover lift
GRAPH_BG  = "#efe9da"   # chart paper
INK       = "#212121"   # fountain-pen ink
INK_SOFT  = "#4a4843"   # secondary ink
PENCIL    = "#8a867e"   # pencil grey
PENCIL_LT = "#b3ada0"   # faint pencil
RULE      = "#ddd5c2"   # hairlines
RULE_DK   = "#c0b797"   # stronger rules
DOTS      = "#d5cdb6"   # dot-grid dots
MARGIN    = "#d69a86"   # red margin rule
SPINE     = "#e8e2d4"   # bound edge strip
STITCH    = "#b3a88f"   # stitching thread
STAMP     = "#b3402e"   # rubber-stamp red
RED       = "#b3402e"   # danger is stamped red, like everything urgent

# legacy aliases kept so untouched call-sites keep working
BG        = PAPER
BG_C      = PAPER_DK
BG_H      = CARD
PANEL     = CARD
PANEL_HI  = CARD_HI
PANEL_ALT = PAPER_DK
BORDER    = RULE
BORDER_HI = RULE_DK
TEXT      = INK
TEXT_HI   = "#111111"
TEXT_DIM  = INK_SOFT
TEXT_MUTE = PENCIL
GREEN     = STAMP       # single interface accent: the stamp pad
GREEN_DK  = STAMP
CYAN      = INK
AMBER     = INK
MAGENTA   = PENCIL
BLUE      = INK

MEAL_COLORS = {"breakfast": INK, "lunch": INK, "dinner": INK}

_DISPLAY_CANDIDATES = ["Playfair Display", "Noto Serif", "Georgia",
                       "DejaVu Serif"]
_BODY_CANDIDATES = ["Outfit", "Inter", "Ubuntu", "DejaVu Sans"]
_MONO_CANDIDATES = ["DM Mono", "JetBrains Mono", "DejaVu Sans Mono"]
_HAND_CANDIDATES = ["Caveat", "Segoe Script", "DejaVu Sans"]

_display_family = None
_body_family = None
_mono_family = None
_hand_family = None


def _pick(candidates, fallbacks=()):
    try:
        available = set(tkfont.families())
    except Exception:
        available = set()
    for name in list(candidates) + list(fallbacks):
        if name in available:
            return name
    return "TkFixedFont"


def resolve_fonts():
    """Pick the journal type system once, falling back gracefully."""
    global _display_family, _body_family, _mono_family, _hand_family
    _display_family = _pick(_DISPLAY_CANDIDATES, ["TkFixedFont"])
    _body_family = _pick(_BODY_CANDIDATES, ["TkFixedFont"])
    _mono_family = _pick(_MONO_CANDIDATES, ["TkFixedFont"])
    _hand_family = _pick(_HAND_CANDIDATES, ["TkFixedFont"])
    return _display_family, _body_family, _mono_family, _hand_family


def display(size=16, weight="normal", slant="roman"):
    spec = [_display_family or "DejaVu Serif", size]
    if weight and weight != "normal":
        spec.append(weight)
    if slant and slant != "roman":
        spec.append(slant)
    return tuple(spec)


def body(size=11, weight="normal"):
    spec = [_body_family or "DejaVu Sans", size]
    if weight and weight != "normal":
        spec.append(weight)
    return tuple(spec)


def mono(size=10, weight="normal"):
    spec = [_mono_family or "DejaVu Sans Mono", size]
    if weight and weight != "normal":
        spec.append(weight)
    return tuple(spec)


def hand(size=14, weight="normal"):
    spec = [_hand_family or "DejaVu Sans", size]
    if weight and weight != "normal":
        spec.append(weight)
    return tuple(spec)


def lerp_hex(a, b, t):
    """Blend two #rrggbb colours."""
    a, b = a.lstrip("#"), b.lstrip("#")
    mix = lambda i: int(int(a[i:i + 2], 16) * (1 - t)
                        + int(b[i:i + 2], 16) * t)
    return "#%02x%02x%02x" % (mix(0), mix(2), mix(4))


# ------------------------------------------------------------------- bits
def init_theme(root):
    """Apply the clam base so ttk widgets inherit the paper ground."""
    resolve_fonts()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(".", background=PAPER, foreground=INK,
                    fieldbackground=CARD, borderwidth=0, focuscolor=PAPER)
    style.configure("Vertical.TScrollbar", background=RULE_DK,
                    troughcolor=PAPER, bordercolor=PAPER, arrowcolor=PAPER,
                    borderwidth=0, relief="flat", arrowsize=0, width=11)
    return style


def frame(parent, bg=PAPER, border=RULE, pad=0, **kw):
    """A flat sheet with a crisp 1px rule."""
    outer = tk.Frame(parent, bg=border, bd=0, highlightthickness=0, **kw)
    inner = tk.Frame(outer, bg=bg, bd=0, highlightthickness=0)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    if pad:
        inner = tk.Frame(inner, bg=bg, bd=0)
        inner.pack(fill="both", expand=True, padx=pad, pady=pad)
        return outer, inner
    return outer, inner


def panel(parent, title=None, bg=CARD, border=RULE, pad=14):
    """Ruled sheet with an optional mono eyebrow heading."""
    outer, body_frame = frame(parent, bg=bg, border=border)
    body_frame.configure(padx=pad, pady=pad)
    if title:
        lbl = tk.Label(body_frame, text=title.upper(), bg=bg, fg=PENCIL,
                       font=mono(10), anchor="w")
        lbl.pack(fill="x", pady=(0, 8))
    return outer, body_frame


def label(parent, text="", fg=INK, bg=CARD, font=None, anchor="w", **kw):
    return tk.Label(parent, text=text, bg=bg, fg=fg,
                    font=font or body(11), anchor=anchor, **kw)


def eyebrow(parent, text, bg=PAPER, fg=PENCIL):
    """Small-caps section kicker, e.g. 'ENTRY - SUNDAY'."""
    return tk.Label(parent, text=text, bg=bg, fg=fg, font=mono(10),
                    anchor="w")


def hline(parent, bg=RULE, pady=6):
    tk.Frame(parent, bg=bg, height=1, bd=0).pack(fill="x", pady=pady)


def double_rule(parent, pady=8):
    """Ledger double rule: thick ink line over a hairline."""
    tk.Frame(parent, bg=INK, height=2, bd=0).pack(fill="x", pady=(pady, 3))
    tk.Frame(parent, bg=RULE_DK, height=1, bd=0).pack(fill="x",
                                                     pady=(0, pady))


def button(parent, text, command, kind="ghost", bg=None, font=None,
           padx=16, pady=8):
    """Letterpress buttons: solid ink primary, ruled ghost secondary."""
    bg = bg or PAPER
    if kind == "primary":
        idle, idle_fg, holder_bg = INK, PAPER, INK
    else:
        idle, idle_fg, holder_bg = bg, INK_SOFT, RULE_DK
    holder = tk.Frame(parent, bg=holder_bg, bd=0, highlightthickness=0)
    lbl = tk.Label(holder, text=text, bg=idle, fg=idle_fg,
                   font=font or mono(10), padx=padx, pady=pady,
                   cursor="hand2")
    lbl.pack(padx=1, pady=1)

    def enter(_=None):
        if kind == "primary":
            lbl.configure(bg=PAPER, fg=INK)
        else:
            lbl.configure(bg=CARD_HI, fg=INK)
            holder.configure(bg=INK)

    def leave(_=None):
        lbl.configure(bg=idle, fg=idle_fg)
        holder.configure(bg=holder_bg)

    def press(_=None):
        lbl.configure(bg=STAMP, fg=PAPER)

    def release(event=None):
        leave()
        command()

    for w in (holder, lbl):
        w.bind("<Enter>", enter)
        w.bind("<Leave>", leave)
        w.bind("<ButtonPress-1>", press)
        w.bind("<ButtonRelease-1>", release)
    return holder, lbl


# ------------------------------------------------------- journal paper
class PaperCanvas(tk.Canvas):
    """Full-window journal sheet: grain, dot-grid ruling, stitched spine
    and a red margin rule. Content widgets pack inside it as children and
    render above the drawings, so the paper breathes through every gutter.
    """

    def __init__(self, master, grain_tile=132, grid=24, **kw):
        super().__init__(master, bg=PAPER, highlightthickness=0, bd=0,
                         **kw)
        self._rng = random.Random(11)
        self._grain_img = None
        self._tile = grain_tile
        self._grid = grid
        self._job = None
        self.bind("<Configure>", self._on_resize)
        self._build_grain()

    def _build_grain(self):
        t = self._tile
        try:
            img = tk.PhotoImage(width=t, height=t)
            rows = []
            for _ in range(t):
                row = []
                for _ in range(t):
                    r = self._rng.random()
                    if r < 0.02:
                        row.append("#d9d0b8")
                    elif r < 0.09:
                        row.append("#e6e0d2")
                    else:
                        row.append(PAPER)
                rows.append("{" + " ".join(row) + "}")
            img.put(" ".join(rows))
            self._grain_img = img  # keep a reference
        except Exception:
            self._grain_img = None

    def _on_resize(self, _e=None):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        self._job = self.after(150, self.redraw)

    def redraw(self):
        self._job = None
        try:
            w, h = self.winfo_width(), self.winfo_height()
        except Exception:
            return
        if w < 10 or h < 10:
            return
        self.delete("paper")
        if self._grain_img is not None:
            t = self._tile
            x = 0
            while x < w:
                y = 0
                while y < h:
                    self.create_image(x, y, image=self._grain_img,
                                      anchor="nw", tags="paper")
                    y += t
                x += t
        # dot-grid ruling
        g = self._grid
        x = g
        while x < w:
            y = g
            while y < h:
                self.create_oval(x - 1, y - 1, x + 1, y + 1, fill=DOTS,
                                 outline="", tags="paper")
                y += g
            x += g
        # bound spine + stitching
        self.create_rectangle(0, 0, 30, h, fill=SPINE, outline="",
                              tags="paper")
        self.create_line(15, 8, 15, h - 8, fill=STITCH, width=1,
                         dash=(6, 5), tags="paper")
        # red margin rule
        self.create_line(64, 0, 64, h, fill=MARGIN, width=1, tags="paper")


# ------------------------------------------------------- rubber stamp
STAMP_SLOPE = math.tan(math.radians(-4))


def stamp_box(canvas, cx, cy, hw, hh, color, width=2, tags=None):
    """Sloped double-rule box, like a hand-struck stamp."""
    tags = tags or ()
    for inset, wd in ((0, width), (4, 1)):
        x0, x1 = cx - hw + inset, cx + hw - inset
        y0, y1 = cy - hh + inset, cy + hh - inset
        canvas.create_polygon(
            x0, y0 + STAMP_SLOPE * (x0 - cx),
            x1, y0 + STAMP_SLOPE * (x1 - cx),
            x1, y1 + STAMP_SLOPE * (x1 - cx),
            x0, y1 + STAMP_SLOPE * (x0 - cx),
            outline=color, fill="", width=wd, tags=tags)


class Stamp(tk.Canvas):
    """A rubber-stamp state mark: sloped tracked type in a double-rule
    box with a misprint offset, struck in stamp red or pencil grey.

    strike() replays the landing: overshoot, press, settle."""

    KINDS = {
        "eaten": STAMP,
        "danger": STAMP,
        "edition": INK,
        "closed": PENCIL,
        "pending": PENCIL_LT,
    }

    def __init__(self, master, height=52, bg=CARD, font=None, tracking=2,
                 **kw):
        super().__init__(master, height=height, bg=bg,
                         highlightthickness=0, bd=0, **kw)
        self._spec = font or ("Outfit", 13, "bold")
        self._base_size = self._spec[1]
        self._tracking = tracking
        self._bg = bg
        self._text = ""
        self._kind = "eaten"
        self._job = None

    def set(self, text, kind="eaten"):
        self._cancel()
        self._text, self._kind = text or "", kind
        self._draw(1.0, 0, 0, 0.0)

    def strike(self, text=None, kind=None):
        """Replay the stamp landing after a toggle to eaten."""
        if text is not None:
            self._text = text
        if kind is not None:
            self._kind = kind
        self._cancel()
        self._frames = [(1.45, 3, 3, 0.35),
                        (1.15, 1, 1, 0.15),
                        (1.0, 0, 0, 0.0)]
        self._step_strike()

    def _step_strike(self):
        self._job = None
        if not getattr(self, "_frames", None) or not self.winfo_exists():
            return
        s, dx, dy, boost = self._frames.pop(0)
        try:
            self._draw(s, dx, dy, boost)
        except Exception:
            return
        if self._frames:
            try:
                self._job = self.after(55, self._step_strike)
            except Exception:
                pass

    def _cancel(self):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _draw(self, scale, dx, dy, boost):
        color = self.KINDS.get(self._kind, STAMP)
        if boost:
            color = lerp_hex(color, "#000000", boost)
        self.delete("all")
        self.configure(bg=self._bg)
        if not self._text:
            self.configure(width=1)
            return
        size = max(6, int(round(self._base_size * scale)))
        spec = (self._spec[0], size) + tuple(self._spec[2:])
        font = tkfont.Font(font=spec)
        widths = [font.measure(c) + self._tracking for c in self._text]
        total = sum(widths)
        h = font.metrics("linespace")
        try:
            cy = int(self.cget("height")) // 2 + dy
        except Exception:
            cy = 27 + dy
        cx = total / 2 + 12 + dx
        ghost = lerp_hex(color, self._bg, 0.55)
        stamp_box(self, cx, cy, total / 2 + 10, h / 2 + 8, color, width=2)
        x = cx - total / 2
        for c, wdx in zip(self._text, widths):
            char_cx = x + (wdx - self._tracking) / 2
            y = cy + STAMP_SLOPE * (char_cx - cx)
            self.create_text(char_cx + 1.2, y + 1, text=c, fill=ghost,
                             font=font, anchor="center")
            self.create_text(char_cx, y, text=c, fill=color, font=font,
                             anchor="center")
            x += wdx
        self.configure(width=int(total) + 28)


# ------------------------------------------------------- pencil marks
class PencilBox(tk.Canvas):
    """Allowance gauge as a pencil box: one ruled cell per miss, struck
    through with hand X marks (half misses get a single slash). Overflow
    past the allowance is stamped red."""

    def __init__(self, master, cell=15, gap=5, per_row=25, bg=PAPER, **kw):
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, **kw)
        self._cell, self._gap, self._row = cell, gap, per_row
        self._bg = bg
        self._used = 0.0
        self._allowed = 25

    def set_value(self, used, allowed=25):
        self._used = max(0.0, float(used))
        self._allowed = max(1, int(round(allowed)))
        self.redraw()

    def redraw(self):
        self.delete("all")
        full = int(self._used)
        half = 1 if self._used - full >= 0.5 else 0
        cells = max(self._allowed, full + half)
        rows = max(1, math.ceil(cells / self._row))
        step = self._cell + self._gap
        self.configure(height=rows * step + 4)
        for i in range(cells):
            r, c = divmod(i, self._row)
            x0 = c * step + 2
            y0 = r * step + 2
            x1, y1 = x0 + self._cell, y0 + self._cell
            over = i >= self._allowed
            self.create_rectangle(x0, y0, x1, y1, outline=RULE_DK,
                                  width=1)
            if i < full:
                col = RED if over else INK
                self.create_line(x0 + 3, y0 + 3, x1 - 3, y1 - 3, fill=col,
                                 width=2)
                self.create_line(x0 + 3, y1 - 3, x1 - 3, y0 + 3, fill=col,
                                 width=2)
            elif i == full and half:
                col = RED if over else INK
                self.create_line(x0 + 3, y1 - 3, x1 - 3, y0 + 3, fill=col,
                                 width=2)


class MarksCanvas(tk.Canvas):
    """One row's B/L/D boxes with hand-drawn checks, like margin ticks."""

    def __init__(self, master, width=150, height=20, bg=PAPER, **kw):
        super().__init__(master, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, **kw)
        self._bg = bg
        self._font = tkfont.Font(font=("DM Mono", 9))

    def set(self, b, l, d, dim=False, bg=None):
        self.delete("all")
        self.configure(bg=bg or self._bg)
        ink = PENCIL if dim else INK
        x = 2
        for letter, val in (("B", b), ("L", l), ("D", d)):
            self.create_text(x + 3, 10, text=letter, fill=ink,
                             font=self._font, anchor="w")
            bx = x + 16
            self.create_rectangle(bx, 4, bx + 12, 16, outline=ink, width=2)
            if val == "yes":
                self.create_line(bx + 2, 10, bx + 6, 13, bx + 11, 5,
                                 fill=ink, width=2)
            elif val == "na":
                self.create_line(bx + 3, 10, bx + 10, 10, fill=ink,
                                 width=2)
            x += 44


# ------------------------------------------------------- timeline gut
class TimelineGutter(tk.Canvas):
    """Stitched thread running down the history leaves, with a knot per
    day: ink-filled when the day is complete, open when it is not, stamp
    red for the selected leaf, faint for previous-cycle days, ringed for
    today."""

    def __init__(self, master, width=26, bg=PAPER, **kw):
        super().__init__(master, width=width, bg=bg, highlightthickness=0,
                         bd=0, **kw)
        self._bg = bg
        self._knots = []
        self.bind("<Configure>", lambda e: self.redraw())

    def set_knots(self, knots):
        """knots: [(y, kind, is_today)] with kind in done/open/prev."""
        self._knots = list(knots)
        self.redraw()

    def redraw(self):
        self.delete("all")
        try:
            w, h = self.winfo_width(), self.winfo_height()
        except Exception:
            return
        if w < 4 or h < 10:
            return
        cx = w // 2
        self.create_line(cx, 4, cx, h - 4, fill=STITCH, width=1,
                         dash=(5, 4))
        for y, kind, is_today in self._knots:
            if kind == "selected":
                fill, edge = STAMP, STAMP
            elif kind == "done":
                fill, edge = INK, INK
            elif kind == "prev":
                fill, edge = self._bg, PENCIL_LT
            else:
                fill, edge = self._bg, INK_SOFT
            if is_today:
                self.create_oval(cx - 7, y - 7, cx + 7, y + 7, outline=edge,
                                 width=1)
            self.create_oval(cx - 4, y - 4, cx + 4, y + 4, outline=edge,
                             fill=fill, width=2)
            self.create_line(cx + 4, y, w - 1, y, fill=edge, width=1)


# ------------------------------------------------------- wax seal
class Seal(tk.Canvas):
    """Circular COMPLETE seal for fully-logged days."""

    def __init__(self, master, size=28, bg=PAPER, **kw):
        super().__init__(master, width=size, height=size, bg=bg,
                         highlightthickness=0, bd=0, **kw)
        self._size = size
        self._bg = bg

    def set(self, sealed, bg=None):
        self.delete("all")
        self.configure(bg=bg or self._bg)
        if not sealed:
            return
        s = self._size
        self.create_oval(2, 3, s - 2, s - 1, outline=STAMP, width=2)
        self.create_oval(5, 6, s - 5, s - 4, outline=STAMP, width=1)
        self.create_line(s * 0.32, s * 0.54, s * 0.46, s * 0.68,
                         s * 0.70, s * 0.34, fill=STAMP, width=2)


# ------------------------------------------------------- page turn
class PageTurn:
    """A page-flip wipe: a blank sheet sweeps across a container,
    revealing the freshly swapped content beneath it."""

    _busy = False

    @classmethod
    def play(cls, parent, box, direction=+1):
        if cls._busy:
            return
        x, y, w, h = box
        if w < 50 or h < 50:
            return
        try:
            cover = tk.Frame(parent, bg="#e7e0cf", bd=0)
            edge = tk.Frame(cover, bg=RULE_DK, width=3, bd=0)
            edge.pack(side="left" if direction > 0 else "right", fill="y")
            cover.place(x=x, y=y, width=w, height=h)
        except Exception:
            return
        cls._busy = True
        steps = 9

        def move(i=0):
            try:
                if i >= steps or not cover.winfo_exists():
                    raise StopIteration
                nx = x - direction * int(w * (i + 1) / steps)
                cover.place(x=nx, y=y, width=w, height=h)
                cover.after(22, lambda: move(i + 1))
            except StopIteration:
                try:
                    cover.destroy()
                except Exception:
                    pass
                cls._busy = False
            except Exception:
                try:
                    cover.destroy()
                except Exception:
                    pass
                cls._busy = False

        move()


# ------------------------------------------------------- scroll frame
class ScrollFrame(tk.Frame):
    """Vertically scrollable container."""

    def __init__(self, master, bg=PAPER, **kw):
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vbar = tk.Scrollbar(self, orient="vertical",
                                 command=self.canvas.yview,
                                 troughcolor=bg, background=RULE_DK, bd=0,
                                 highlightthickness=0, width=12,
                                 activebackground=PENCIL)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner,
                                              anchor="nw")
        self._win_h = None
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)

    def _on_scroll(self, first, last):
        try:
            need = int(self.canvas.winfo_height()) < \
                self.inner.winfo_reqheight()
        except Exception:
            need = False
        if need:
            if not self.vbar.winfo_ismapped():
                self.vbar.pack(side="right", fill="y", padx=(2, 0))
            self.vbar.set(first, last)
        elif self.vbar.winfo_ismapped():
            self.vbar.pack_forget()
        try:
            self.canvas.yview_moveto(first)
        except Exception:
            pass

    def _on_inner(self, _e=None):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass
        self._stretch()

    def _on_canvas(self, e):
        try:
            self.canvas.itemconfigure(self._win, width=e.width)
        except Exception:
            pass
        self._stretch()
        try:
            self._on_scroll(*self.canvas.yview())
        except Exception:
            pass

    def _stretch(self):
        try:
            h = self.canvas.winfo_height()
        except Exception:
            return
        if h <= 1:
            return
        want = max(self.inner.winfo_reqheight(), h)
        if self._win_h != want:
            self._win_h = want
            try:
                self.canvas.itemconfigure(self._win, height=want)
            except Exception:
                pass

    def refresh(self):
        self._win_h = None
        self._on_inner()


# ------------------------------------------------------ legacy bits
class Check(tk.Frame):
    """Custom square checkbox drawn on a canvas."""

    BOX = 16

    def __init__(self, master, text, variable=None, command=None, fg=INK,
                 bg=CARD, accent=GREEN, enabled=True, font=None,
                 note=None):
        super().__init__(master, bg=bg, bd=0, highlightthickness=0)
        self._var = variable if variable is not None else tk.BooleanVar(
            value=False)
        self._command = command
        self._accent = accent
        self._fg = fg
        self._enabled = enabled
        self._note = note

        self.canvas = tk.Canvas(self, width=self.BOX, height=self.BOX,
                                bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack(side="left", pady=(1, 0))
        self.text = tk.Label(self, text="", bg=bg, fg=fg, font=font or
                             body(12), anchor="w", justify="left")
        self.text.pack(side="left", padx=(9, 0))
        self.set_text(text)
        self._redraw()

        for w in (self.canvas, self.text):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._hover)
            w.bind("<Leave>", lambda e: self.canvas.configure(cursor=""))
        self._var.trace_add("write", lambda *a: self._redraw())

    def _hover(self, _event=None):
        if self._enabled:
            self.canvas.configure(cursor="hand2")

    def configure_state(self, text, note=None, enabled=True):
        self._note = note
        self._enabled = enabled
        self.set_text(text)
        self._redraw()

    def set_text(self, text):
        label = text if not self._note else f"{text}  {self._note}"
        self.text.configure(
            text=label,
            fg=self._fg if self._enabled else PENCIL)

    def set_accent(self, color):
        self._accent = color
        self._redraw()

    def _click(self, _event=None):
        if not self._enabled:
            return
        self._var.set(not self._var.get())
        if self._command:
            self._command()

    def _redraw(self):
        c = self.canvas
        c.delete("all")
        on = self._var.get()
        accent = self._accent if self._enabled else PENCIL
        edge = accent if on else (RULE_DK if self._enabled else RULE)
        c.create_rectangle(0, 0, self.BOX - 1, self.BOX - 1,
                           outline=edge, fill=accent if on else PAPER,
                           width=2)
        if on:
            c.create_line(4, 4, self.BOX - 5, self.BOX - 5, fill=PAPER,
                          width=2)
            c.create_line(self.BOX - 5, 4, 4, self.BOX - 5, fill=PAPER,
                          width=2)
        self.text.configure(fg=self._fg if (self._enabled and on) else
                            (INK if self._enabled else PENCIL))


class Meter(tk.Canvas):
    """Chunky segmented bar: one cell per unit, filled up to `used`."""

    def __init__(self, master, height=18, bg=CARD, fill=GREEN, over=RED,
                 empty=RULE, segments=25, **kw):
        super().__init__(master, height=height, bg=bg, highlightthickness=1,
                         highlightbackground=RULE, bd=0, **kw)
        self._fill, self._over, self._empty = fill, over, empty
        self._segments = max(1, segments)
        self._used = 0.0
        self.bind("<Configure>", lambda e: self.redraw())

    def set_value(self, used, total=None):
        if total:
            self._segments = max(1, total)
        self._used = max(0.0, float(used))
        self.redraw()

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        gap = 2
        seg_w = max(2, (w - gap * (self._segments - 1)) // self._segments)
        top, bot = 2, h - 3
        over = self._used > self._segments
        for i in range(self._segments):
            x = i * (seg_w + gap)
            part = min(1.0, max(0.0, self._used - i))
            if part <= 0:
                self.create_rectangle(x, top, x + seg_w, bot,
                                      outline=self._empty, fill="")
                continue
            colour = self._over if over else self._fill
            if part >= 1.0:
                self.create_rectangle(x, top, x + seg_w, bot, fill=colour,
                                      outline="")
            else:
                self.create_rectangle(x, top, x + seg_w, bot,
                                      outline=self._empty, fill="")
                self.create_rectangle(x, top, x + max(1, int(seg_w * part)),
                                      bot, fill=colour, outline="")
