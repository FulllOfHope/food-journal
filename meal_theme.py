"""Mess Ledger theme: a paper journal with photographic mastheads.

Warm paper with grain and dot-grid ruling, a stitched spine, Playfair
entry mastheads set directly over your artwork (washed warm with a baked
scrim for legibility), Caveat margin notes, rubber-stamp states and a
a ruled miss allowance. Put photos in art/ (today.jpg, log.jpg,
insights.jpg, or a single bg.jpg) — without them the banners fall back
to plain paper and ink.

Domain rules and storage live in meal_common; this file is presentation.
"""
import hashlib
import math
import os
import random
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import ttk

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageTk
    _PIL = True
except Exception:
    _PIL = False

ART_DIR = Path(__file__).resolve().parent / "art"


def art(*names):
    """First existing artwork file, or None (paper fallback)."""
    for name in names:
        p = ART_DIR / name
        if p.is_file():
            return str(p)
    return None

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
HONEY     = "#d9a441"   # part-days: some meals taken, not all
BARK_DK   = "#6b4a2f"   # trunk
FRUIT     = "#c96a24"   # ripe tangerine
FRUIT_DK  = "#96501c"
FRUIT_HI  = "#f2c078"
LEAF_FILL = "#5a7a2a"
LEAF_DK   = "#42591d"
PETAL     = "#fbf7ec"   # the cream used inside stamps and petals
SKY       = "#c3dcee"
SKY_DK    = "#8ab4d2"
SPARK     = "#d9a441"
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
GREEN_DK  = STAMP       # one accent only: kept marks are ink, misses are red
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

    def __init__(self, master, grain_tile=132, grid=24, photo=None,
                 wash=0.14, **kw):
        super().__init__(master, bg=PAPER, highlightthickness=0, bd=0,
                         **kw)
        self._rng = random.Random(11)
        self._grain_img = None
        self._tile = grain_tile
        self._grid = grid
        self._photo = photo
        self._wash = wash
        self._wash_img = None
        self._wash_key = None
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
        if self._photo and _PIL:
            key = (self._photo, w, h)
            if key != self._wash_key:
                try:
                    self._wash_img = wash_cover(self._photo, w, h, 0.5,
                                                self._wash)
                    self._wash_key = key
                except Exception:
                    self._wash_img = None
                    self._wash_key = None
            if self._wash_img is not None:
                self.create_image(0, 0, image=self._wash_img, anchor="nw",
                                  tags="paper")
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


# ------------------------------------------------------- photo art
PAPER_RGB = (244, 241, 234)


_CACHE_DIR = Path.home() / ".cache" / "mess-ledger" / "art"
_ART_VERSION = 9  # bump whenever the art pipeline changes


def _cache_path(key):
    digest = hashlib.sha1(repr(key).encode()).hexdigest()
    return _CACHE_DIR / (digest + ".png")


