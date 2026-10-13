"""Draw a filled-in example of the three inserts side by side (Example-filled.pdf).

The entries are examples built from notes in this vault, not a real practice record.
Run: python3 _Print/make_example.py
"""

import math
import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_inserts as mi  # noqa: E402
from make_stickers import FAMILY_STYLE, GLUE, FLAG, TAB_W, flag_face, hexrgb, tint  # noqa: E402

OUT = Path(__file__).resolve().parent / "Example-filled.pdf"
W, H, P = mi.W, mi.H, mi.PITCH
INK = (0.13, 0.27, 0.62)
GAP, MX, TITLE, TABS, LABELS = 9 * mm, 10 * mm, 14 * mm, 12 * mm, 11 * mm
CW, CH = 2 * MX + 3 * W + 2 * GAP, LABELS + H + TABS + TITLE


def hw(c, x, y, text, size=7.6, color=INK, font="Serif"):
    """Handwriting stand-in: slanted serif in pen-blue."""
    c.saveState()
    c.translate(x, y)
    c.skew(0, 11)
    c.setFillColorRGB(*color)
    c.setFont(font, size)
    c.drawString(0, 0, text)
    c.restoreState()


def ring(c, cx, cy, r=1.8 * mm):
    c.saveState()
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(0.6)
    c.ellipse(cx - r * 1.05, cy - r * 0.9, cx + r * 0.95, cy + r * 1.0, stroke=1, fill=0)
    c.restoreState()


def symbol_x(p, tag):
    """Centre x of a response symbol in symbol_row (drawn right-aligned from x1)."""
    order = [s[1] for s in mi.SYMBOLS]
    i = len(order) - 1 - order.index(tag)
    sym = mi.SYMBOLS[order.index(tag)][0]
    right = p.x1 - i * 3.6 * mm
    return right - pdfmetrics.stringWidth(sym, "Sans", 6.4) / 2


def tag_line(c, p, y, icon, word):
    mi.draw_icon(c, icon, p.x0 + 4 * mm, y - 0.6 * mm, 3.4 * mm, color=INK, width=0.6)
    hw(c, p.x0 + 8.2 * mm, y + 0.3 * mm, word, size=7.4)


def field_x(label, x0):
    return x0 + pdfmetrics.stringWidth(label, "Sans", 5.2) + 1.6 * mm


def reading_page(c):
    p = mi.Page(c, 5)
    entries = [
        ("12.10", "DBET", "?", ["pain is unavoidable,", "suffering is optional", "(хоёр сум, Будда)"],
         "уй гашуу аль сум нь вэ?", "balloon", "suffering", "question"),
        ("13.10", "DBET", "?", ["words point TO the truth", "truth = a feeling,", "“feels like home”"],
         "танил уу, амар амгалан уу?", "helix", "inner-wisdom", "review"),
    ]
    top = H - mi.TOP - 2 * mm
    for date, book, page, quote, thought, icon, tag, resp in entries:
        bottom = mi.reading_entry(p, top)
        hy = top + 0.5 * mm
        x = field_x("Огноо", p.x0)
        hw(c, x + 0.5 * mm, hy, date)
        x = x + 11 * mm + 2 * mm
        hw(c, field_x("Ном", x) + 0.5 * mm, hy, book)
        x = field_x("Ном", x) + 18 * mm + 2 * mm
        hw(c, field_x("х.", x) + 1 * mm, hy, page)
        y1 = top - 6.2 * mm
        for i, line in enumerate(quote):
            hw(c, p.x0 + 2.2 * mm, y1 - i * P + 0.7 * mm, line)
        hw(c, p.x0 + 4 * mm, y1 - 5 * P + 0.7 * mm, thought)
        tag_line(c, p, bottom, icon, tag)
        ring(c, symbol_x(p, resp), bottom + 1.6 * mm)
        if top == H - mi.TOP - 2 * mm:
            p.hline(bottom - 2.6 * mm, color=mi.FAINT, width=0.6)
            top = bottom - 6.4 * mm
    p.folio()
    return p


def practice_page(c):
    p = mi.Page(c, 5)
    mi.practice_entry(p)
    y = H - mi.TOP - 2 * mm
    hw(c, field_x("Огноо", p.x0) + 0.5 * mm, y + 0.5 * mm, "15.10")
    hx = field_x("Огноо", p.x0) + 13 * mm + 2 * mm
    mi.draw_icon(c, "balloon", hx + 3.6 * mm, y - 0.8 * mm, 3.4 * mm, color=INK, width=0.6)
    hw(c, hx + 7.6 * mm, y + 0.5 * mm, "suffering")
    y -= 5.4 * mm
    hw(c, field_x("Санаа / note", p.x0) + 0.5 * mm, y + 0.5 * mm, "Pain = 1-р сум, suffering = 2-р сум")
    y -= 6.2 * mm
    answers = [
        ["Шалгалтын дүн муу гарсан.", "(1-р сум)"],
        ["“Би чадахгүй” гэж орой", "болтол бодсон. (2-р сум)"],
        ["1-р сумаа нэрлэсэн: “дүн муу”.", "2-р сумаа анзаарсан:", "“би чадахгүй” гэдэг бодол."],
        ["10 минутын дараа бодол намжсан.", "Дараагийн алхам: багштай уулзах."],
    ]
    for lines in answers:
        y -= 5.6 * mm
        for i, line in enumerate(lines):
            hw(c, p.x0 + 0.8 * mm, y - i * P + 0.7 * mm, line, size=7.2)
        y = y - 2 * P - 4.6 * mm
    y += 0.6 * mm
    x = p.x0 + 15 * mm
    for label in ["тийм", "хэсэгчлэн", "үгүй"]:
        if label == "хэсэгчлэн":
            hw(c, x + 0.2 * mm, y - 0.3 * mm, "✓", size=9, font="Sans-B")
        x += 3.4 * mm + pdfmetrics.stringWidth(label, "Sans", 5.3) + 3.2 * mm
    p.folio()
    return p


