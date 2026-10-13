"""Digital 88 x 125 mm notebooks for GoodNotes.

Outputs in _Print/GoodNotes/:
  notebooks/   cover + contents page + 60 pages + back cover, with page links
  templates/   single-page templates to import into GoodNotes
  covers/      cover images (PNG) for GoodNotes custom covers (rendered by build step)

Covers are original designs inspired by retro travel notebooks and minimalist
cat notebooks; no brand names or artwork are copied.

Run: python3 _Print/make_goodnotes.py
"""

import math
import random
import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_inserts as mi  # noqa: E402  (registers fonts)
from make_stickers import KUSHINA, KUSHINA_PAL, draw_pixels, hexrgb, tint  # noqa: E402

OUT = Path(__file__).resolve().parent / "GoodNotes"
W, H = mi.W, mi.H
PAGES = 60  # 30 sheets / 60 pages, like the paper notebooks

PAPER = hexrgb("#FBF8F1")
RULE = hexrgb("#D3CDC1")
DOT = hexrgb("#A39B8D")
INK = hexrgb("#2E2A26")
SOFT = hexrgb("#8A8378")


# ---------- small drawing helpers ----------

def fill(c, rgb, alpha=1.0):
    c.setFillColorRGB(*rgb)
    c.setFillAlpha(alpha)


def stroke(c, rgb, width=0.4, alpha=1.0):
    c.setStrokeColorRGB(*rgb)
    c.setStrokeAlpha(alpha)
    c.setLineWidth(width)


def reset_alpha(c):
    c.setFillAlpha(1)
    c.setStrokeAlpha(1)


def text(c, x, y, s, font="Sans", size=6, color=INK, align="left"):
    fill(c, color)
    c.setFont(font, size)
    {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align](x, y, s)


def spaced(c, x, y, s, font, size, color, tracking, align="center"):
    """Letter-spaced text (for small caps labels)."""
    widths = [pdfmetrics.stringWidth(ch, font, size) for ch in s]
    total = sum(widths) + tracking * (len(s) - 1)
    start = {"center": x - total / 2, "left": x, "right": x - total}[align]
    fill(c, color)
    c.setFont(font, size)
    for ch, w in zip(s, widths):
        c.drawString(start, y, ch)
        start += w + tracking


def arc_text(c, s, cx, cy, r, font, size, color, tracking=0.0):
    """Text along the top of a circle, centred at the top."""
    widths = [pdfmetrics.stringWidth(ch, font, size) + tracking for ch in s]
    total = sum(widths) - tracking
    angle = math.pi / 2 + total / (2 * r)
    fill(c, color)
    c.setFont(font, size)
    for ch, w in zip(s, widths):
        mid = angle - (w - tracking) / (2 * r)
        c.saveState()
        c.translate(cx + r * math.cos(mid), cy + r * math.sin(mid))
        c.rotate(math.degrees(mid) - 90)
        c.drawCentredString(0, 0, ch)
        c.restoreState()
        angle -= w / r


def paper_texture(c, base, seed, fibers=520, specks=260):
    """Kraft/handmade paper look: base colour, light fibres, dark specks."""
    rnd = random.Random(seed)
    fill(c, base)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    for _ in range(fibers):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        ang = rnd.uniform(0, math.pi)
        ln = rnd.uniform(0.6, 2.8) * mm
        light = rnd.random() < 0.7
        col = tint(base, 0.45) if light else tuple(v * 0.82 for v in base)
        stroke(c, col, width=rnd.uniform(0.15, 0.35), alpha=rnd.uniform(0.25, 0.6))
        c.line(x, y, x + ln * math.cos(ang), y + ln * math.sin(ang))
    for _ in range(specks):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        fill(c, tuple(v * 0.7 for v in base), alpha=rnd.uniform(0.15, 0.45))
        c.circle(x, y, rnd.uniform(0.08, 0.22), stroke=0, fill=1)
    reset_alpha(c)


def grain_texture(c, base, seed, n=2600):
    """Fine leatherette grain for the cream cat cover."""
    rnd = random.Random(seed)
    fill(c, base)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        dark = rnd.random() < 0.55
        fill(c, (0.55, 0.53, 0.5) if dark else (1, 1, 1), alpha=rnd.uniform(0.05, 0.14))
        c.ellipse(x, y, x + rnd.uniform(0.3, 0.9), y + rnd.uniform(0.2, 0.6), stroke=0, fill=1)
    reset_alpha(c)


