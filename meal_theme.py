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
VEG       = "#2e7d46"   # shakahari green, for the veg mark
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


def _round_rect(cv, x0, y0, x1, y1, r, **kw):
    """A rounded rectangle from ovals + bars; seamless when fill and
    outline share a colour."""
    cv.create_oval(x0, y0, x0 + 2 * r, y1, **kw)
    cv.create_oval(x1 - 2 * r, y0, x1, y1, **kw)
    cv.create_rectangle(x0 + r, y0, x1 - r, y1, **kw)
    cv.create_rectangle(x0, y0 + r, x1, y1 - r, **kw)


class RoundedButton(tk.Canvas):
    """A softly rounded tool button: ink outline on paper; the primary
    action arrives filled in ink and warms to stamp red on hover."""

    def __init__(self, master, text, command, kind="ghost", bg=PAPER,
                 font=None, padx=18, pady=9, radius=10, **kw):
        self._font = tkfont.Font(font=font or mono(10))
        self._text = text
        self._kind = kind
        self._bg = bg
        w = self._font.measure(text) + padx * 2
        h = self._font.metrics("linespace") + pady * 2
        super().__init__(master, width=w, height=h, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2", **kw)
        self._command = command
        self._radius = radius
        self._draw(False)
        self.bind("<Button-1>", lambda e: self._command())
        self.bind("<Enter>", lambda e: self._draw(True))
        self.bind("<Leave>", lambda e: self._draw(False))

    def _draw(self, hot):
        self.delete("all")
        w, h = int(self.cget("width")), int(self.cget("height"))
        r = min(self._radius, h // 2 - 1)
        if self._kind == "primary":
            fill = STAMP if hot else INK
            self._round_rect_bg(w, h, r, fill, fill, PAPER)
        else:
            fill = CARD if hot else "#eadfc6"
            edge = INK if hot else RULE_DK
            fg = INK if hot else INK_SOFT
            self._round_rect_bg(w, h, r, fill, edge, fg)

    def _round_rect_bg(self, w, h, r, fill, edge, fg):
        _round_rect(self, 1, 1, w - 1, h - 1, r, fill=fill, outline=edge,
                    width=1.5)
        self.create_text(w / 2, h / 2, text=self._text, fill=fg,
                         font=self._font)


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
        self._fonts = {}

    def set(self, text, kind="eaten"):
        self._cancel()
        self._text, self._kind = text or "", kind
        # Fix the width up front: scaling the ink mid-strike must never
        # move the layout, or the whole card breathes and the motion judders.
        self.configure(width=self._measure(1.0))
        self._draw(1.0, 0, 0, 0.0)

    def strike(self, text=None, kind=None):
        """Replay the stamp landing after a toggle to eaten: overshoot,
        press, settle over six eased frames."""
        if text is not None:
            self._text = text
        if kind is not None:
            self._kind = kind
        self._cancel()
        self.configure(width=self._measure(1.0))
        self._frames = [(1.50, 4, 4, 0.40),
                        (1.34, 3, 3, 0.30),
                        (1.20, 2, 2, 0.22),
                        (1.10, 1, 1, 0.12),
                        (1.03, 0, 0, 0.05),
                        (1.00, 0, 0, 0.00)]
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
                self._job = self.after(30, self._step_strike)
            except Exception:
                pass

    def _cancel(self):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _scaled_font(self, scale):
        # Cache per size: minting a font object every animation frame
        # stutters the strike.
        size = max(6, int(round(self._base_size * scale)))
        font = self._fonts.get(size)
        if font is None:
            spec = (self._spec[0], size) + tuple(self._spec[2:])
            font = self._fonts[size] = tkfont.Font(font=spec)
        return font

    def _measure(self, scale):
        font = self._scaled_font(scale)
        total = sum(font.measure(c) + self._tracking for c in self._text)
        return int(total * 1.6) + 28 if self._text else 1

    def _draw(self, scale, dx, dy, boost):
        color = self.KINDS.get(self._kind, STAMP)
        if boost:
            color = lerp_hex(color, "#000000", boost)
        self.delete("all")
        self.configure(bg=self._bg)
        if not self._text:
            return
        font = self._scaled_font(scale)
        widths = [font.measure(c) + self._tracking for c in self._text]
        total = sum(widths)
        h = font.metrics("linespace")
        try:
            width = int(self.cget("width"))
        except Exception:
            width = int(total * 1.6) + 28
        cx = width / 2 + dx
        try:
            cy = int(self.cget("height")) // 2 + dy
        except Exception:
            cy = 27 + dy
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


# ------------------------------------------------------- corner ticks
class CornerTicks(tk.Canvas):
    """Crop-mark corners instead of a box: four short ink rules that bound
    an entry without boxing it. Eaten entries tick in ink."""

    def __init__(self, master, arm=26, bg=PAPER, **kw):
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, **kw)
        self._ink = RULE_DK
        self._arm = arm
        self.bind("<Configure>", lambda e: self.draw())

    def set_ink(self, color):
        if color != self._ink:
            self._ink = color
            self.draw()

    def draw(self):
        self.delete("all")
        try:
            w, h = self.winfo_width(), self.winfo_height()
        except Exception:
            return
        if w < 30 or h < 30:
            return
        m, a, c = 5, self._arm, self._ink
        for x0, y0, dx, dy in ((m, m, 1, 1), (w - m, m, -1, 1),
                               (m, h - m, 1, -1), (w - m, h - m, -1, -1)):
            self.create_line(x0, y0, x0 + dx * a, y0, fill=c, width=2)
            self.create_line(x0, y0, x0, y0 + dy * a, fill=c, width=2)


# ------------------------------------------------------- ephemera
class Ephemera(tk.Canvas):
    """Margin furniture: an asterism divider with hairlines, a bold
    coffee ring and a stamped shakahari mark."""

    RING = "#a9885f"

    def __init__(self, master, height=150, bg=PAPER, **kw):
        super().__init__(master, height=height, bg=bg, highlightthickness=0,
                         bd=0, **kw)
        self.bind("<Configure>", lambda e: self.redraw())

    def redraw(self):
        self.delete("all")
        try:
            w, h = self.winfo_width(), self.winfo_height()
        except Exception:
            return
        if w < 60 or h < 20:
            return
        cy = h // 2 - 4
        self.create_line(0, cy + 3, max(0, w - 250), cy - 2, fill=RULE,
                         width=1)
        cx = max(60, (w - 230) // 2)
        for dx, dy in ((-11, 6), (11, 6), (0, -9)):
            x, y = cx + dx, cy + dy
            self.create_line(x - 6, y, x + 6, y, fill=RULE_DK, width=1)
            self.create_line(x, y - 6, x, y + 6, fill=RULE_DK, width=1)
        rx, ry = w - 96, cy + 6
        self.create_oval(rx - 64, ry - 58, rx + 64, ry + 58,
                         outline=self.RING, width=7, stipple="gray50")
        self.create_oval(rx - 52, ry - 47, rx + 52, ry + 47,
                         outline=self.RING, width=2)
        self.create_oval(rx + 72, ry + 42, rx + 76, ry + 46,
                         fill=self.RING, outline="")
        for sx, sy in ((rx + 90, ry - 40), (rx - 60, ry + 62)):
            self.create_line(sx - 5, sy, sx + 5, sy, fill=PENCIL_LT,
                             width=1)
            self.create_line(sx, sy - 5, sx, sy + 5, fill=PENCIL_LT,
                             width=1)
        self._veg_mark(rx - 108, ry + 8)

    def _veg_mark(self, x, y):
        self.create_rectangle(x - 13, y - 13, x + 13, y + 13, outline=VEG,
                              width=2)
        self.create_rectangle(x - 10, y - 10, x + 10, y + 10, outline=VEG,
                              width=1)
        self.create_oval(x - 6, y - 6, x + 6, y + 6, fill=VEG, outline="")


# ------------------------------------------------------- grove
class Grove(tk.Canvas):
    """Tangerine trees for the empty stretches: deep marigold fruit and
    olive leaves on bark branches, flat fills with depth. Mode 'grove'
    rises from the bottom-left corner to fill a void; 'sprig' is a small
    cutting for panel footers."""

    FRUIT = "#c96a24"
    FRUIT_DK = "#96501c"
    FRUIT_HI = "#f2c078"
    LEAF = "#5a7a2a"
    LEAF_DK = "#42591d"
    BARK = "#6b4a2f"
    SPARK = "#d9a441"
    WASH = "#e6dfcc"

    def __init__(self, master, mode="grove", bg=PAPER, **kw):
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, **kw)
        self._mode = mode
        self._folio = ""
        self._fonts = {}
        self.bind("<Configure>", lambda e: self.redraw())

    def set_folio(self, text):
        if text != self._folio:
            self._folio = text
            self.redraw()

    def _folio_font(self, size):
        if size not in self._fonts:
            self._fonts[size] = tkfont.Font(
                font=("Playfair Display", size, "bold"))
        return self._fonts[size]

    def _branch(self, points, width):
        flat = [c for p in points for c in p]
        self.create_line(*flat, fill=self.BARK, width=width, smooth=True,
                         capstyle="round")

    def _leaf(self, x, y, length, angle_deg):
        a = math.radians(angle_deg)
        dx, dy = math.cos(a), math.sin(a)
        px, py = -dy, dx
        half, third = length / 2, length * 0.21
        tip = (x + dx * half, y + dy * half)
        base = (x - dx * half, y - dy * half)
        m1 = (x + px * third + dx * half * 0.12,
              y + py * third + dy * half * 0.12)
        m2 = (x - px * third + dx * half * 0.12,
              y - py * third + dy * half * 0.12)
        self.create_polygon([tip, m1, base, m2], fill=self.LEAF,
                            outline=self.LEAF_DK, width=1.5)
        self.create_line(base, tip, fill=self.LEAF_DK, width=1)

    def _fruit(self, x, y, r):
        self.create_oval(x - r, y - r, x + r, y + r, fill=self.FRUIT,
                         outline=self.FRUIT_DK, width=2)
        self.create_oval(x - r * 0.45, y - r * 0.52, x - r * 0.12,
                         y - r * 0.2, fill=self.FRUIT_HI, outline="")
        self.create_line(x, y - r, x, y - r - 7, fill=self.FRUIT_DK,
                         width=2)
        self._leaf(x + 7, y - r - 9, 17, -28)

    def _spark(self, x, y, r):
        self.create_line(x - r, y, x + r, y, fill=self.SPARK, width=2)
        self.create_line(x, y - r, x, y + r, fill=self.SPARK, width=2)
        self.create_polygon([(x, y - r * 0.5), (x + r * 0.18, y),
                             (x, y + r * 0.5), (x - r * 0.18, y)],
                            fill=self.SPARK, outline="")

    def redraw(self):
        self.delete("all")
        try:
            w, h = self.winfo_width(), self.winfo_height()
        except Exception:
            return
        if w < 80 or h < 60:
            return
        if self._mode == "sprig":
            self._sprig(w, h)
            return
        if self._folio:
            size = max(80, min(190, int(h * 0.62)))
            self.create_text(56, h * 0.44, text=self._folio, fill=self.WASH,
                             font=self._folio_font(size), anchor="w")
        btw = lambda f: w * f
        self._branch([(14, h - 6), (btw(0.09), h - 74), (btw(0.17), h - 148),
                      (btw(0.27), h * 0.30)], 6)
        self._branch([(btw(0.09), h - 74), (btw(0.16), h - 60),
                      (btw(0.22), h - 78)], 3)
        self._branch([(btw(0.17), h - 148), (btw(0.24), h - 168),
                      (btw(0.30), h - 158)], 3)
        self._branch([(btw(0.05), h - 40), (btw(0.02), h - 90)], 3)
        for lx, ly, ll, la in ((btw(0.06), h - 60, 34, -50),
                               (btw(0.13), h - 100, 38, 30),
                               (btw(0.11), h - 130, 30, -120),
                               (btw(0.20), h - 120, 34, 55),
                               (btw(0.24), h - 190, 30, -40),
                               (btw(0.16), h - 210, 28, 140),
                               (btw(0.04), h - 70, 26, 160),
                               (btw(0.28), h - 130, 26, 20)):
            self._leaf(lx, ly, ll, la)
        self._fruit(btw(0.22), h - 78, 19)
        self._fruit(btw(0.30), h - 158, 15)
        self._fruit(btw(0.045), h - 108, 13)
        for sx, sy, sr in ((btw(0.36), h * 0.22, 10),
                           (btw(0.45), h * 0.42, 7),
                           (btw(0.14), h * 0.12, 8),
                           (btw(0.55), h * 0.18, 9)):
            self._spark(sx, sy, sr)

    def _sprig(self, w, h):
        cy = h // 2
        self._branch([(8, cy + 8), (w * 0.30, cy), (w * 0.52, cy - 6)], 4)
        self._leaf(w * 0.12, cy - 2, 26, -35)
        self._leaf(w * 0.20, cy + 10, 24, 150)
        self._leaf(w * 0.34, cy - 12, 24, -20)
        self._leaf(w * 0.42, cy + 4, 22, 160)
        self._fruit(w * 0.27, cy - 4, 14)
        self._spark(w * 0.60, cy - 16, 8)
        self._spark(w * 0.06, cy - 22, 6)


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
