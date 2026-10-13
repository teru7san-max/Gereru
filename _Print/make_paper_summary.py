"""Two-page 88 x 125 mm research summary (GoodNotes / traveler's notebook size).

Paper: Ihara et al. (2021) Advantage of Handwriting Over Typing on Learning Words:
Evidence From an N400 Event-Related Potential Index. Front. Hum. Neurosci. 15:679191.
doi:10.3389/fnhum.2021.679191 (CC BY 4.0)

Values marked "≈" were measured from the paper's figures (Fig. 3D, 3E, 4) at 400 dpi
against the axis ticks; all other numbers are quoted from the paper's text.
Run: python3 _Print/make_paper_summary.py
"""

import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_inserts  # noqa: E402,F401  (registers fonts)
from make_stickers import hexrgb, tint  # noqa: E402

OUT = Path(__file__).resolve().parent / "GoodNotes" / "summaries" / "Handwriting vs typing · Ihara 2021.pdf"
W, H = 88 * mm, 125 * mm
X0, X1 = 6 * mm, W - 6 * mm

PAPER = hexrgb("#FBF8F1")
INK = hexrgb("#2B2824")
INK2 = hexrgb("#5E5850")
MUTED = hexrgb("#8F887C")
GRID = hexrgb("#E4DED3")
# categorical slots 1-3 of the reference palette (validated all-pairs on this surface)
SERIES = {"ink": hexrgb("#2a78d6"), "dig": hexrgb("#eb6834"), "key": hexrgb("#1baf7a")}
NAMES = {"ink": "Ink pen", "dig": "Digital pen", "key": "Keyboard"}
ORDER = ["ink", "dig", "key"]


# ---------- helpers ----------

def fill(c, rgb):
    c.setFillColorRGB(*rgb)


def stroke(c, rgb, w=0.4):
    c.setStrokeColorRGB(*rgb)
    c.setLineWidth(w)


def text(c, x, y, s, font="Sans", size=6, color=INK, align="left"):
    fill(c, color)
    c.setFont(font, size)
    {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align](x, y, s)


def wrap(c, x, y, s, width, font="Sans", size=6, color=INK, leading=None):
    leading = leading or size * 1.32
    line = ""
    for word in s.split():
        trial = (line + " " + word).strip()
        if pdfmetrics.stringWidth(trial, font, size) <= width:
            line = trial
        else:
            text(c, x, y, line, font, size, color)
            y -= leading
            line = word
    if line:
        text(c, x, y, line, font, size, color)
        y -= leading
    return y


def rich_line(c, x, y, parts, size):
    """Draw [(text, font, color), ...] on one line."""
    for s, font, color in parts:
        text(c, x, y, s, font, size, color)
        x += pdfmetrics.stringWidth(s, font, size)
    return x


def bar(c, x, y0, w, h, color, r=0.55 * mm):
    """Vertical bar anchored to the baseline with a rounded data end."""
    if h <= 0.05:
        stroke(c, color, 0.8)
        c.line(x, y0, x + w, y0)
        return
    fill(c, color)
    r = min(r, h, w / 2)
    c.roundRect(x, y0, w, h, r, stroke=0, fill=1)
    c.rect(x, y0, w, min(r, h), stroke=0, fill=1)


def hbar(c, x0, y, w, h, color, r=0.55 * mm):
    fill(c, color)
    r = min(r, w, h / 2)
    c.roundRect(x0, y, w, h, r, stroke=0, fill=1)
    c.rect(x0, y, min(r, w), h, stroke=0, fill=1)


def bracket(c, xa, xb, y, label, tick=0.9 * mm):
    stroke(c, INK2, 0.35)
    p = c.beginPath()
    p.moveTo(xa, y - tick); p.lineTo(xa, y); p.lineTo(xb, y); p.lineTo(xb, y - tick)
    c.drawPath(p, stroke=1, fill=0)
    text(c, (xa + xb) / 2, y + 0.7 * mm, label, size=4.4, color=INK2, align="center")


def section(c, y, title, note=None):
    text(c, X0, y, title, font="Sans-B", size=6.4, color=INK)
    if note:
        text(c, X1, y, note, size=4.3, color=MUTED, align="right")
    return y - 2.2 * mm


def swatch(c, x, y, key):
    fill(c, SERIES[key])
    c.roundRect(x, y - 0.3 * mm, 2.4 * mm, 2.4 * mm, 0.4 * mm, stroke=0, fill=1)


def legend(c, y):
    x = X0
    for k in ORDER:
        swatch(c, x, y, k)
        text(c, x + 3.2 * mm, y, NAMES[k], size=5.2, color=INK2)
        x += 3.2 * mm + pdfmetrics.stringWidth(NAMES[k], "Sans", 5.2) + 4.5 * mm