def rounded_corner_mask(c, r=3.2 * mm):
    """Paint the page corners with the app-background-neutral paper colour so covers look rounded."""
    # GoodNotes shows the whole page; keep corners subtle by drawing a soft outline instead of cutting.
    stroke(c, (0, 0, 0), width=0.25, alpha=0.12)
    c.roundRect(0.3, 0.3, W - 0.6, H - 0.6, r, stroke=1, fill=0)
    reset_alpha(c)


def spine(c, color, width, label, label_color, font="Sans-B", size=5.2, tracking=0.9, stitches=True):
    fill(c, color)
    c.rect(0, 0, width, H, stroke=0, fill=1)
    fill(c, (0, 0, 0), alpha=0.18)
    c.rect(width - 0.6 * mm, 0, 0.6 * mm, H, stroke=0, fill=1)
    reset_alpha(c)
    if stitches:
        stroke(c, tint(color, 0.45), width=0.35)
        c.setDash(1.4 * mm, 1.1 * mm)
        c.line(width + 0.9 * mm, 3 * mm, width + 0.9 * mm, H - 3 * mm)
        c.setDash()
    c.saveState()
    c.translate(width / 2 + size * 0.36, H - 14 * mm)
    c.rotate(-90)
    spaced(c, 0, 0, label, font, size, label_color, tracking, align="left")
    c.restoreState()


def diamond_emblem(c, cx, cy, w, h, color, letter="G"):
    stroke(c, color, width=0.6)
    p = c.beginPath()
    p.moveTo(cx - w / 2, cy); p.lineTo(cx, cy + h / 2); p.lineTo(cx + w / 2, cy); p.lineTo(cx, cy - h / 2); p.close()
    c.drawPath(p, stroke=1, fill=0)
    p = c.beginPath()
    k = 0.7
    p.moveTo(cx - w * k / 2, cy); p.lineTo(cx, cy + h * k / 2); p.lineTo(cx + w * k / 2, cy); p.lineTo(cx, cy - h * k / 2); p.close()
    c.drawPath(p, stroke=1, fill=0)
    fill(c, color)
    c.rect(cx - 1.6 * mm, cy - 1.3 * mm, 3.2 * mm, 2.6 * mm, stroke=0, fill=1)
    text(c, cx, cy - 0.95 * mm, letter, font="Serif-B", size=6.2, color=(1, 1, 1), align="center")


def ribbon(c, cx, cy, w, h, color, label, label_color):
    fold = 2.2 * mm
    fill(c, tuple(v * 0.75 for v in color))
    for side in (-1, 1):
        x_in = cx + side * (w / 2 - 0.4 * mm)
        x_out = cx + side * (w / 2 + fold)
        p = c.beginPath()
        p.moveTo(x_in, cy - h / 2 - 0.9 * mm)
        p.lineTo(x_out, cy - h / 2 - 0.9 * mm)
        p.lineTo(x_out - side * 1.2 * mm, cy - 0.45 * mm)
        p.lineTo(x_out, cy + h / 2 - 0.9 * mm)
        p.lineTo(x_in, cy + h / 2 - 0.9 * mm)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    fill(c, color)
    c.roundRect(cx - w / 2, cy - h / 2, w, h, 0.8 * mm, stroke=0, fill=1)
    spaced(c, cx, cy - h * 0.2, label, "Sans-B", 4.4, label_color, 0.55)


def double_frame(c, x0, y0, x1, y1, color, r=4 * mm):
    stroke(c, color, width=0.9)
    c.roundRect(x0, y0, x1 - x0, y1 - y0, r, stroke=1, fill=0)
    stroke(c, color, width=0.35)
    g = 1.1 * mm
    c.roundRect(x0 + g, y0 + g, x1 - x0 - 2 * g, y1 - y0 - 2 * g, r - g, stroke=1, fill=0)


# ---------- pixel art ----------

def check(rows):
    w = len(rows[0])
    assert all(len(r) == w for r in rows), [len(r) for r in rows]
    return rows


