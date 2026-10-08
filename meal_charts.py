"""Hand-drawn pixel charts on Tk canvases.

The layout functions are pure (no Tk) so the geometry can be unit tested
headlessly; the renderers just paint what the layout returns. Bars are snapped
to integers and no anti-aliasing is used anywhere, which keeps everything
axis-aligned and crisp.
"""
import math
import random
import tkinter as tk

import meal_theme as th

PAD = (10, 12, 26, 34)   # left, top, right, bottom


def nice_ceiling(value, target=4):
    """Round `value` up to a friendly axis maximum."""
    if value is None or value <= 0:
        return 1.0
    step = value / float(target)
    mag = 10 ** math.floor(math.log10(step))
    for mult in (1, 2, 2.5, 5, 10):
        if step <= mult * mag:
            step = mult * mag
            break
    else:
        step = 10 * mag
    return math.ceil(value / step) * step


def layout_bars(values, width, height, pad=PAD, target_ticks=4, ymax=None):
    """Bar geometry for a flat series of values."""
    left, top, right, bottom = pad
    x0, y0 = left, top
    x1 = max(x0 + 1, width - right)
    y1 = max(y0 + 1, height - bottom)
    plot_w, plot_h = x1 - x0, y1 - y0
    if ymax is None:
        ymax = nice_ceiling(max(values) if values else 0.0, target_ticks)

    bars = []
    n = max(1, len(values))
    slot = plot_w / float(n)
    bar_w = max(1, int(round(slot * 0.68)))
    for i, v in enumerate(values):
        bx = x0 + i * slot + (slot - bar_w) / 2.0
        h = 0 if not v or v <= 0 else int(round(v / ymax * plot_h))
        bars.append((int(bx), y1 - h, int(bx) + bar_w, y1, v))
    ticks = [(ymax * i / float(target_ticks),
              y1 - plot_h * i / float(target_ticks)) for i in range(target_ticks + 1)]
    return {"bars": bars, "plot": (x0, y0, x1, y1), "ymax": ymax,
            "ticks": ticks, "slot": slot, "x0": x0}


def layout_step(values, width, height, pad=PAD, target_ticks=4):
    """Staircase geometry for a cumulative series."""
    left, top, right, bottom = pad
    x0, y0 = left, top
    x1 = max(x0 + 1, width - right)
    y1 = max(y0 + 1, height - bottom)
    plot_w, plot_h = x1 - x0, y1 - y0
    ymax = nice_ceiling(max(values) if values else 0.0, target_ticks)

    n = max(1, len(values))
    step = plot_w / float(n)
    points = []
    for i, v in enumerate(values):
        px = x0 + i * step
        py = y1 - (0 if not v or v <= 0 else (v / ymax * plot_h))
        points.append((int(px), int(py)))
    ticks = [(ymax * i / float(target_ticks),
              y1 - plot_h * i / float(target_ticks)) for i in range(target_ticks + 1)]
    return {"points": points, "plot": (x0, y0, x1, y1), "ymax": ymax,
            "ticks": ticks, "step": step, "x1": x1, "y1": y1}


def _fmt(v):
    return f"{v:.1f}"


class Chart(tk.Canvas):
    """Base canvas: black background, blocky grid, y-axis ticks."""

    def __init__(self, master, height=170, bg=th.PANEL, grid=th.BORDER,
                 tick_fg=th.TEXT_MUTE, pad=PAD, **kw):
        super().__init__(master, height=height, bg=bg, highlightthickness=1,
                         highlightbackground=th.BORDER, bd=0, **kw)
        self._grid = grid
        self._tick_fg = tick_fg
        self._pad = pad
        self._vgrid = True
        self.bind("<Configure>", lambda e: self.redraw())

    def _frame(self, ticks):
        x0, y0, x1, y1 = self._plot_rect()
        if self._vgrid:
            for i in range(6):
                gx = x0 + (x1 - x0) * i / 5.0
                self.create_line(int(gx), y0, int(gx), y1, fill=self._grid)
        for value, gy in ticks:
            self.create_line(x0, int(gy), x1, int(gy), fill=self._grid)
            self.create_text(x0 - 5, int(gy), text=_fmt(value), fill=self._tick_fg,
                             font=th.mono(8), anchor="e")
        self.create_line(x0, y1, x1, y1, fill=th.BORDER_HI)

    def _plot_rect(self):
        left, top, right, bottom = self._pad
        w, h = self.winfo_width(), self.winfo_height()
        return (left, top, max(left + 1, w - right), max(top + 1, h - bottom))

    def redraw(self):
        self.delete("all")

    def _empty(self, msg="NO DATA"):
        self.create_text(self.winfo_width() / 2, self.winfo_height() / 2,
                         text=msg, fill=th.TEXT_MUTE, font=th.display(10))


