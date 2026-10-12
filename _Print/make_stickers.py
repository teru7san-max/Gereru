"""Generate a printable A4 sticker sheet for the traveler's notebook.

Page 1: fold-over tag tabs, one per concept tag plus family and blank tabs.
Page 2: pixel-art stickers and response-tag dots.

Print on A4 sticker paper at 100% (Actual size), then cut along the grey lines.
Run: python3 _Print/make_stickers.py
"""

import math
import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_inserts import SYMBOLS, TAGS, draw_icon  # noqa: E402  (also registers fonts)

OUT = Path(__file__).resolve().parent / "Tag-stickers-A4.pdf"
A4W, A4H = 210 * mm, 297 * mm
CUT = (0.72, 0.72, 0.72)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def tint(rgb, k):
    return tuple(1 - (1 - v) * k for v in rgb)


DARK = hexrgb("#2b2b2b")
WHITE = (1, 1, 1)

# family -> (color, ink on that color)
FAMILY_STYLE = {
    "Mind": ("#4A90C8", WHITE),
    "Emotions": ("#2BA7A0", WHITE),
    "Desire & happiness": ("#F2B630", DARK),
    "Self": ("#8A63C7", WHITE),
    "Freedom & acceptance": ("#79C267", DARK),
    "Hope & inner": ("#3949AB", WHITE),
    "Action & craft": ("#E4572E", WHITE),
    "Love": ("#F07AA0", DARK),
}

# ---------- fold-over tabs ----------
# Strip: TAB_W wide. Glue zone, then the visible flag, a fold line in the middle,
# the flag's back, and a second glue zone. Back content is rotated 180° so it
# reads upright from the back of the page after folding over the page edge.
TAB_W, GLUE, FLAG = 16 * mm, 6 * mm, 10 * mm
TAB_H = 2 * (GLUE + FLAG)


def split_word(word, font, size, width):
    if pdfmetrics.stringWidth(word, font, size) <= width:
        return [word]
    if "-" in word:
        a, b = word.split("-", 1)
        return [a + "-", b]
    return [word]


def flag_face(c, x, y, icon, label, ink):
    """Draw icon + label inside a FLAG-tall face whose bottom-left is (x, y)."""
    font, size = "Sans-B", 4.5
    lines = split_word(label, font, size, TAB_W - 1.6 * mm)
    while max(pdfmetrics.stringWidth(l, font, size) for l in lines) > TAB_W - 1.2 * mm:
        size -= 0.2
    icon_size = 4.2 * mm if len(lines) == 1 else 3.6 * mm
    lead = size * 1.12
    block = icon_size + 0.7 * mm + lead * len(lines)
    top = y + FLAG / 2 + block / 2
    if icon:
        draw_icon(c, icon, x + TAB_W / 2 - icon_size / 2, top - icon_size, icon_size,
                  color=ink, width=0.75)
    c.setFillColorRGB(*ink)
    c.setFont(font, size)
    ty = top - icon_size - 0.7 * mm - size * 0.82
    for line in lines:
        c.drawCentredString(x + TAB_W / 2, ty, line)
        ty -= lead


def tab(c, x, y, family, icon, label):
    color = hexrgb(FAMILY_STYLE[family][0])
    ink = FAMILY_STYLE[family][1]
    glue = tint(color, 0.28)
    c.setStrokeColorRGB(*CUT)
    c.setLineWidth(0.25)
    c.setFillColorRGB(*glue)
    c.rect(x, y, TAB_W, GLUE, stroke=0, fill=1)
    c.rect(x, y + TAB_H - GLUE, TAB_W, GLUE, stroke=0, fill=1)
    c.setFillColorRGB(*color)
    c.rect(x, y + GLUE, TAB_W, 2 * FLAG, stroke=0, fill=1)
    c.rect(x, y, TAB_W, TAB_H, stroke=1, fill=0)
    # fold line
    c.setStrokeColorRGB(*tint(ink, 0.35) if ink == WHITE else tint(ink, 0.5))
    c.setDash(0.8, 0.8)
    c.setLineWidth(0.25)
    c.line(x + 0.6 * mm, y + TAB_H / 2, x + 1.8 * mm, y + TAB_H / 2)
    c.line(x + TAB_W - 1.8 * mm, y + TAB_H / 2, x + TAB_W - 0.6 * mm, y + TAB_H / 2)
    c.setDash()
    flag_face(c, x, y + GLUE, icon, label, ink)
    c.saveState()
    c.translate(x + TAB_W, y + TAB_H)
    c.rotate(180)
    flag_face(c, 0, GLUE, icon, label, ink)
    c.restoreState()