# Original pixel bear reading a book (for the reading notebook).
BEAR = check([
    "...KKK........KKK...",
    "..KBbBK......KBbBK..",
    "..KBBBKKKKKKKKBBBK..",
    "...KBBBBBBBBBBBBK...",
    "..KBBBBBBBBBBBBBBK..",
    "..KBBBEBBBBBBEBBBK..",
    "..KBBBBBLLLLBBBBBK..",
    "..KBBBBLLNNLLBBBBK..",
    "...KBBBBLLLLBBBBK...",
    "....KKBBBBBBBBKK....",
    "...KBBBBBBBBBBBBK...",
    "..KBBBBBBBBBBBBBBK..",
    ".KBBKKKKKKKKKKKKBBK.",
    ".KBKRPPPPPKPPPPPRKBK",
    ".KBKRPpppPKPpppPRKBK",
    ".KBBKRPPPPKPPPPRKBBK",
    "..KBBKRRRRKRRRRKBBK.",
    "..KBBBKKKKKKKKKBBBK.",
    "..KbbBBBBBBBBBBBbbK.",
    "...KKKKKKKKKKKKKKK..",
])
BEAR = [r.ljust(20, ".")[:20] for r in BEAR]
BEAR_PAL = {
    "K": "#3b2a20", "B": "#8a5a3c", "b": "#6b4430", "L": "#dcb791", "E": "#1e1410",
    "N": "#2a1a12", "P": "#f4ecd8", "p": "#c9bd9f", "R": "#b5523b",
}


def illustration_panel(c, cx, cy, w, h, bg, art, pal, px, frame=hexrgb("#F2E6C9")):
    fill(c, frame)
    c.rect(cx - w / 2 - 1.4 * mm, cy - h / 2 - 1.4 * mm, w + 2.8 * mm, h + 2.8 * mm, stroke=0, fill=1)
    fill(c, bg)
    c.rect(cx - w / 2, cy - h / 2, w, h, stroke=0, fill=1)
    # halftone dots for a printed, vintage feel
    fill(c, tint(bg, 0.6), alpha=0.35)
    step = 1.6 * mm
    yy = cy - h / 2 + step / 2
    row = 0
    while yy < cy + h / 2:
        xx = cx - w / 2 + (step / 2 if row % 2 else step)
        while xx < cx + w / 2:
            c.circle(xx, yy, 0.22 * mm, stroke=0, fill=1)
            xx += step
        yy += step
        row += 1
    reset_alpha(c)
    aw, ah = len(art[0]) * px, len(art) * px
    # ground shadow
    fill(c, (0, 0, 0), alpha=0.16)
    c.ellipse(cx - aw * 0.38, cy - h / 2 + 2.2 * mm, cx + aw * 0.38, cy - h / 2 + 4.4 * mm, stroke=0, fill=1)
    reset_alpha(c)
    draw_pixels(c, art, pal, cx - aw / 2, cy - h / 2 + 3.2 * mm, px)


# ---------- covers ----------

RETRO = {
    "yellow": {"paper": hexrgb("#E2A847"), "ink": hexrgb("#3A2418"), "spine": hexrgb("#4A2C20"),
               "panel": hexrgb("#3F5E48"), "art": (BEAR, BEAR_PAL, 1.45 * mm)},
    "pink": {"paper": hexrgb("#D9A2A0"), "ink": hexrgb("#3A2020"), "spine": hexrgb("#40252A"),
             "panel": hexrgb("#9DB1B4"), "art": (KUSHINA, KUSHINA_PAL, 1.1 * mm)},
}


def retro_cover(c, style, title, subtitle, tagline, seed):
    s = RETRO[style]
    paper_texture(c, s["paper"], seed)
    sw = 7.5 * mm
    spine(c, s["spine"], sw, "GERERU · TRAVEL NOTES · 88×125", tint(s["paper"], 0.7))
    x0, x1 = sw + 3.4 * mm, W - 3.2 * mm
    y0, y1 = 3.4 * mm, H - 3.4 * mm
    double_frame(c, x0, y0, x1, y1, s["ink"])
    cx = (x0 + x1) / 2
    ribbon(c, cx, H - 23 * mm, 30 * mm, 3.6 * mm, s["ink"], "GERERU NOTES", s["paper"])
    # arched title with slanted side rules
    r = 40 * mm
    arc_text(c, title.upper(), cx, H - 72 * mm, r, "Serif-B", 15 if len(title) <= 6 else 12.5, s["ink"], tracking=0.6)
    stroke(c, s["ink"], width=0.7)
    c.line(cx - 27 * mm, H - 27.5 * mm, cx - 23 * mm, H - 40 * mm)
    c.line(cx + 27 * mm, H - 27.5 * mm, cx + 23 * mm, H - 40 * mm)
    spaced(c, cx, H - 41.2 * mm, subtitle.upper(), "Sans-B", 5.2, s["ink"], 0.9)
    spaced(c, cx, H - 45.5 * mm, "EST 2026", "Sans", 3.8, s["ink"], 0.7)
    art, pal, px = s["art"]
    illustration_panel(c, cx, H - 72 * mm, 34 * mm, 34 * mm, s["panel"], art, pal, px)
    y = 26 * mm
    for line in tagline:
        spaced(c, cx, y, line.upper(), "Sans-B", 3.7, s["ink"], 0.45)
        y -= 3.2 * mm
    diamond_emblem(c, cx, 10.5 * mm, 9 * mm, 5.4 * mm, s["ink"])
    rounded_corner_mask(c)