def thinking_page(c):
    p = mi.Page(c, 5)
    c.setFillColorRGB(0.66, 0.66, 0.66)
    step = 5 * mm
    yy = H - mi.TOP
    while yy > mi.BOTTOM:
        xx = p.x0
        while xx <= p.x1 + 0.1:
            c.circle(xx, yy, 0.32, stroke=0, fill=1)
            xx += step
        yy -= step
    hw(c, p.x0, H - mi.TOP - 4.5 * mm, "Spiral → Helix", size=10, font="Serif-B")
    # flat spiral
    cx, cy = p.x0 + 14 * mm, H - 38 * mm
    path = c.beginPath()
    for k in range(400):
        t = 3 * 2 * math.pi * k / 399
        r = 0.55 * mm * t
        x, y = cx + r * math.cos(t), cy + r * math.sin(t)
        path.moveTo(x, y) if k == 0 else path.lineTo(x, y)
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(0.7)
    c.drawPath(path, stroke=1, fill=0)
    mi.draw_icon(c, "helix", p.x1 - 26 * mm, H - 50 * mm, 22 * mm, color=INK, width=0.8)
    hw(c, cx + 12 * mm, cy + 1 * mm, "→", size=12, font="Sans")
    hw(c, p.x0, H - 58 * mm, "rumination", size=7)
    hw(c, p.x0, H - 61.5 * mm, "ижил өндөрт", size=6.6)
    hw(c, p.x1 - 26 * mm, H - 58 * mm, "reflection", size=7)
    hw(c, p.x1 - 26 * mm, H - 61.5 * mm, "дээшилдэг", size=6.6)
    lines = [
        ("Давталт ≠ зогсонги.", 7.6),
        ("Асуулт: өнгөрсөн удаагаас", 7.4),
        ("юу өөр байна вэ?", 7.4),
        ("", 4),
        ("→ [[We cling to familiar suffering]]", 6.4),
        ("→ [[Pain is the first arrow…]]", 6.4),
        ("", 4),
        ("1 (oneness) = ?", 7.6),
    ]
    y = H - 72 * mm
    for text, size in lines:
        if text:
            hw(c, p.x0, y, text, size=size)
        y -= size * 0.55 * mm
    p.folio()
    return p


def tab_on_page(c, px, family, icon, label):
    color = hexrgb(FAMILY_STYLE[family][0])
    ink = FAMILY_STYLE[family][1]
    c.setFillColorRGB(*tint(color, 0.28))
    c.rect(px, H - GLUE, TAB_W, GLUE, stroke=0, fill=1)
    c.setFillColorRGB(*color)
    c.rect(px, H, TAB_W, FLAG, stroke=0, fill=1)
    flag_face(c, px, H, icon, label, ink)


def main():
    c = canvas.Canvas(str(OUT), pagesize=(CW, CH))
    c.setTitle("Жишээ: дүүргэсэн хуудас")
    c.setAuthor("Gereru")
    c.setFillColorRGB(*mi.INK)
    c.setFont("Serif-B", 12)
    c.drawString(MX, CH - 9 * mm, "Жишээ: дүүргэсэн хуудас")
    c.setFont("Sans", 6.5)
    c.setFillColorRGB(*mi.SOFT)
    c.drawString(MX + pdfmetrics.stringWidth("Жишээ: дүүргэсэн хуудас", "Serif-B", 12) + 5 * mm, CH - 9 * mm,
                 "Танай vault-ын note-уудаас бүтээсэн жишээ. Хэрэгжүүлэх хуудас бол бодит бичлэг биш.")
    pages = [
        (reading_page, "1 · Унших (урд)", ("Freedom & acceptance", "balloon", "suffering")),
        (practice_page, "2 · Хэрэгжүүлэх (дунд)", None),
        (thinking_page, "3 · Сэтгэх, dot grid (ард, дараа нь)", ("Hope & inner", "helix", "growth")),
    ]
    for i, (fn, label, tab) in enumerate(pages):
        ox = MX + i * (W + GAP)
        c.saveState()
        c.translate(ox, LABELS)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(0.8 * mm, -0.8 * mm, W, H, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.4)
        c.rect(0, 0, W, H, stroke=1, fill=1)
        fn(c)
        if tab:
            tab_on_page(c, W - TAB_W - 10 * mm, *tab)
        c.restoreState()
        c.setFillColorRGB(*mi.INK)
        c.setFont("Sans-B", 7.5)
        c.drawCentredString(ox + W / 2, 4.5 * mm, label)
    c.showPage()
    c.save()


if __name__ == "__main__":
    main()