class BarChart(Chart):
    """Vertical bars, one per value, with optional per-bar colours.

    With thin=True the bars become restrained monochrome lines with small
    square caps (the Insights rhythm); zero days collapse to a hairline tick.
    """

    def __init__(self, master, color=th.TEXT, value_fmt=True, ymax=None,
                 thin=False, vgrid=True, target_ticks=4, **kw):
        super().__init__(master, **kw)
        self._color = color
        self._values = []
        self._labels = []
        self._colors = None
        self._value_fmt = value_fmt
        self._missing = None
        self._ymax = ymax
        self._thin = thin
        self._vgrid = vgrid
        self._target_ticks = target_ticks

    def set_data(self, values, labels=None, colors=None, missing=None):
        self._values = list(values)
        self._labels = list(labels) if labels else []
        self._colors = list(colors) if colors else None
        self._missing = list(missing) if missing else None
        self.redraw()

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        if not self._values:
            self._empty()
            return
        L = layout_bars(self._values, w, h, self._pad,
                        target_ticks=self._target_ticks, ymax=self._ymax)
        self._frame(L["ticks"])
        n = len(self._values)
        label_every = max(1, int(math.ceil(n / 12.0)))
        for i, (bx0, by0, bx1, by1, v) in enumerate(L["bars"]):
            missing = bool(self._missing[i]) if self._missing else False
            color = th.BORDER if missing else (
                self._colors[i] if self._colors else self._color)
            cx = int((bx0 + bx1) / 2)
            if self._thin:
                if by1 - by0 <= 0:
                    tick = th.BORDER if missing else th.BORDER_HI
                    self.create_rectangle(cx - 3, by1 - 2, cx + 4, by1,
                                          fill=tick, outline="")
                else:
                    self.create_line(cx, by1, cx, by0, fill=color, width=3)
                    self.create_rectangle(cx - 3, by0 - 4, cx + 4, by0 + 1,
                                          fill=color, outline="")
            elif by1 - by0 <= 0:
                self.create_rectangle(bx0, by1 - 2, bx1, by1, fill=th.BORDER_HI)
            else:
                self.create_rectangle(bx0, by0, bx1, by1, fill=color)
                self.create_rectangle(bx0, by0, bx1, by0 + 2, fill=th.TEXT)
            if self._value_fmt and not missing and v > 0:
                self.create_text((bx0 + bx1) / 2, by0 - 7, text=_fmt(v),
                                 fill=th.TEXT_DIM, font=th.mono(8))
            if self._labels and i % label_every == 0:
                self.create_text((bx0 + bx1) / 2, by1 + 9, text=self._labels[i],
                                 fill=th.TEXT_MUTE, font=th.mono(8))


class SketchBars(Chart):
    """Hand-ruled bars for the journal: wobbly triple-stroke columns with
    sketch-ring caps, Caveat ticks and day labels on graph paper.

    The wobble comes from a fixed seed, so redraws never shimmer."""

    def __init__(self, master, color=th.INK, faint=th.PENCIL_LT,
                 ymax=3.0, **kw):
        super().__init__(master, **kw)
        self._color = color
        self._faint = faint
        self._ymax = ymax
        self._values = []
        self._labels = []
        self._colors = None
        self._missing = None

    def set_data(self, values, labels=None, colors=None, missing=None):
        self._values = list(values)
        self._labels = list(labels) if labels else []
        self._colors = list(colors) if colors else None
        self._missing = list(missing) if missing else None
        self.redraw()

    def _hand_line(self, x0, y0, x1, y1, fill, width=1, wobble=1.0):
        """A ruled line with a hand echo: the stroke plus a fainter twin
        offset by a pixel, like ink bleeding through paper."""
        self.create_line(x0, y0, x1, y1, fill=fill, width=width)
        self.create_line(x0 + wobble, y0 + wobble, x1 + wobble, y1 + wobble,
                         fill=th.RULE_DK, width=1)

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        if not self._values:
            self._empty()
            return
        rng = random.Random(9)
        left, top, right, bottom = self._pad
        x0 = left
        x1 = max(x0 + 1, w - right)
        y1 = max(top + 1, h - bottom)
        plot_h = y1 - top
        n = len(self._values)
        slot = (x1 - x0) / float(max(1, n))

        def y_of(v):
            return y1 - v / self._ymax * plot_h

        # hand-ruled gridlines with Caveat ticks, every half meal
        steps = int(round(self._ymax * 2))
        for i in range(steps + 1):
            v = self._ymax * i / steps
            gy = int(y_of(v))
            self.create_line(x0, gy, x1, gy + rng.choice((-1, 0, 1)),
                             fill=self._grid)
            self.create_text(x0 - 8, gy, text=f"{v:g}", fill=th.INK_SOFT,
                             font=th.hand(12), anchor="e")
        # doubled baseline, the ledger rule
        self.create_line(x0, y1, x1, y1, fill=self._color, width=2)
        self.create_line(x0, y1 + 2, x1, y1 + 2, fill=th.RULE_DK, width=1)

        label_every = max(1, int(math.ceil(n / 12.0)))
        for i, v in enumerate(self._values):
            missing = bool(self._missing[i]) if self._missing else False
            color = th.RULE if missing else (
                self._colors[i] if self._colors else self._color)
            cx = x0 + (i + 0.5) * slot
            if missing or not v or v <= 0:
                if missing:
                    self.create_oval(cx - 1, y1 - 3, cx + 1, y1 - 1,
                                     fill=th.RULE, outline="")
                else:
                    # a logged zero day: small open ring, deliberate
                    self.create_oval(cx - 3, y1 - 7, cx + 3, y1 - 1,
                                     outline=color, width=1)
            else:
                top_y = y_of(v)
                tilt = rng.uniform(-2.5, 2.5)
                for dx, wd in ((-1.6, 1), (0, 2), (1.6, 1)):
                    self.create_line(cx + dx, y1, cx + dx + tilt, top_y,
                                     fill=color, width=wd)
                # sketch-ring cap: jittered octagon, never a perfect circle
                r = 4
                pts = []
                for k in range(8):
                    ang = math.pi / 4 * k + rng.uniform(-0.15, 0.15)
                    rr = r + rng.uniform(-1.0, 1.0)
                    pts.extend([cx + tilt + rr * math.cos(ang),
                                top_y - 6 + rr * math.sin(ang)])
                self.create_polygon(pts, outline=color, fill="", width=2)
            if self._labels and i % label_every == 0:
                self.create_text(cx, y1 + 12, text=self._labels[i],
                                 fill=th.INK_SOFT, font=th.hand(11),
                                 anchor="n", justify="center")