def retro_back(c, style, seed):
    s = RETRO[style]
    paper_texture(c, s["paper"], seed + 1)
    x0, x1 = 3.2 * mm, W - 3.4 * mm - 7.5 * mm
    double_frame(c, x0, 3.4 * mm, x1, H - 3.4 * mm, s["ink"])
    fill(c, s["spine"])
    c.rect(W - 7.5 * mm, 0, 7.5 * mm, H, stroke=0, fill=1)
    cx = (x0 + x1) / 2
    diamond_emblem(c, cx, H / 2 + 6 * mm, 12 * mm, 7.2 * mm, s["ink"])
    spaced(c, cx, H / 2 - 4 * mm, "LESS BUT BETTER", "Sans-B", 4.2, s["ink"], 0.8)
    spaced(c, cx, 9 * mm, "88 × 125 MM · 60 PAGES", "Sans", 3.6, s["ink"], 0.5)
    rounded_corner_mask(c)


# Original sitting tuxedo cat, drawn on a 100 x 120 grid (y up).
CAT_BODY = [
    ("M", 29, 95), ("C", 27, 101, 27, 106, 28, 111), ("C", 32, 109, 36, 106, 39, 104),
    ("C", 44, 106, 50, 106, 55, 104), ("C", 58, 106, 62, 109, 66, 111), ("C", 67, 106, 67, 100, 65, 95),
    ("C", 69, 87, 68, 78, 61, 72), ("C", 67, 62, 72, 46, 72, 30), ("C", 72, 20, 70, 13, 66, 9),
    ("L", 22, 9), ("C", 20, 18, 21, 34, 26, 50), ("C", 29, 60, 33, 67, 36, 71),
    ("C", 30, 77, 27, 87, 30, 96), ("Z",),
]
CAT_TAIL = [("M", 66, 12), ("C", 80, 8, 92, 9, 93, 16), ("C", 94, 22, 88, 26, 84, 24)]
CAT_BIB = [
    ("M", 41, 79), ("C", 44, 76, 50, 76, 53, 79), ("C", 54, 72, 52, 63, 50, 54),
    ("C", 49, 46, 51, 38, 49, 30), ("C", 46, 36, 44, 44, 44, 52), ("C", 43, 62, 40, 72, 41, 79), ("Z",),
]
CAT_PAWS = [(25, 2, 37, 11), (38, 2, 50, 11)]


def cat_path(c, segs, ox, oy, k):
    p = c.beginPath()
    for seg in segs:
        pts = [(ox + seg[i] * k, oy + seg[i + 1] * k) for i in range(1, len(seg), 2)]
        if seg[0] == "M":
            p.moveTo(*pts[0])
        elif seg[0] == "L":
            p.lineTo(*pts[0])
        elif seg[0] == "C":
            p.curveTo(*pts[0], *pts[1], *pts[2])
        else:
            p.close()
    return p