def tabs_page(c):
    items = []
    for family, icon, tags in TAGS:
        items.append((family, icon, family.split(" & ")[0].upper()))
        items += [(family, icon, t) for t in tags.split(" · ")]
        items += [(family, icon, ""), (family, icon, "")]  # blanks: write your own
    gap, margin_x, top = 2 * mm, 9 * mm, A4H - 22 * mm
    cols = int((A4W - 2 * margin_x + gap) // (TAB_W + gap))
    x0 = (A4W - (cols * TAB_W + (cols - 1) * gap)) / 2
    c.setFillColorRGB(*DARK)
    c.setFont("Serif-B", 12)
    c.drawString(x0, A4H - 13 * mm, "Tag tabs")
    c.setFont("Sans", 6.5)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(x0 + 24 * mm, A4H - 13 * mm,
                 "Хайчлаад, тасархай шугамаар хуудасны ирмэг дээгүүр нугалж наа. "
                 "Хоосон tab дээр өөрөө бич.")
    for i, (family, icon, label) in enumerate(items):
        col, row = i % cols, i // cols
        x = x0 + col * (TAB_W + gap)
        y = top - (row + 1) * TAB_H - row * gap
        tab(c, x, y, family, icon, label)
    return len(items)


# ---------- pixel art ----------

def draw_pixels(c, rows, palette, x, y, px):
    h = len(rows)
    for i, row in enumerate(rows):
        for j, ch in enumerate(row):
            if ch == ".":
                continue
            c.setFillColorRGB(*hexrgb(palette[ch]))
            c.rect(x + j * px, y + (h - 1 - i) * px, px + 0.06, px + 0.06, stroke=0, fill=1)


def check(rows):
    w = len(rows[0])
    assert all(len(r) == w for r in rows), [len(r) for r in rows]
    return rows


# Fan pixel art inspired by Kushina (long red hair, hairclip). Personal use only.
KUSHINA = check([
    "......KKKKKKKK......",
    "....KKRRRRRRRRKK....",
    "...KRRhhRRRRRRRRK...",
    "..KRRhRRRRRRRRRRRK..",
    "..KRRRRRRRRRRRRCCK..",
    ".KRRRRRRRRRRRRRCCRK.",
    ".KRRrRRRRRrRRRRRRRK.",
    ".KRRrSSRRRSrRRRrRRK.",
    ".KRRSSSSSSSSSSSSRRK.",
    ".KRRSWESSSSSSWESRRK.",
    ".KRRSEESSSSSSEESRRK.",
    ".KRRSBSSSSSSSSBSRRK.",
    ".KRRSSSSSMMSSSSSRRK.",
    ".KRRRKSSSSSSSSKRRRK.",
    ".KRRRRKKSSSSKKRRRRK.",
    ".KRRRKTTTTTTTTKRRRK.",
    ".KRRKTTTGGGGTTTKRRK.",
    ".KRRKTKGGGGGGKTKRRK.",
    ".KRRKSKGGGGGGKSKRRK.",
    "..KrrKGGGGGGGGKrrK..",
    "..KrrKGGGGGGGGKrrK..",
    "...KKgGGGGGGGGgKK...",
    "....KgGGGGGGGGgK....",
    "....KKKKKKKKKKKK....",
    ".....KFFK..KFFK.....",
    ".....KKKK..KKKK.....",
])
KUSHINA_PAL = {
    "K": "#3a2328", "R": "#d8343a", "r": "#a8242e", "h": "#f27365", "S": "#fde3cf",
    "E": "#4b3b5c", "W": "#ffffff", "B": "#f59ca4", "M": "#c4504f", "C": "#e9c45c",
    "T": "#f6f1e6", "G": "#5a8a64", "g": "#3e6449", "F": "#5b3b2b",
}

HEART = check([
    "..KKK...KKK..",
    ".KRRRK.KRRRK.",
    "KRhhRRKRRRRRK",
    "KRhRRRRRRRRRK",
    "KRRRRRRRRRRRK",
    "KRRRRRRRRRRrK",
    ".KRRRRRRRRrK.",
    "..KRRRRRRrK..",
    "...KRRRRrK...",
    "....KRRrK....",
    ".....KrK.....",
    "......K......",
])
HEART_PAL = {"K": "#5a1f33", "R": "#f05d84", "r": "#c73b62", "h": "#ffc2d1"}


def spiral_rows(n=19, turns=3.0):
    cx = cy = n // 2
    a = (n / 2 - 1.2) / (turns * 2 * math.pi)
    grid = [["."] * n for _ in range(n)]
    steps = 4000
    for k in range(steps + 1):
        t = turns * 2 * math.pi * k / steps
        r = a * t
        x, y = round(cx + r * math.cos(t)), round(cy - r * math.sin(t))
        if 0 <= x < n and 0 <= y < n:
            grid[y][x] = "I" if r < n / 6 else ("M" if r < n / 3 else "O")
    return ["".join(r) for r in grid]


SPIRAL_PAL = {"I": "#a81f2a", "M": "#d8402f", "O": "#f08a2e"}


def helix_rows(w=15, turns=3.0, rx=6.3, ry=3.2, pitch=6.0):
    """A tilted coil spring: front arcs bright, back arcs dim."""
    h = int(math.ceil(pitch * turns + 2 * ry + 2))
    grid = [["."] * w for _ in range(h)]
    cx = (w - 1) / 2
    pts = []
    for k in range(4000):
        t = turns * 2 * math.pi * k / 3999
        x = round(cx + rx * math.cos(t))
        y = round(h - 1 - ry - 0.5 - pitch * t / (2 * math.pi) + ry * math.sin(t))
        pts.append((x, y, math.sin(t) > 0))
    for x, y, front in pts:  # back arcs first, front arcs on top
        if not front:
            grid[y][x] = "b"
    for x, y, front in pts:
        if front:
            grid[y][x] = "F"
    rows = ["".join(r) for r in grid]
    return [r for r in rows if set(r) != {"."}]


HELIX_PAL = {"F": "#3949AB", "b": "#9fa8da"}

SUNRISE = check([
    "........Y........",
    "..Y.....Y.....Y..",
    "...Y.........Y...",
    "......SSSSS......",
    "YY..SSSSSSSSS..YY",
    "...SSSSssSSSSS...",
    "..SSSssSSSSSSSS..",
    "..SSSsSSSSSSSSS..",
    ".SSSSSSSSSSSSSSS.",
    "HHHHHHHHHHHHHHHHH",
    "..hhhhhhhhhhhhh..",
    ".....hhhhhhh.....",
])
SUNRISE_PAL = {"Y": "#f6b63a", "S": "#ffcf4a", "s": "#fff1a8", "H": "#e0763a", "h": "#f3a46b"}


def sticker(c, x, y, rows, pal, px, label=None, label_color=DARK):
    """White rounded backing with pixel art and an optional label; (x, y) = bottom-left."""
    pad = 1.6 * mm
    art_w, art_h = len(rows[0]) * px, len(rows) * px
    lab_h = 3.6 * mm if label else 0
    w, h = art_w + 2 * pad, art_h + 2 * pad + lab_h
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*CUT)
    c.setLineWidth(0.3)
    c.roundRect(x, y, w, h, 1.6 * mm, stroke=1, fill=1)
    draw_pixels(c, rows, pal, x + pad, y + pad + lab_h, px)
    if label:
        c.setFillColorRGB(*label_color)
        c.setFont("Sans-B", 6)
        c.drawCentredString(x + w / 2, y + pad + 0.4 * mm, label)
    return w, h