def paper(c):
    fill(c, PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def footer(c, n):
    text(c, W / 2, 3.6 * mm, f"{n} / 2", size=4.6, color=MUTED, align="center")


# ---------- page 1 ----------

def page1(c):
    paper(c)
    y = H - 8 * mm
    text(c, X0, y, "RESEARCH SUMMARY", font="Sans-B", size=4.6, color=MUTED)
    text(c, X1, y, "Ihara et al., 2021", size=4.6, color=MUTED, align="right")
    y -= 6 * mm
    text(c, X0, y, "Handwriting vs typing:", font="Serif-B", size=9.6)
    y -= 4.2 * mm
    text(c, X0, y, "learning new words", font="Serif-B", size=9.6)
    y -= 3.2 * mm

    # main idea
    box_top = y
    lines = [
        [("Writing new words ", "Sans", INK), ("by hand", "Sans-B", INK),
         (" (ink pen or digital pen)", "Sans", INK)],
        [("left a ", "Sans", INK), ("bigger brain trace of learning", "Sans-B", INK),
         (" than typing,", "Sans", INK)],
        [("even though typing let people write ", "Sans", INK), ("23% more", "Sans-B", INK)],
        [("repetitions", "Sans-B", INK), (". Test scores right after did not differ.", "Sans", INK)],
    ]
    for parts in lines:
        assert sum(pdfmetrics.stringWidth(t, f, 5.4) for t, f, _ in parts) < X1 - X0 - 4 * mm, parts
    h = len(lines) * 3.0 * mm + 3.2 * mm
    fill(c, tint(SERIES["ink"], 0.1))
    c.roundRect(X0, box_top - h, X1 - X0, h, 1.4 * mm, stroke=0, fill=1)
    fill(c, SERIES["ink"])
    c.rect(X0, box_top - h, 0.8 * mm, h, stroke=0, fill=1)
    ly = box_top - 3.6 * mm
    for parts in lines:
        rich_line(c, X0 + 2.6 * mm, ly, parts, 5.4)
        ly -= 3.0 * mm
    y = box_top - h - 4.4 * mm

    # study design
    y = section(c, y, "The study")
    tiles = [("33", "adults (Japanese)"), ("60", "Indonesian words"), ("10 min", "per tool, 20 words")]
    tw = (X1 - X0 - 2 * 1.6 * mm) / 3
    for i, (big, small) in enumerate(tiles):
        tx = X0 + i * (tw + 1.6 * mm)
        stroke(c, GRID, 0.4)
        c.roundRect(tx, y - 7.8 * mm, tw, 7.8 * mm, 1 * mm, stroke=1, fill=0)
        text(c, tx + tw / 2, y - 4.0 * mm, big, font="Sans-B", size=7.6, color=INK, align="center")
        text(c, tx + tw / 2, y - 6.5 * mm, small, size=4.3, color=INK2, align="center")
    y -= 10.4 * mm
    steps = ["Learn", "Mood check", "Word test", "EEG (N400)"]
    sw = (X1 - X0) / len(steps)
    for i, s in enumerate(steps):
        cx = X0 + sw * (i + 0.5)
        text(c, cx, y, s, font="Sans-B", size=4.8, color=INK2, align="center")
        if i < len(steps) - 1:
            text(c, X0 + sw * (i + 1), y, "→", size=5, color=MUTED, align="center")
    y -= 5 * mm

    legend(c, y)
    y -= 5.6 * mm

    # chart A: N400 learning signal (hero)
    y = section(c, y, "Brain learning signal", "N400 priming effect, µV ≈ · bigger = more learning")
    vals = {"ink": 1.26, "dig": 1.36, "key": 0.46}
    ch = 20 * mm
    base = y - 4 * mm - ch
    ymax = 2.25
    axis_w = 6 * mm
    for t in (0, 0.5, 1.0, 1.5, 2.0):
        ty = base + ch * t / ymax
        stroke(c, GRID if t else MUTED, 0.3 if t else 0.45)
        c.line(X0 + axis_w, ty, X1, ty)
        text(c, X0 + axis_w - 1 * mm, ty - 1.3, f"{t:g}", size=4.2, color=MUTED, align="right")
    plot_w = X1 - X0 - axis_w
    slot = plot_w / 3
    bw = slot * 0.56
    xs = {}
    for i, k in enumerate(ORDER):
        bx = X0 + axis_w + slot * i + (slot - bw) / 2
        xs[k] = bx + bw / 2
        bh = ch * vals[k] / ymax
        bar(c, bx, base, bw, bh, SERIES[k])
        text(c, bx + bw / 2, base + bh + 1.1 * mm, f"≈{vals[k]:.2f}", font="Sans-B", size=5.2, color=INK,
             align="center")
        text(c, bx + bw / 2, base - 3 * mm, NAMES[k], size=4.8, color=INK2, align="center")
    bracket(c, xs["dig"], xs["key"], base + ch * 1.82 / ymax, "p = .03")
    bracket(c, xs["ink"], xs["key"], base + ch * 2.12 / ymax, "p = .04")
    y = base - 7.4 * mm

    # chart B: repetitions (horizontal)
    y = section(c, y, "…but typing gave more practice", "writing repetitions per word")
    reps = {"ink": 9.24, "dig": 9.10, "key": 11.33}
    label_w = 14 * mm
    vmax = 12.0
    rw = X1 - X0 - label_w - 8 * mm
    rh = 2.4 * mm
    yy = y - 1.6 * mm
    for k in ORDER:
        text(c, X0, yy - rh + 0.65 * mm, NAMES[k], size=4.8, color=INK2)
        hbar(c, X0 + label_w, yy - rh, rw * reps[k] / vmax, rh, SERIES[k])
        text(c, X0 + label_w + rw * reps[k] / vmax + 1.2 * mm, yy - rh + 0.65 * mm, f"{reps[k]:.1f}",
             font="Sans-B", size=5, color=INK)
        yy -= rh + 0.7 * mm
    text(c, X1, yy - 2.2 * mm, "keyboard > both pens, p < .05", size=4.2, color=MUTED, align="right")
    text(c, X0, yy - 2.2 * mm, "More repetitions ≠ more learning.", font="Sans-B", size=5, color=INK)
    footer(c, 1)


# ---------- page 2 ----------

def page2(c):
    paper(c)
    y = H - 8 * mm
    text(c, X0, y, "RESEARCH SUMMARY", font="Sans-B", size=4.6, color=MUTED)
    text(c, X1, y, "Ihara et al., 2021", size=4.6, color=MUTED, align="right")
    y -= 5 * mm
    legend(c, y)
    y -= 5 * mm

    # chart C: familiarity
    y = section(c, y, "Familiarity with the digital pen matters", "N400 size, µV ≈")
    groups = [("Uses a digital pen daily", "n = 12", {"ink": 0.47, "dig": 1.47, "key": 0.0}),
              ("Doesn't use one", "n = 21", {"ink": 2.06, "dig": 1.24, "key": 0.94})]
    ch = 18 * mm
    base = y - 3.8 * mm - ch
    ymax = 2.4
    for t in (0, 1.0, 2.0):
        ty = base + ch * t / ymax
        stroke(c, GRID if t else MUTED, 0.3 if t else 0.45)
        c.line(X0 + 5 * mm, ty, X1, ty)
        text(c, X0 + 4 * mm, ty - 1.3, f"{t:g}", size=4.2, color=MUTED, align="right")
    gw = (X1 - X0 - 5 * mm) / 2
    for gi, (gname, n, vals) in enumerate(groups):
        gx = X0 + 5 * mm + gi * gw
        bw = gw * 0.22
        gap = 0.6 * mm
        start = gx + (gw - 3 * bw - 2 * gap) / 2
        best = max(vals, key=vals.get)
        for i, k in enumerate(ORDER):
            bx = start + i * (bw + gap)
            bh = ch * vals[k] / ymax
            bar(c, bx, base, bw, bh, SERIES[k])
            label = "≈0" if vals[k] == 0 else f"{vals[k]:.1f}"
            text(c, bx + bw / 2, base + bh + 1 * mm, label, font="Sans-B" if k == best else "Sans",
                 size=4.8, color=INK, align="center")
        text(c, gx + gw / 2, base - 3 * mm, gname, font="Sans-B", size=4.7, color=INK2, align="center")
        text(c, gx + gw / 2, base - 5.4 * mm, n, size=4.3, color=MUTED, align="center")
    y = base - 8.6 * mm
    y = wrap(c, X0, y, "Used to a digital pen: the digital pen was highest (vs keyboard p = .02). "
                       "Not used to it: the ink pen was highest (vs keyboard p = .057, only a trend).",
             X1 - X0, size=5, color=INK2)
    y -= 2 * mm

    # stat tiles: test scores and mood
    tw = (X1 - X0 - 1.6 * mm) / 2
    th = 17 * mm
    for i in range(2):
        stroke(c, GRID, 0.4)
        c.roundRect(X0 + i * (tw + 1.6 * mm), y - th, tw, th, 1 * mm, stroke=1, fill=0)
    # tile 1: words remembered
    tx = X0 + 1.8 * mm
    text(c, tx, y - 3.6 * mm, "Words remembered", font="Sans-B", size=5, color=INK)
    text(c, tx, y - 7.6 * mm, "9–12 of 20", font="Sans-B", size=8.2, color=INK)
    text(c, tx, y - 10.6 * mm, "for every tool (8.8–11.8)", size=4.6, color=INK2)
    text(c, tx, y - 13.4 * mm, "no difference (p = .19)", size=4.3, color=MUTED)
    # tile 2: mood (vigor) as mini bars
    tx = X0 + tw + 1.6 * mm + 1.8 * mm
    text(c, tx, y - 3.6 * mm, "Felt energetic (Vigor) ≈", font="Sans-B", size=5, color=INK)
    vig = {"ink": 49.4, "dig": 47.9, "key": 45.8}
    lo, hi = 44.0, 51.0          # dot plot: position, not length, so a non-zero axis is honest
    mw = tw - 12 * mm
    def vx(v):
        return tx + mw * (v - lo) / (hi - lo)
    my = y - 5.8 * mm
    for k in ORDER:
        stroke(c, GRID, 0.35)
        c.line(tx, my, tx + mw, my)
        fill(c, SERIES[k])
        c.circle(vx(vig[k]), my, 0.85 * mm, stroke=0, fill=1)
        text(c, tx + mw + 1.2 * mm, my - 1.5, f"{vig[k]:.1f}", size=4.6, color=INK,
             font="Sans-B" if k == "ink" else "Sans")
        my -= 2.3 * mm
    for t in (45, 50):
        stroke(c, MUTED, 0.3)
        c.line(vx(t), my + 1.5 * mm, vx(t), my + 2.1 * mm)
        text(c, vx(t), my - 0.1 * mm, str(t), size=3.8, color=MUTED, align="center")
    text(c, tx, y - th + 1.3 * mm, "T-score; ink > keyboard p = .036", size=4.1, color=MUTED)
    y -= th + 4 * mm

    # caveats
    y = section(c, y, "Read with care")
    caveats = [
        "Small groups (12 and 21 people).",
        "Measured right after learning only; no long-term test.",
        "The brain signal differed; test scores did not.",
        "The digital pen was a Wacom pen display, not an iPad.",
        "Co-funded by a pen-tablet maker (Wacom); two authors work there.",
    ]
    for s in caveats:
        text(c, X0, y - 0.2 * mm, "•", size=5, color=MUTED)
        y = wrap(c, X0 + 2.4 * mm, y, s, X1 - X0 - 2.4 * mm, size=4.9, color=INK2, leading=6.2) - 0.3 * mm
    y -= 1.6 * mm

    # takeaway (Mongolian)
    take = [
        "Шинэ үг цээжлэхдээ гараар бич, бүү шив.",
        "GoodNotes + Apple Pencil: дассан бол цаас шиг сайн; дасаагүй бол цаасаар бич.",
        "Олон давтах нь илүү сурсан гэсэн үг биш.",
    ]
    out = []  # wrapped lines per bullet
    for s in take:
        seg, line = [], ""
        for w_ in s.split():
            t = (line + " " + w_).strip()
            if pdfmetrics.stringWidth(t, "Sans", 5.2) <= X1 - X0 - 7 * mm:
                line = t
            else:
                seg.append(line); line = w_
        seg.append(line)
        out.append(seg)
    nlines = sum(len(s) for s in out)
    bh = 5.4 * mm + nlines * 2.75 * mm
    fill(c, tint(SERIES["dig"], 0.12))
    c.roundRect(X0, y - bh, X1 - X0, bh, 1.4 * mm, stroke=0, fill=1)
    text(c, X0 + 2.4 * mm, y - 3.4 * mm, "Миний хувьд", font="Sans-B", size=5.6, color=INK)
    ly = y - 6.4 * mm
    for seg in out:
        text(c, X0 + 2.4 * mm, ly, "•", size=5.2, color=INK)
        for line in seg:
            text(c, X0 + 4.6 * mm, ly, line, size=5.2, color=INK)
            ly -= 2.75 * mm
    y -= bh + 2.6 * mm

    # citation
    cite = ("Ihara AS, Nakajima K, Kake A, Ishimaru K, Osugi K, Naruse Y (2021). Advantage of handwriting "
            "over typing on learning words: evidence from an N400 event-related potential index. "
            "Front. Hum. Neurosci. 15:679191. doi:10.3389/fnhum.2021.679191 · CC BY 4.0. "
            "≈ = measured from the paper's figures.")
    wrap(c, X0, y, cite, X1 - X0, size=3.7, color=MUTED, leading=4.6)
    footer(c, 2)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H))
    c.setTitle("Handwriting vs typing: learning new words (Ihara et al., 2021)")
    c.setAuthor("Gereru")
    page1(c)
    c.showPage()
    page2(c)
    c.showPage()
    c.save()


if __name__ == "__main__":
    main()