def draw_cat(c, ox, oy, k, ink=(0.08, 0.08, 0.08), bg=(1, 1, 1), label=True):
    fill(c, ink)
    c.drawPath(cat_path(c, CAT_BODY, ox, oy, k), stroke=0, fill=1)
    stroke(c, ink, width=5.2 * k)
    c.setLineCap(1)
    c.drawPath(cat_path(c, CAT_TAIL, ox, oy, k), stroke=1, fill=0)
    for x0, y0, x1, y1 in CAT_PAWS:
        fill(c, ink)
        c.roundRect(ox + x0 * k, oy + y0 * k, (x1 - x0) * k, (y1 - y0) * k, 4 * k, stroke=0, fill=1)
        stroke(c, bg, width=1.1 * k)
        c.line(ox + (x0 + 4) * k, oy + (y0 + 1.5) * k, ox + (x0 + 4) * k, oy + (y0 + 4.5) * k)
        c.line(ox + (x0 + 8) * k, oy + (y0 + 1.5) * k, ox + (x0 + 8) * k, oy + (y0 + 4.5) * k)
    fill(c, bg)
    c.drawPath(cat_path(c, CAT_BIB, ox, oy, k), stroke=0, fill=1)
    # face: two white dot eyes and a small muzzle
    for ex in (39, 55):
        c.circle(ox + ex * k, oy + 92 * k, 2.3 * k, stroke=0, fill=1)
    c.ellipse(ox + 43.5 * k, oy + 82 * k, ox + 50.5 * k, oy + 87 * k, stroke=0, fill=1)
    fill(c, ink)
    c.ellipse(ox + 45.8 * k, oy + 84.6 * k, ox + 48.2 * k, oy + 86.2 * k, stroke=0, fill=1)
    if label:
        c.saveState()
        c.translate(ox + 76 * k, oy + 36 * k)
        c.rotate(-32)
        text(c, 0, 0, "hmm~", font="Sans-B", size=8.5 * k / (0.44 * mm), color=ink)
        c.restoreState()


CREAM = hexrgb("#F1EDE4")
BLACK = hexrgb("#1D1C1B")


def cat_cover(c, title, subtitle, tagline, seed):
    grain_texture(c, CREAM, seed)
    sw = 12.5 * mm
    spine(c, BLACK, sw, f"{title.lower()}  ·  {subtitle}", CREAM, font="Sans-B", size=5.6,
          tracking=0.5, stitches=False)
    # small bracketed motto at the bottom of the spine
    c.saveState()
    c.translate(sw / 2 + 1.8, 34 * mm)
    c.rotate(-90)
    text(c, 0, 0, "( one quiet page a day )", font="Sans", size=4.4, color=CREAM)
    c.restoreState()
    x0, x1 = sw, W
    tx = x1 - 6 * mm
    text(c, tx, H - 19 * mm, title.lower(), font="Sans-B", size=17, color=BLACK, align="right")
    text(c, tx, H - 24.5 * mm, subtitle, font="Sans", size=5.4, color=BLACK, align="right")
    k = 0.44 * mm
    draw_cat(c, (x0 + x1) / 2 - 50 * k, 15 * mm, k, ink=BLACK, bg=CREAM)
    text(c, (x0 + x1) / 2, 8.5 * mm, tagline, font="Sans-B", size=5.0, color=BLACK, align="center")
    rounded_corner_mask(c)


def cat_back(c, seed):
    grain_texture(c, CREAM, seed + 1)
    fill(c, BLACK)
    c.rect(W - 12.5 * mm, 0, 12.5 * mm, H, stroke=0, fill=1)
    cx = (W - 12.5 * mm) / 2
    k = 0.18 * mm
    draw_cat(c, cx - 50 * k, H / 2 - 6 * mm, k, ink=BLACK, bg=CREAM, label=False)
    stroke(c, BLACK, width=0.3)
    c.line(6 * mm, 17 * mm, W - 18.5 * mm, 17 * mm)
    text(c, 6 * mm, 12.8 * mm, "Gereru · Сэтгэх", font="Sans-B", size=5, color=BLACK)
    text(c, 6 * mm, 9.4 * mm, "88 × 125 mm · 60 хуудас · dot grid", font="Sans", size=4.3, color=BLACK)
    text(c, 6 * mm, 6.4 * mm, "Read → Capture → Understand → Connect → Review", font="Sans", size=3.6, color=SOFT)
    rounded_corner_mask(c)


# ---------- inner pages ----------

class DigitalPage(mi.Page):
    """Symmetric margins: on screen there is no binding side."""

    def __init__(self, c, number):
        super().__init__(c, number)
        self.x0, self.x1 = 6 * mm, W - 6 * mm
        self.right_hand = True