DOT_STYLE = {
    "insight": ("#F2B630", DARK),
    "resonates": ("#F07AA0", DARK),
    "question": ("#4A90C8", WHITE),
    "disagree": ("#8a8a8a", WHITE),
    "review": ("#2BA7A0", WHITE),
    "active": ("#E4572E", WHITE),
}


def dots(c, x0, y_top, per=7, d=9 * mm, gap=2.4 * mm):
    y = y_top
    for sym, tag, _ in SYMBOLS:
        color, ink = DOT_STYLE[tag]
        for k in range(per):
            cx = x0 + k * (d + gap) + d / 2
            c.setFillColorRGB(*hexrgb(color))
            c.setStrokeColorRGB(*CUT)
            c.setLineWidth(0.3)
            c.circle(cx, y - d / 2, d / 2, stroke=1, fill=1)
            c.setFillColorRGB(*ink)
            c.setFont("Sans-B", 10.5)
            c.drawCentredString(cx, y - d / 2 - 3.6, sym)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont("Sans", 6.5)
        c.drawString(x0 + per * (d + gap) + 1 * mm, y - d / 2 - 2.2, tag)
        y -= d + gap
    return y


def pixel_page(c):
    m = 14 * mm
    c.setFillColorRGB(*DARK)
    c.setFont("Serif-B", 12)
    c.drawString(m, A4H - 13 * mm, "Pixel stickers")
    y = A4H - 22 * mm
    row = [
        (KUSHINA, KUSHINA_PAL, 1.35 * mm, "KUSHINA", "#d8343a"),
        (KUSHINA, KUSHINA_PAL, 1.0 * mm, None, None),
        (HEART, HEART_PAL, 2.0 * mm, "LOVE", "#c73b62"),
        (HEART, HEART_PAL, 1.3 * mm, None, None),
    ]
    x = m
    tallest = 0
    for rows, pal, px, label, col in row:
        w, h = sticker(c, x, y - (len(rows) * px + 3.2 * mm + (3.6 * mm if label else 0)),
                       rows, pal, px, label, hexrgb(col) if col else DARK)
        x += w + 5 * mm
        tallest = max(tallest, h)
    y -= tallest + 6 * mm

    spiral = spiral_rows()
    helix = helix_rows()
    row2 = [
        (spiral, SPIRAL_PAL, 1.5 * mm, "SPIRAL", "#d8402f"),
        (helix, HELIX_PAL, 1.4 * mm, "HELIX", "#3949AB"),
        (SUNRISE, SUNRISE_PAL, 1.8 * mm, "HOPE", "#e0763a"),
        (spiral, SPIRAL_PAL, 1.0 * mm, None, None),
        (HEART, HEART_PAL, 1.0 * mm, None, None),
    ]
    x, tallest = m, 0
    for rows, pal, px, label, col in row2:
        h_need = len(rows) * px + 3.2 * mm + (3.6 * mm if label else 0)
        w, h = sticker(c, x, y - h_need, rows, pal, px, label, hexrgb(col) if col else DARK)
        x += w + 5 * mm
        tallest = max(tallest, h)
    y -= tallest + 9 * mm

    c.setFillColorRGB(*DARK)
    c.setFont("Serif-B", 10)
    c.drawString(m, y, "Response dots")
    dots(c, m, y - 4 * mm)
    c.setFont("Sans", 6)
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.drawString(m, 12 * mm, "● active: зөвхөн бодитоор хэрэгжүүлсэн үед. "
                             "Kushina: fan pixel art, хувийн хэрэгцээнд.")


def main():
    c = canvas.Canvas(str(OUT), pagesize=(A4W, A4H))
    c.setTitle("Tag stickers · traveler's notebook")
    c.setAuthor("Gereru")
    tabs_page(c)
    c.showPage()
    pixel_page(c)
    c.showPage()
    c.save()


if __name__ == "__main__":
    main()