def cached_image(key, builder):
    """Processed art, memoized on disk: repeat loads cost a PNG decode,
    so banners appear instead of grinding through PIL each time."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        hit = _cache_path(key)
        if hit.is_file():
            img = Image.open(hit)
            img.load()
            return img
    except Exception:
        pass
    img = builder()
    try:
        img.save(_cache_path(key))
    except Exception:
        pass
    return img


def _file_stamp(path):
    try:
        st = os.stat(path)
        return (st.st_mtime, st.st_size)
    except Exception:
        return (0, 0)


def cover_fit(img, w, h, anchor=0.5):
    """Scale img to cover (w, h), cropping with vertical anchor 0..1."""
    sw, sh = img.size
    scale = max(w / max(1, sw), h / max(1, sh))
    img = img.resize((max(1, int(sw * scale)), max(1, int(sh * scale))),
                     Image.LANCZOS)
    sw, sh = img.size
    x = max(0, (sw - w) // 2)
    y = max(0, int((sh - h) * min(1.0, max(0.0, anchor))))
    return img.crop((x, y, x + w, y + h))


def deckle(img, top=6, bottom=8, seed=7):
    """Tear the top and bottom edges so a band reads as a pasted strip.

    Three slow waves at coprime periods give an organic wobble. The
    earlier version added a per-column hash for fibre texture, but on a
    band this short it read as static, not paper, so the randomness is
    gone and the tear is carried by shape alone."""
    w, h = img.size
    out = img.convert("RGBA")
    alpha = Image.new("L", (w, h), 255)
    px = alpha.load()
    k = seed * 0.9

    def wave(x, n):
        return (math.sin(x / 61.0 + n + k) * 2.6
                + math.sin(x / 27.0 + n * 1.7 + k) * 1.5
                + math.sin(x / 13.0 + n * 2.3 + k) * 0.7)

    for x in range(w):
        t = top + wave(x, 0.0)
        b = h - bottom - wave(x, 2.4)
        for y in range(0, max(0, min(h, int(t)))):
            px[x, y] = 0
        for y in range(max(0, min(h, int(b))), h):
            px[x, y] = 0
    out.putalpha(alpha)
    return out


def band_fit(img, w, h, anchor=0.45, tear=True):
    """Fill a wide, short band with one photo, cropped rather than
    squashed, so the artwork keeps its proportions edge to edge.

    Left soft on purpose. An unsharp pass was tried here to give the
    resize some bite, and on this artwork it cut the foliage out into
    hard shapes and fought the painted surface. A warm, calm band is
    the point, so it is not sharpened."""
    band = cover_fit(img, w, h, anchor)
    return deckle(band) if tear else band


def feather_edges(img, top=30, bottom=56):
    """Melt the banner's edges into the paper instead of ending in hard
    photographic lines."""
    w, h = img.size
    mask = Image.new("L", (1, h), 255)
    mp = mask.load()
    for y in range(h):
        if y < top:
            mp[0, y] = int(255 * y / max(1, top))
        elif y >= h - bottom:
            mp[0, y] = int(255 * (h - 1 - y) / max(1, bottom - 1))
    img = img.convert("RGBA")
    img.putalpha(mask.resize((w, h)))
    return img


def procedural_banner(w, h, seed=7):
    """Warm abstract wash when a slot has no photo: marigold and olive
    drifts on cream, so the page is designed even bare."""
    import random as _random
    rng = _random.Random(seed)
    img = Image.new("RGB", (w, h), PAPER_RGB)
    from PIL import ImageDraw as _D
    layer = Image.new("RGB", (w, h), PAPER_RGB)
    dd = _D.Draw(layer)
    tones = [(217, 164, 65), (138, 154, 74), (179, 64, 46), (201, 173, 124)]
    for _ in range(7):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        rx, ry = rng.uniform(w * 0.08, w * 0.30), rng.uniform(h * 0.2, h * 0.9)
        dd.ellipse((cx - rx, cy - ry, cx + rx, cy + ry),
                   fill=tones[_ % len(tones)])
    layer = layer.filter(ImageFilter.GaussianBlur(max(8, w // 28)))
    return Image.blend(img, layer, 0.55)


def wash_cover(path, w, h, anchor, strength):
    """Your photo melted into the paper at low strength for backgrounds."""
    def build():
        img = Image.open(path).convert("RGB")
        img = cover_fit(img, w, h, anchor)
        img = img.filter(ImageFilter.GaussianBlur(1.2))
        return Image.blend(Image.new("RGB", img.size, PAPER_RGB), img,
                           strength)
    key = (_ART_VERSION, "wash", path, _file_stamp(path), w, h,
           round(anchor, 3), strength)
    return ImageTk.PhotoImage(cached_image(key, build))


class PhotoBanner(tk.Canvas):
    """Full-bleed photographic masthead in original colour, melted into
    the paper at the edges. Headings live on paper beneath it, so type
    is always ink on paper and the photo is never muted for legibility.
    Without art (or PIL) the band is plain paper."""

    def __init__(self, master, height=168, photo=None, anchor=0.0,
                 bg=PAPER, seed=7, photos=None, **kw):
        super().__init__(master, height=height, bg=bg, highlightthickness=0,
                         bd=0, **kw)
        pool = list(photos) if photos else ([photo] if photo else [])
        self._photo = pool[0] if pool else None
        self._anchor = anchor
        self._seed = seed
        self._img = None
        self._key = None
        self._job = None
        self._stamp_text = ""
        self.bind("<Configure>", self._on_resize)

    def set_stamp(self, text):
        """Rubber-stamp a date into the corner of the band."""
        text = text or ""
        if text == self._stamp_text:
            return
        self._stamp_text = text
        self._draw_stamp()

    def _draw_stamp(self):
        self.delete("stamp")
        if not self._stamp_text or self._img is None:
            return
        w, h = self.winfo_width(), self.winfo_height()
        if w < 200 or h < 40:
            return
        cx, cy = w - 96, h - 44
        self.create_rectangle(cx - 70, cy - 17, cx + 70, cy + 17,
                              outline=STAMP, width=2, tags="stamp")
        self.create_text(cx, cy, text=self._stamp_text, fill=STAMP, angle=-7,
                         font=mono(12), tags="stamp")

    def _on_resize(self, _e=None):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        self._job = self.after(250, self.redraw)

    def redraw(self):
        self._job = None
        self.delete("all")
        try:
            w, h = self.winfo_width(), self.winfo_height()
        except Exception:
            return
        if w < 60 or h < 30:
            return
        photo = self._photo and _PIL
        if photo:
            key = (_ART_VERSION, "band", self._photo,
                   _file_stamp(self._photo), w, h,
                   round(self._anchor, 3))
            if key != self._key:
                try:
                    def build(w=w, h=h):
                        img = Image.open(self._photo).convert("RGB")
                        return band_fit(img, w, h, self._anchor)
                    self._img = ImageTk.PhotoImage(cached_image(key, build))
                    self._key = key
                except Exception:
                    self._img = None
                    self._key = None
        elif _PIL:
            key = (_ART_VERSION, "procedural", w, h, self._seed)
            if key != self._key:
                try:
                    def build(w=w, h=h):
                        return feather_edges(procedural_banner(w, h,
                                                               self._seed))
                    self._img = ImageTk.PhotoImage(cached_image(key, build))
                    self._key = key
                except Exception:
                    self._img = None
                    self._key = None
        if self._img is not None:
            self.create_image(0, 0, image=self._img, anchor="nw")
            self._draw_stamp()

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


# ------------------------------------------------------- doodle stamp
def tally(canvas, x, y, value, h=15, gap=5, colour=INK_SOFT, slant=6,
          max_groups=9):
    """Pen tally marks: four uprights and a diagonal for each five.

    Returns the x just past the last stroke, so callers can lay marks out
    in a row the way they would rule them on paper."""
    done = 0
    x0 = x
    while value >= 5 and done < max_groups:
        for i in range(4):
            canvas.create_line(x0 + i * gap, y - h, x0 + i * gap, y,
                               fill=colour, width=1.8, capstyle="round")
        canvas.create_line(x0 - slant * 0.6, y + 1, x0 + 3 * gap + slant * 0.6,
                           y - h - 1, fill=colour, width=1.8,
                           capstyle="round")
        x0 += 4 * gap + slant + gap
        value -= 5
        done += 1
    for i in range(int(value)):
        canvas.create_line(x0 + i * gap, y - h, x0 + i * gap, y,
                           fill=colour, width=1.8, capstyle="round")
        x0 += gap
    return x0


class PenTally(tk.Canvas):
    """A row of hand-ruled tally marks, like counting on a page."""

    def __init__(self, master, height=22, bg=PAPER, colour=INK_SOFT, **kw):
        super().__init__(master, height=height, bg=bg, highlightthickness=0,
                         bd=0, **kw)
        self._colour = colour
        self._value = 0
        self._over = False
        self.bind("<Configure>", lambda e: self.redraw())

    def set_value(self, value, over=False):
        self._value = max(0, int(round(value)))
        self._over = over
        self.redraw()

    def redraw(self):
        self.delete("all")
        if self._value <= 0:
            return
        y = self.winfo_height() - 6
        end = tally(self, 1, y, self._value, h=min(14, y - 3),
                    colour=RED if self._over else self._colour)
        if self._over:
            self.create_text(end + 6, y - 7, text="over", anchor="w",
                             fill=RED, font=mono(9))


class MealBreakdown(tk.Canvas):
    """Which meals actually get skipped, ruled the way you would on paper:
    a row of ticked boxes, one per day the meal was offered.

    Saturday dinner is worth nothing, so it is reported as closed rather
    than dragging the count down with a fake miss."""

    ROW_H = 40

    def __init__(self, master, bg=PAPER, height=None, **kw):
        super().__init__(master, height=height or self.ROW_H * 3 + 6, bg=bg,
                         highlightthickness=0, bd=0, **kw)
        self._stats = {}
        self.bind("<Configure>", lambda e: self.redraw())

    def set_stats(self, stats, days):
        self._stats = stats or {}
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = max(1, self.winfo_width())
        if w < 120 or not self._stats:
            return
        labels = {"breakfast": "BREAKFAST", "lunch": "LUNCH",
                  "dinner": "DINNER"}
        box, step = 13, 16
        for i, meal in enumerate(("breakfast", "lunch", "dinner")):
            d = self._stats.get(meal, {})
            y = i * self.ROW_H
            offered = d.get("offered", 0)
            skipped = d.get("skipped", 0)
            self.create_text(0, y + 7, text=labels[meal], anchor="w",
                             fill=INK, font=mono(10))
            if offered <= 0:
                self.create_text(w, y + 7, text="closed on Saturdays",
                                 anchor="e", fill=PENCIL_LT, font=mono(9))
                continue
            kept = offered - skipped
            x0 = 92
            # one ruled box per day offered: ticked when it was eaten
            for k in range(offered):
                bx = x0 + k * step
                if bx + box > w - 118:
                    break
                self.create_rectangle(bx, y, bx + box, y + box,
                                      outline=RULE_DK, width=1)
                if k < kept:
                    self.create_line(bx + 3, y + box / 2, bx + box / 2,
                                     y + box - 3, fill=INK, width=1.8,
                                     capstyle="round")
                    self.create_line(bx + box / 2, y + box - 3,
                                     bx + box - 3, y + 3, fill=INK,
                                     width=1.8, capstyle="round")
                else:
                    self.create_line(bx + 3, y + 3, bx + box - 3, y + box - 3,
                                     fill=RED, width=1.6)
                    self.create_line(bx + box - 3, y + 3, bx + 3, y + box - 3,
                                     fill=RED, width=1.6)
            note = f"{skipped} missed of {offered}" if skipped else \
                   f"all {offered} kept"
            self.create_text(w, y + 7, text=note, anchor="e",
                             fill=RED if skipped else PENCIL,
                             font=mono(9))


class MonthGrid(tk.Canvas):
    """A calendar month shaded by how many meals were eaten each day.

    Click a cell to jump straight to editing that day."""

    HEAD_H = 26
    CELL_W = 0

    def __init__(self, master, bg=PAPER, on_pick=None, **kw):
        super().__init__(master, height=340, bg=bg, highlightthickness=0,
                         bd=0, **kw)
        self._cells = []
        self._marks = {}
        self._today = None
        self._on_pick = on_pick
        self.bind("<Configure>", lambda e: self.redraw())

    def set_month(self, months, today=None, ticks=None):
        """`months` is [(date, eaten, expected), ...] for one month.

        `ticks` is [(date, {meal: eaten_or_closed}), ...] so each cell can
        show its three marks instead of a filled bar."""
        self._cells = list(months)
        self._marks = {d: m for d, m in (ticks or [])}
        self._today = today
        self.redraw()

    def _pick(self, i):
        if self._on_pick and 0 <= i < len(self._cells):
            self._on_pick(self._cells[i][0])

    def redraw(self):
        self.delete("all")
        w = max(1, self.winfo_width())
        if w < 120 or not self._cells:
            return
        names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        cw = w / 7.0
        for c, n in enumerate(names):
            self.create_text(cw * c + cw / 2, self.HEAD_H / 2, text=n,
                             fill=PENCIL, font=mono(9))
        self.create_line(0, self.HEAD_H, w, self.HEAD_H, fill=RULE, width=1)

        rows = {}
        for i, (d, eaten, expected) in enumerate(self._cells):
            rows.setdefault(d.weekday(), []).append(i)
        body_top = self.HEAD_H + 6
        avail_h = max(60, self.winfo_height() - body_top - 4)
        weeks = max(1, -(-len(self._cells) // 7))
        ch = min(64.0, avail_h / weeks)
        for i, (d, eaten, expected) in enumerate(self._cells):
            r, c = divmod(i, 7)
            x = cw * c
            y = body_top + r * ch
            today = (d == self._today)
            self.create_rectangle(x + 3, y + 2, x + cw - 3, y + ch - 4,
                                  outline=STAMP if today else RULE,
                                  width=1.4 if today else 1)
            self.create_text(x + 9, y + 13, text=d.strftime("%d"),
                             anchor="w",
                             fill=INK if today else INK_SOFT,
                             font=mono(10))
            marks = self._marks.get(d)
            if marks:
                bx, bs = x + 9, 11
                for j, meal in enumerate(("breakfast", "lunch", "dinner")):
                    got = marks.get(meal)
                    if got is None:
                        continue
                    mx = bx + j * bs
                    my = y + ch - 18
                    if got == "closed":
                        self.create_line(mx, my + 4, mx + 6, my + 4,
                                         fill=RULE_DK, width=1.6)
                        continue
                    self.create_rectangle(mx, my, mx + 6, my + 6,
                                          outline=RULE_DK, width=1)
                    if got:
                        self.create_line(mx + 1, my + 3, mx + 3, my + 5,
                                         fill=INK, width=1.4,
                                         capstyle="round")
                        self.create_line(mx + 3, my + 5, mx + 5, my + 1,
                                         fill=INK, width=1.4,
                                         capstyle="round")
            self.create_rectangle(x, y, x + cw, y + ch, fill="",
                                  outline="", tags=f"m{i}")
            self.tag_bind(f"m{i}", "<Button-1>", lambda e, k=i: self._pick(k))
            self.tag_bind(f"m{i}", "<Enter>",
                          lambda e: self.configure(cursor="hand2"))
            self.tag_bind(f"m{i}", "<Leave>",
                          lambda e: self.configure(cursor=""))


class TangerineTree(tk.Canvas):
    """A tangerine tree that fruits as the cycle fills up.

    Drawn from `progress`, the share of this cycle's meals actually
    eaten, so it is a record rather than ornament: a bare seed on day
    one, blossom by the middle, laden by the end. Deterministic, so the
    same day always grows the same tree."""

    def __init__(self, master, width=150, height=250, bg=PAPER, **kw):
        super().__init__(master, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, **kw)
        self._p = 0.0
        self.bind("<Configure>", lambda e: self.redraw())

    def set_progress(self, progress):
        self._p = max(0.0, min(1.0, float(progress)))
        self.redraw()

    # a fixed scatter of leaf and fruit anchors, so the canopy fills in
    # from the trunk outwards instead of scrambling as it grows
    LEAVES = ((-30, -128), (-6, -150), (22, -132), (-40, -104), (40, -108),
              (-16, -112), (10, -118), (-48, -78), (46, -82), (-24, -86),
              (8, -92), (34, -64), (-38, -52), (40, -54), (-8, -58),
              (14, -40), (-26, -26), (24, -28))
    FRUIT = ((-34, -118), (26, -120), (-44, -90), (42, -94), (-2, -96),
             (36, -66), (-40, -60), (4, -44), (-20, -34), (22, -50),
             (-10, -70), (14, -84))

    def redraw(self):
        self.delete("all")
        p = self._p
        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())
        cx = w / 2.0
        base = h - 30          # leave a line for the caption underneath

        # soil: a ruled line of earth with a few pressed specks
        self.create_line(cx - 34, base, cx + 34, base, fill=BARK_DK, width=2)
        for dx in (-24, -8, 10, 26):
            self.create_oval(cx + dx - 2, base - 2, cx + dx + 2, base + 2,
                             fill="#8a6a4a", outline="")

        if p <= 0.001:
            # day one: a seed, and the promise of the thing
            self.create_oval(cx - 4, base - 7, cx + 4, base - 1,
                             fill="#6b4a2f", outline="")
            self.create_text(cx, base + 16, text="a seed", anchor="center",
                             fill=PENCIL, font=mono(9))
            return
            return

        # trunk: short and thick at first, tall and tapered later
        top = base - (34 + 96 * p)
        lean = -6 + 14 * p
        self.create_line(cx, base, cx + lean, top, fill=BARK_DK,
                         width=7 if p < 0.5 else 5, capstyle="round")
        # one limb for each step of growth
        for i in range(1, 4):
            if p < i / 3.4:
                break
            f = i / 3.0
            by = top + (base - top) * (1 - f) * 0.7
            for side in (-1, 1):
                self.create_line(cx + lean * (1 - (1 - f) * 0.7), by,
                                 cx + lean + side * (10 + 12 * f), by - 9 * f,
                                 fill="#6b4a2f", width=3 - f, capstyle="round")

        # leaves fill the canopy outward, largest first
        n_leaf = max(1, int(round(len(self.LEAVES) * min(1.0, p * 1.12))))
        for i, (dx, dy) in enumerate(self.LEAVES[:n_leaf]):
            lx, ly = cx + dx, top + (dy + 150) * (0.55 + 0.45 * p)
            r = 7 + 3 * p
            self.create_oval(lx - r, ly - r * 0.7, lx + r, ly + r * 0.7,
                             fill=LEAF_FILL, outline=LEAF_DK, width=1.2)

        # fruit only once there is a canopy able to carry it
        n_fruit = int(round(len(self.FRUIT) * max(0.0, (p - 0.2) / 0.8)))
        for dx, dy in self.FRUIT[:n_fruit]:
            fx, fy = cx + dx, top + (dy + 150) * (0.55 + 0.45 * p)
            self.create_oval(fx - 6, fy - 6, fx + 6, fy + 6,
                             fill=FRUIT, outline=FRUIT_DK, width=1.4)
            self.create_oval(fx - 3, fy - 4, fx - 1, fy - 2, fill=FRUIT_HI,
                             outline="")
        if n_fruit:
            self.create_text(cx, base + 16,
                             text=f"{n_fruit} of {len(self.FRUIT)} ripe",
                             anchor="center", fill=PENCIL, font=mono(9))
        else:
            self.create_text(cx, base + 16, text="growing", anchor="center",
                             fill=PENCIL, font=mono(9))

        # a blossom appears once, mid-cycle, and is the reward for the
        # habit rather than for the number
        if 0.35 <= p < 0.75:
            bx, by = cx + 30, top + 6
            for a in range(0, 360, 72):
                import math as _m
                r = _m.radians(a)
                self.create_oval(bx + 4 * _m.cos(r) - 3,
                                 by + 4 * _m.sin(r) - 3,
                                 bx + 4 * _m.cos(r) + 3,
                                 by + 4 * _m.sin(r) + 3,
                                 fill="#fbf7ec", outline=HONEY, width=1)


class Doodle(tk.Canvas):
    """A bare hand-drawn veg doodle for the empty stretches: flat
    storybook fills with depth, no box, no words. Static art."""

    FRUIT = "#c96a24"
    FRUIT_DK = "#96501c"
    FRUIT_HI = "#f2c078"
    LEAF = "#5a7a2a"
    LEAF_DK = "#42591d"
    BARK = "#6b4a2f"
    GRAIN = "#d9a441"
    GRAIN_DK = "#8a6a25"
    LEMON = "#e6c33c"
    LEMON_DK = "#ab8a1c"
    SKY = "#c3dcee"
    SKY_DK = "#8ab4d2"
    PETAL = "#fbf7ec"
    POLLEN = "#dfae3a"
    BERRY = "#c0453a"
    TAPE_A = "#d6e6c6"
    TAPE_B = "#e9d3c2"

    def __init__(self, master, doodle="tangerine", size=110, bg=PAPER,
                 **kw):
        super().__init__(master, width=size, height=size, bg=bg,
                         highlightthickness=0, bd=0, **kw)
        self._kind = doodle
        cx, cy = size / 2, size / 2 + 2
        {"tangerine": self._tangerine,
         "sprig": self._sprig,
         "wheat": self._wheat,
         "star": self._star,
         "leaf": self._leaf,
         "chili": self._chili,
         "lemon": self._lemon,
         "slice": self._slice,
         "daisy": self._daisy,
         "butterfly": self._butterfly,
         "bee": self._bee,
         "cloud": self._cloud,
         "sun": self._sun,
         "bird": self._bird,
         "heart": self._heart,
         "bow": self._bow,
         "tape": self._tape,
         "stamp": self._stamp,
         "postmark": self._postmark,
         "airmail": self._airmail,
         "passport": self._passport,
         "compass": self._compass}.get(doodle, self._tangerine)(cx, cy)

    def _tangerine(self, x, y):
        self.create_oval(x - 16, y - 15, x + 16, y + 15, fill=self.FRUIT,
                         outline=self.FRUIT_DK, width=2.5)
        self.create_oval(x - 9, y - 11, x - 2, y - 4, fill=self.FRUIT_HI,
                         outline="")
        for dx, dy in ((-11, -13), (-4, -18), (4, -18), (11, -13)):
            self.create_line(x, y - 14, x + dx, y + dy, fill=self.LEAF,
                             width=2.5)
        self.create_line(x + 1, y - 18, x + 1, y - 25, fill=self.LEAF,
                         width=2.5)

    def _sprig(self, x, y):
        self.create_line(x, y + 24, x, y - 24, fill=self.BARK, width=2.5)
        for i, dy in enumerate((-14, -2, 10)):
            side = 1 if i % 2 == 0 else -1
            for sgn in (side, -side):
                lx, ly = x + sgn * 14, y + dy - 8
                self.create_oval(min(x, lx) - 1, min(y + dy, ly) - 4,
                                 max(x, lx) + 1, max(y + dy, ly) + 4,
                                 fill=self.LEAF, outline=self.LEAF_DK,
                                 width=1.5)

    def _wheat(self, x, y):
        self.create_line(x, y + 24, x, y - 24, fill=self.BARK, width=2.5)
        for dy in (-16, -7, 2, 11):
            for sgn in (1, -1):
                gx, gy = x + sgn * 11, y + dy - 7
                self.create_oval(min(x, gx) - 1, min(y + dy, gy) - 4,
                                 max(x, gx) + 1, max(y + dy, gy) + 4,
                                 fill=self.GRAIN, outline=self.GRAIN_DK,
                                 width=1.5)

    def _star(self, x, y):
        r = 15
        self.create_line(x - r, y, x + r, y, fill=SPARK, width=2.5)
        self.create_line(x, y - r, x, y + r, fill=SPARK, width=2.5)
        self.create_polygon([(x, y - r * 0.55), (x + r * 0.2, y),
                             (x, y + r * 0.55), (x - r * 0.2, y)],
                            fill=SPARK, outline="")

    def _leaf(self, x, y):
        self.create_polygon([(x, y - 20), (x + 13, y - 2), (x + 4, y + 18),
                             (x - 4, y + 18), (x - 13, y - 2)],
                            fill=self.LEAF, outline=self.LEAF_DK, width=2)
        self.create_line(x, y - 20, x, y + 18, fill=self.LEAF_DK, width=1.5)

    def _chili(self, x, y):
        self.create_line(x - 15, y - 6, x - 2, y + 6, x + 13, y - 4,
                         fill=STAMP, width=7, capstyle="round", smooth=True)
        self.create_line(x + 13, y - 4, x + 19, y - 14, fill=self.LEAF,
                         width=2.5)
        self.create_line(x + 19, y - 14, x + 13, y - 16, fill=self.LEAF,
                         width=2)
        self.create_line(x + 19, y - 14, x + 23, y - 18, fill=self.LEAF,
                         width=2)


    def _lemon(self, x, y):
        self.create_oval(x - 17, y - 13, x + 15, y + 13, fill=self.LEMON,
                         outline=self.LEMON_DK, width=2.5)
        self.create_polygon([(x - 17, y - 4), (x - 25, y - 9),
                             (x - 25, y + 1)], fill=self.LEMON,
                            outline=self.LEMON_DK, width=2)
        self.create_line(x + 2, y - 13, x + 8, y - 22, fill=self.LEAF,
                         width=2.5)

    def _slice(self, x, y):
        self.create_oval(x - 17, y - 17, x + 17, y + 17, fill=self.FRUIT,
                         outline=self.FRUIT_DK, width=2.5)
        self.create_oval(x - 12, y - 12, x + 12, y + 12, fill=self.FRUIT_HI,
                         outline="")
        for a in range(0, 360, 45):
            import math as _m
            r = _m.radians(a)
            self.create_line(x, y, x + 11 * _m.cos(r), y + 11 * _m.sin(r),
                             fill=self.FRUIT_DK, width=1.6)

    def _daisy(self, x, y):
        for dx, dy in ((0, -13), (11, -4), (7, 10), (-7, 10), (-11, -4)):
            self.create_oval(x + dx - 7, y + dy - 7, x + dx + 7, y + dy + 7,
                             fill=PETAL, outline=SKY_DK,
                             width=1.6)
        self.create_oval(x - 7, y - 7, x + 7, y + 7, fill=self.POLLEN,
                         outline="")

    def _butterfly(self, x, y):
        for sgn in (1, -1):
            self.create_oval(x + sgn * 5 - 10, y - 15, x + sgn * 5 + 10,
                             y - 1, fill=SPARK, outline=self.FRUIT_DK,
                             width=1.8)
            self.create_oval(x + sgn * 5 - 8, y - 1, x + sgn * 5 + 8, y + 14,
                             fill=self.FRUIT_HI, outline=self.FRUIT_DK,
                             width=1.8)
        self.create_line(x, y - 12, x, y + 12, fill=self.BARK, width=2.5)
        self.create_line(x, y - 12, x - 6, y - 21, fill=self.BARK, width=1.6)
        self.create_line(x, y - 12, x + 6, y - 21, fill=self.BARK, width=1.6)

    def _bee(self, x, y):
        self.create_oval(x - 13, y - 12, x + 12, y + 12, fill=SPARK,
                         outline=self.FRUIT_DK, width=2)
        for dx in (-4, 4):
            self.create_line(x + dx - 3, y - 10, x + dx - 3, y + 10,
                             fill=self.BARK, width=2.5)
        self.create_oval(x + 12, y - 10, x + 24, y + 1, fill=SKY,
                         outline=SKY_DK, width=1.6)
        self.create_line(x - 13, y, x - 21, y - 5, fill=self.BARK, width=2)

    def _cloud(self, x, y):
        self.create_oval(x - 24, y - 4, x - 4, y + 12, fill=PETAL,
                         outline=SKY_DK, width=2)
        self.create_oval(x - 10, y - 13, x + 12, y + 10, fill=PETAL,
                         outline=SKY_DK, width=2)
        self.create_oval(x + 4, y - 2, x + 24, y + 12, fill=PETAL,
                         outline=SKY_DK, width=2)
        self.create_line(x - 20, y + 11, x + 20, y + 11, fill=SKY_DK,
                         width=2)

    def _sun(self, x, y):
        import math as _m
        for a in range(0, 360, 45):
            r = _m.radians(a)
            self.create_line(x + 15 * _m.cos(r), y + 15 * _m.sin(r),
                             x + 23 * _m.cos(r), y + 23 * _m.sin(r),
                             fill=SPARK, width=2.5)
        self.create_oval(x - 13, y - 13, x + 13, y + 13, fill=SPARK,
                         outline=self.GRAIN_DK, width=2)

    def _bird(self, x, y):
        for sgn in (1, -1):
            self.create_arc(x + sgn * 2 - 11, y - 10, x + sgn * 2 + 11,
                            y + 8, start=200 if sgn > 0 else 320,
                            extent=140, style="arc", outline=INK_SOFT,
                            width=2.5)

    def _heart(self, x, y):
        self.create_polygon([(x, y + 15), (x - 17, y - 2), (x - 13, y - 11),
                             (x - 5, y - 12), (x, y - 6), (x + 5, y - 12),
                             (x + 13, y - 11), (x + 17, y - 2)],
                            fill=self.BERRY, outline="")

    def _bow(self, x, y):
        for sgn in (1, -1):
            self.create_oval(x + sgn * 4 - 13, y - 10, x + sgn * 4 + 13,
                             y + 8, fill=STAMP, outline="")
            self.create_polygon([(x + sgn * 3, y + 4), (x + sgn * 12, y + 20),
                                 (x + sgn * 5, y + 17), (x, y + 5)],
                                fill=STAMP, outline="")
        self.create_oval(x - 5, y - 6, x + 5, y + 5, fill=self.BERRY,
                         outline="")

    def _tape(self, x, y):
        self.create_rectangle(x - 34, y - 9, x + 34, y + 9,
                              fill=self.TAPE_A, outline="")
        for dx in (-26, -8, 10, 28):
            self.create_line(x + dx, y - 9, x + dx + 9, y + 9,
                             fill=self.TAPE_B, width=5)

    def _stamp(self, x, y):
        self.create_rectangle(x - 17, y - 17, x + 17, y + 17,
                              fill=PETAL, outline=RULE_DK,
                              width=2, dash=(3, 3))
        self.create_oval(x - 9, y - 6, x + 9, y + 11, fill=self.FRUIT,
                         outline=self.FRUIT_DK, width=1.8)
        self.create_line(x, y - 6, x + 3, y - 13, fill=self.LEAF, width=1.8)


    def _postmark(self, x, y):
        """Postal cancellation: a ring of dashes with waves through it."""
        import math as _m
        for a in range(0, 360, 24):
            r0, r1 = _m.radians(a), _m.radians(a + 13)
            self.create_line(x + 20 * _m.cos(r0), y + 20 * _m.sin(r0),
                             x + 20 * _m.cos(r1), y + 20 * _m.sin(r1),
                             fill=self.FRUIT_DK, width=2)
        for dy in (-5, 0, 5):
            self.create_line(x - 26, y + dy, x + 26, y + dy,
                             fill=INK_SOFT, width=1.6)

    def _airmail(self, x, y):
        """The red-and-blue edged tag every parcel travels in."""
        self.create_rectangle(x - 26, y - 12, x + 26, y + 12,
                              fill=PETAL, outline=INK_SOFT,
                              width=1.4)
        self.create_rectangle(x - 26, y - 12, x - 19, y + 12,
                              fill=STAMP, outline="")
        self.create_rectangle(x + 19, y - 12, x + 26, y + 12,
                              fill="#3d5a80", outline="")
        self.create_line(x - 13, y - 5, x + 13, y + 5, fill=PENCIL,
                         width=1.4)
        self.create_line(x - 13, y + 5, x + 13, y - 5, fill=PENCIL,
                         width=1.4)

    def _passport(self, x, y):
        """A travel stamp: peak and sun inside a perforation."""
        self.create_rectangle(x - 17, y - 17, x + 17, y + 17,
                              fill=PETAL, outline=RULE_DK,
                              width=1.6, dash=(3, 3))
        self.create_polygon([(x - 12, y + 9), (x - 3, y - 7), (x + 5, y + 9)],
                            fill=SKY, outline=SKY_DK, width=1.2)
        self.create_oval(x + 6, y - 11, x + 13, y - 4, fill=SPARK,
                         outline="")

    def _compass(self, x, y):
        """A hand-drawn rose, the way a scrapbook marks a direction."""
        import math as _m
        self.create_oval(x - 18, y - 18, x + 18, y + 18,
                         outline=INK_SOFT, width=1.6)
        self.create_line(x, y - 13, x, y + 13, fill=INK_SOFT, width=1.4)
        self.create_line(x - 13, y, x + 13, y, fill=INK_SOFT, width=1.4)
        for a, col in ((45, self.FRUIT), (225, SKY_DK)):
            r = _m.radians(a)
            self.create_polygon([(x + 14 * _m.cos(r), y + 14 * _m.sin(r)),
                                 (x - 5 * _m.cos(r), y - 5 * _m.sin(r)),
                                 (x - 5 * _m.sin(r), y + 5 * _m.cos(r)),
                                 (x + 14 * _m.sin(r), y - 14 * _m.cos(r))],
                                fill=col, outline="")


# ------------------------------------------------------- pencil marks
class AllowanceBox(tk.Canvas):
    """Miss allowance ruled out in full: one cell per allowed miss, the
    used ones struck through by hand.

    The whole grid is always drawn. A compact one-row summary was tried
    and rejected - the cells are the point, and hiding them behind a
    hover made the gauge unreadable at rest."""

    def __init__(self, master, cell=15, gap=5, per_row=25, bg=PAPER, **kw):
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, **kw)
        self._cell, self._gap, self._row = cell, gap, per_row
        self._bg = bg
        self._used = 0.0
        self._allowed = 25
        self.bind("<Configure>", lambda e: self.redraw())

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
        w = max(1, self.winfo_width())
        # shrink the cells to fit the measure rather than clipping the
        # tail of the grid off the right edge
        per = max(1, min(self._row, int((w - 4) // step)))
        for i in range(cells):
            r, c = divmod(i, per)
            x0 = c * step + 2
            y0 = r * step + 2
            x1, y1 = x0 + self._cell, y0 + self._cell
            over = i >= self._allowed
            self.create_rectangle(x0, y0, x1, y1, outline=RULE_DK, width=1)
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


# ------------------------------------------------------- photo prints
class Medallion(tk.Label):
    """A round tangerine portrait for panel headers."""

    def __init__(self, master, photo, size=88, bg=PAPER, **kw):
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kw)
        self._img = None
        if photo and _PIL:
            try:
                img = Image.open(photo).convert("RGB")
                img = cover_fit(img, size, size, 0.4)
                mask = Image.new("L", (size, size), 0)
                d = ImageDraw.Draw(mask)
                d.ellipse((0, 0, size - 1, size - 1), fill=255)
                img = img.convert("RGBA")
                img.putalpha(mask)
                ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                rd = ImageDraw.Draw(ring)
                rd.ellipse((1, 1, size - 2, size - 2),
                           outline=(33, 33, 33, 255), width=2)
                self._img = ImageTk.PhotoImage(
                    Image.alpha_composite(img, ring))
                self.configure(image=self._img)
            except Exception:
                pass


# ------------------------------------------------------- scroll frame
_HOVER_CANVASES = []
_HOVER_BOUND = []


def _hover_scroll_target(widget):
    """Innermost registered scroll canvas under the pointer, if any."""
    try:
        w = widget.winfo_containing(widget.winfo_pointerx(),
                                    widget.winfo_pointery())
    except Exception:
        return None
    while w is not None:
        if w in _HOVER_CANVASES:
            return w
        w = getattr(w, "master", None)
    return None


def _hover_scroll(event):
    frame = _hover_scroll_target(event.widget)
    if frame is None:
        return None
    if getattr(event, "num", 0) == 4:
        steps = -1
    elif getattr(event, "num", 0) == 5:
        steps = 1
    else:
        delta = getattr(event, "delta", 0) or 0
        steps = -1 if delta > 0 else 1
    try:
        frame.smooth_scroll(steps)
    except Exception:
        return None
    return "break"


def register_hover_scroll(frame):
    """Route the wheel to this frame whenever the pointer is anywhere
    over it - no scrollbar grabbing, no clicking first."""
    _HOVER_CANVASES.append(frame)
    if not _HOVER_BOUND:
        _HOVER_BOUND.append(True)
        frame.canvas.bind_all("<Button-4>", _hover_scroll, add="+")
        frame.canvas.bind_all("<Button-5>", _hover_scroll, add="+")
        frame.canvas.bind_all("<MouseWheel>", _hover_scroll, add="+")


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
        self._anim = None
        self._target = 0.0
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.inner = self.inner
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        register_hover_scroll(self)

    def smooth_scroll(self, steps):
        """Glide toward the target instead of jumping: wheel notches
        accumulate into one eased motion."""
        try:
            total = self.inner.winfo_reqheight()
            h = self.canvas.winfo_height()
        except Exception:
            return
        if total <= h + 2:
            return
        if self._anim is None:
            try:
                self._target = self.canvas.yview()[0]
            except Exception:
                return
        self._target = min(1.0, max(0.0, self._target + steps * 60.0 /
                                    max(1, total - h)))
        if self._anim is None:
            self._step_smooth()

    def _step_smooth(self):
        self._anim = None
        try:
            cur = self.canvas.yview()[0]
        except Exception:
            return
        diff = self._target - cur
        if abs(diff) < 0.0006:
            try:
                self.canvas.yview_moveto(self._target)
            except Exception:
                pass
            return
        try:
            self.canvas.yview_moveto(cur + diff * 0.35)
        except Exception:
            return
        self._anim = self.after(16, self._step_smooth)

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