def paper(c):
    fill(c, PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def home_icon(c, x, y, s=2.6 * mm, color=SOFT):
    stroke(c, color, width=0.45)
    p = c.beginPath()
    p.moveTo(x, y + s * 0.55); p.lineTo(x + s / 2, y + s); p.lineTo(x + s, y + s * 0.55)
    c.drawPath(p, stroke=1, fill=0)
    c.rect(x + s * 0.18, y, s * 0.64, s * 0.55, stroke=1, fill=0)


def chrome(c, number, index_key):
    """Page number and a home link to the contents page."""
    text(c, W / 2, 3.6 * mm, str(number), size=5, color=SOFT, align="center")
    hx, hy = W - 6 * mm - 2.6 * mm, H - 5.6 * mm
    home_icon(c, hx, hy)
    c.linkRect("", index_key, (hx - 2.2 * mm, hy - 2.2 * mm, hx + 4.8 * mm, hy + 4.8 * mm),
               relative=0, thickness=0)


def page_blank(c, p):
    pass


def page_dot(c, p, step=5 * mm):
    fill(c, DOT)
    y = H - 9 * mm
    while y > 7 * mm:
        x = p.x0
        while x <= p.x1 + 0.1:
            c.circle(x, y, 0.36, stroke=0, fill=1)
            x += step
        y -= step


def page_lined(c, p, pitch=6 * mm):
    stroke(c, RULE, width=0.35)
    y = H - 11 * mm
    while y > 8 * mm:
        c.line(p.x0, y, p.x1, y)
        y -= pitch


def page_grid(c, p, step=5 * mm):
    stroke(c, tint(RULE, 0.75), width=0.3)
    x = p.x0
    while x <= p.x1 + 0.1:
        c.line(x, 7 * mm, x, H - 9 * mm)
        x += step
    y = H - 9 * mm
    while y >= 7 * mm - 0.1:
        c.line(p.x0, y, p.x1, y)
        y -= step


def page_reading(c, p):
    top = H - mi.TOP - 3.5 * mm
    bottom = mi.reading_entry(p, top)
    p.hline(bottom - 2.6 * mm, color=mi.FAINT, width=0.6)
    mi.reading_entry(p, bottom - 6.4 * mm)


def page_practice(c, p):
    mi.practice_entry(p)


PAGE_TYPES = {
    "blank": page_blank, "dot": page_dot, "lined": page_lined, "grid": page_grid,
    "reading": page_reading, "practice": page_practice,
}


def contents_page(c, index_key, page_keys):
    paper(c)
    p = DigitalPage(c, 1)
    y = p.heading("Агуулга", y=H - 9 * mm)
    text(c, p.x0, y, "Сэдэв", font="Sans-B", size=5, color=SOFT)
    text(c, p.x1, y, "х.", font="Sans-B", size=5, color=SOFT, align="right")
    y -= 1.5 * mm
    for _ in range(8):
        y -= 5.4 * mm
        stroke(c, RULE, width=0.35)
        c.line(p.x0, y, p.x1 - 8 * mm, y)
        c.line(p.x1 - 6 * mm, y, p.x1, y)
    y -= 7 * mm
    text(c, p.x0, y, "Хуудас руу үсрэх", font="Sans-B", size=5.2, color=SOFT)
    y -= 2.5 * mm
    cols, cw, ch = 10, (p.x1 - p.x0) / 10, 6.2 * mm
    for i, key in enumerate(page_keys):
        r, col = divmod(i, cols)
        x = p.x0 + col * cw
        yy = y - (r + 1) * ch
        stroke(c, RULE, width=0.3)
        c.roundRect(x + 0.4 * mm, yy + 0.4 * mm, cw - 0.8 * mm, ch - 0.8 * mm, 0.8 * mm, stroke=1, fill=0)
        text(c, x + cw / 2, yy + ch / 2 - 1.6, str(i + 1), size=5.4, color=INK, align="center")
        c.linkRect("", key, (x, yy, x + cw, yy + ch), relative=0, thickness=0)
    c.bookmarkPage(index_key)


# ---------- notebooks ----------

NOTEBOOKS = [
    {"file": "Унших · Reading log", "cover": ("retro", "yellow"), "pages": "reading",
     "title": "Унших", "subtitle": "Reading log",
     "tagline": ["Read · Capture · Understand", "Connect · Question · Review"], "seed": 11},
    {"file": "Хэрэгжүүлэх · Practice log", "cover": ("retro", "pink"), "pages": "practice",
     "title": "Хэрэгжүүлэх", "subtitle": "Practice log",
     "tagline": ["Understanding and living", "are two different things"], "seed": 23},
    {"file": "Сэтгэх · Thinking", "cover": ("cat",), "pages": "dot",
     "title": "Сэтгэх", "subtitle": "the gathering of thoughts.",
     "tagline": "Get your daily dose of quiet thinking.", "seed": 37},
]


def draw_cover(c, nb):
    if nb["cover"][0] == "retro":
        retro_cover(c, nb["cover"][1], nb["title"], nb["subtitle"], nb["tagline"], nb["seed"])
    else:
        cat_cover(c, nb["title"], nb["subtitle"], nb["tagline"], nb["seed"])


def draw_back(c, nb):
    if nb["cover"][0] == "retro":
        retro_back(c, nb["cover"][1], nb["seed"])
    else:
        cat_back(c, nb["seed"])


def build_notebook(nb, path):
    c = canvas.Canvas(str(path), pagesize=(W, H))
    c.setTitle(nb["file"])
    c.setAuthor("Gereru")
    c.setSubject("88 × 125 mm digital notebook for GoodNotes")
    page_keys = [f"p{i}" for i in range(1, PAGES + 1)]
    # cover
    draw_cover(c, nb)
    c.bookmarkPage("cover")
    c.addOutlineEntry("Нүүр", "cover", level=0)
    c.showPage()
    # contents
    contents_page(c, "index", page_keys)
    c.addOutlineEntry("Агуулга", "index", level=0)
    c.showPage()
    # pages
    # draw the page body once as a reusable form; every page references it
    c.beginForm("body")
    paper(c)
    PAGE_TYPES[nb["pages"]](c, DigitalPage(c, 1))
    c.endForm()
    for i, key in enumerate(page_keys, start=1):
        c.doForm("body")
        chrome(c, i, "index")
        c.bookmarkPage(key)
        if i % 10 == 1:
            c.addOutlineEntry(f"Хуудас {i}–{i + 9}", key, level=0)
        c.showPage()
    draw_back(c, nb)
    c.bookmarkPage("back")
    c.addOutlineEntry("Ар нүүр", "back", level=0)
    c.showPage()
    c.save()


def build_template(kind, path):
    c = canvas.Canvas(str(path), pagesize=(W, H))
    c.setTitle(f"Template · {kind}")
    c.setAuthor("Gereru")
    paper(c)
    p = DigitalPage(c, 1)
    PAGE_TYPES[kind](c, p)
    c.showPage()
    c.save()


def build_single_covers(folder):
    for nb in NOTEBOOKS:
        c = canvas.Canvas(str(folder / f"{nb['file']} · cover.pdf"), pagesize=(W, H))
        c.setTitle(f"{nb['file']} · cover")
        c.setAuthor("Gereru")
        draw_cover(c, nb)
        c.showPage()
        c.save()


def build_covers_pdf(path):
    c = canvas.Canvas(str(path), pagesize=(W, H))
    c.setTitle("Covers")
    for nb in NOTEBOOKS:
        draw_cover(c, nb)
        c.showPage()
    for nb in NOTEBOOKS:
        draw_back(c, nb)
        c.showPage()
    c.save()


def main():
    (OUT / "notebooks").mkdir(parents=True, exist_ok=True)
    (OUT / "templates").mkdir(parents=True, exist_ok=True)
    (OUT / "covers").mkdir(parents=True, exist_ok=True)
    for nb in NOTEBOOKS:
        build_notebook(nb, OUT / "notebooks" / f"{nb['file']}.pdf")
    for kind in PAGE_TYPES:
        build_template(kind, OUT / "templates" / f"{kind}.pdf")
    build_covers_pdf(OUT / "covers" / "covers.pdf")
    build_single_covers(OUT / "covers")
    export_cover_pngs(OUT / "covers" / "covers.pdf")


def export_cover_pngs(pdf, dpi=300):
    """PNG covers for GoodNotes' custom-cover picker (needs poppler's pdftoppm)."""
    import shutil
    import subprocess
    if not shutil.which("pdftoppm"):
        print("pdftoppm not found; skipping PNG covers")
        return
    names = [f"{nb['file']} · cover" for nb in NOTEBOOKS] + [f"{nb['file']} · back" for nb in NOTEBOOKS]
    for i, name in enumerate(names, start=1):
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", "-f", str(i), "-l", str(i),
                        str(pdf), str(pdf.parent / name)], check=True)


if __name__ == "__main__":
    main()