class WeekdayChart(Chart):
    """Average meals per weekday, Monday through Sunday."""

    NAMES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

    def __init__(self, master, height=150, **kw):
        super().__init__(master, height=height, **kw)
        self._values = []
        self._counts = []

    def set_data(self, values, counts=None):
        self._values = list(values)
        self._counts = list(counts) if counts else None
        self.redraw()

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        if not self._values:
            self._empty()
            return
        pad = (34, 12, 12, 30)
        L = layout_bars(self._values, w, h, pad)
        self._frame(L["ticks"])
        x0, y0, x1, y1 = L["plot"]
        colors = [self._color_default(i) for i in range(len(self._values))]
        for i, (bx0, by0, bx1, by1, v) in enumerate(L["bars"]):
            self.create_rectangle(bx0, by0, bx1, by1, fill=colors[i])
            self.create_rectangle(bx0, by0, bx1, by0 + 2, fill=th.TEXT)
            self.create_text((bx0 + bx1) / 2, by0 - 8, text=_fmt(v),
                             fill=th.TEXT_DIM, font=th.mono(8))
            self.create_text((bx0 + bx1) / 2, y1 + 8, text=self.NAMES[i],
                             fill=th.TEXT_MUTE, font=th.mono(8), anchor="n")
            if self._counts and self._counts[i]:
                self.create_text((bx0 + bx1) / 2, y1 + 19,
                                 text=f"n={self._counts[i]}", fill=th.BORDER_HI,
                                 font=th.mono(7), anchor="n")

    @staticmethod
    def _color_default(i):
        return th.TEXT


class StepChart(Chart):
    """Cumulative total over the selected range, drawn as a staircase."""

    def __init__(self, master, height=150, color=th.TEXT, **kw):
        super().__init__(master, height=height, **kw)
        self._color = color
        self._values = []
        self._labels = []

    def set_data(self, values, labels=None):
        self._values = list(values)
        self._labels = list(labels) if labels else []
        self.redraw()

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        if not self._values:
            self._empty()
            return
        L = layout_step(self._values, w, h, self._pad)
        self._frame(L["ticks"])
        pts = L["points"]
        x0, y0, x1, y1 = L["plot"]
        poly = [pts[0][0], y1]
        for px, py in pts:
            poly.extend([px, py])
        poly.extend([pts[-1][0], y1])
        flat = self._shade()
        if flat:
            self.create_polygon(poly, fill=flat, outline="")
        for i in range(1, len(pts)):
            ax, ay = pts[i - 1]
            bx, by = pts[i]
            self.create_line(ax, ay, bx, ay, fill=self._color, width=2)
            if by != ay:
                self.create_line(bx, ay, bx, by, fill=self._color, width=2)
        px, py = pts[-1]
        self.create_rectangle(px - 2, py - 2, px + 3, py + 3, fill=th.TEXT)
        self.create_text(px, py - 12, text=_fmt(self._values[-1]),
                         fill=th.TEXT, font=th.mono(9), anchor="e")
        if self._labels:
            step = max(1, int(len(self._labels) / 12.0))
            for i in range(0, len(self._labels), step):
                gx, _ = pts[i]
                self.create_text(gx, y1 + 9, text=self._labels[i],
                                 fill=th.TEXT_MUTE, font=th.mono(8))

    def _shade(self):
        """A dark tint of the line colour for the area fill."""
        base = self._color.lstrip("#")
        r, g, b = (int(base[i:i + 2], 16) for i in (0, 2, 4))
        mix = lambda c: int(c * 0.28)
        return "#%02x%02x%02x" % (mix(r), mix(g), mix(b))