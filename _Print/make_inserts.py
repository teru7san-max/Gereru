"""Generate printable traveler's-notebook inserts (88 x 125 mm).

Outputs, next to this script:
  Inserts-88x125-preview.pdf   every page at real size, in reading order
  Reading-insert-A4.pdf        Унших insert, imposed for A4 duplex printing
  Practice-insert-A4.pdf       Хэрэгжүүлэх insert, imposed for A4 duplex printing

Run: python3 _Print/make_inserts.py   (needs reportlab, pypdf, DejaVu fonts)
"""

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", FONT_DIR + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-B", FONT_DIR + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif", FONT_DIR + "DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("Serif-B", FONT_DIR + "DejaVuSerif-Bold.ttf"))

W, H = 88 * mm, 125 * mm
PAGES = 32  # per insert; must be a multiple of 4
TOP, BOTTOM, INNER, OUTER = 7 * mm, 8 * mm, 7 * mm, 5.5 * mm
PITCH = 5.5 * mm  # ruled-line spacing

INK = (0.18, 0.18, 0.18)
SOFT = (0.45, 0.45, 0.45)
RULE = (0.78, 0.78, 0.78)
FAINT = (0.88, 0.88, 0.88)

SYMBOLS = [
    ("★", "insight", "шинээр ойлгосон"),
    ("♥", "resonates", "надад хүрсэн"),
    ("?", "question", "эргэлзээ, судлах"),
    ("✗", "disagree", "санал нийлэхгүй"),
    ("↻", "review", "эргэж унших"),
    ("●", "active", "бодитоор хэрэгжүүлсэн"),
]

TAGS = [
    ("Mind", "thinking · overthinking · rumination · intuition · mental-clarity · attention"),
    ("Emotions", "emotions · fear · joy · self-compassion · emotional-regulation"),
    ("Desire", "desire · happiness · peace · envy · attachment · freedom"),
    ("Self", "authenticity · self-love · self-awareness · values · identity"),
    ("Freedom", "suffering · letting-go · acceptance · non-resistance · presence · lightness"),
    ("Inner", "hope · inner-wisdom · meaning · growth · spirituality"),
    ("Action", "resistance · professionalism · consistency · creativity · courage · craft"),
    ("Love", "love · compassion · romantic-love · trust · intimacy · connection · relationships"),
]

BOOKS = [
    ("DBET", "Don't Believe Everything You Think", "J. Nguyen"),
    ("ALM", "The Almanack of Naval Ravikant", "E. Jorgenson"),
    ("WOA", "The War of Art", "S. Pressfield"),
]


# ---------- drawing helpers ----------

class Page:
    """One 88 x 125 mm page; knows which side the binding is on."""

    def __init__(self, c, number):
        self.c = c
        self.n = number
        right_hand = number % 2 == 1
        self.x0 = INNER if right_hand else OUTER
        self.x1 = W - (OUTER if right_hand else INNER)
        self.right_hand = right_hand

    @property
    def width(self):
        return self.x1 - self.x0

    def text(self, x, y, s, font="Sans", size=6, color=INK, align="left"):
        c = self.c
        c.setFillColorRGB(*color)
        c.setFont(font, size)
        if align == "center":
            c.drawCentredString(x, y, s)
        elif align == "right":
            c.drawRightString(x, y, s)
        else:
            c.drawString(x, y, s)

    def wrap(self, x, y, s, width, font="Sans", size=6, color=INK, leading=None):
        """Draw wrapped text; return the y below the last line."""
        leading = leading or size * 1.35
        words, line = s.split(), ""
        for w in words:
            trial = (line + " " + w).strip()
            if pdfmetrics.stringWidth(trial, font, size) <= width:
                line = trial
            else:
                self.text(x, y, line, font, size, color)
                y -= leading
                line = w
        if line:
            self.text(x, y, line, font, size, color)
            y -= leading
        return y

    def hline(self, y, x0=None, x1=None, color=RULE, width=0.35):
        c = self.c
        c.setStrokeColorRGB(*color)
        c.setLineWidth(width)
        c.line(self.x0 if x0 is None else x0, y, self.x1 if x1 is None else x1, y)

    def rules(self, y, count, pitch=PITCH):
        """Ruled lines starting at y (first line at y), going down."""
        for i in range(count):
            self.hline(y - i * pitch)
        return y - (count - 1) * pitch

    def field(self, x, y, label, length, size=5.2):
        """Small label followed by an underline to write on."""
        self.text(x, y, label, size=size, color=SOFT)
        lx = x + pdfmetrics.stringWidth(label, "Sans", size) + 1 * mm
        self.hline(y - 0.8 * mm, lx, lx + length, color=RULE)
        return lx + length

    def folio(self):
        x = self.x1 if self.right_hand else self.x0
        self.text(x, 4 * mm, str(self.n), size=5, color=SOFT,
                  align="right" if self.right_hand else "left")

    def heading(self, s, y=None):
        y = H - TOP - 3 * mm if y is None else y
        self.text(self.x0, y, s, font="Serif-B", size=9)
        self.hline(y - 2 * mm, color=INK, width=0.5)
        return y - 7 * mm


def cover(p, title, subtitle, lines):
    cx = (p.x0 + p.x1) / 2
    p.text(cx, H * 0.62, title, font="Serif-B", size=20, align="center")
    p.text(cx, H * 0.62 - 7 * mm, subtitle, font="Serif", size=8, color=SOFT, align="center")
    p.hline(H * 0.62 - 11 * mm, cx - 10 * mm, cx + 10 * mm, color=INK, width=0.5)
    y = H * 0.30
    for label in lines:
        p.field(p.x0 + 6 * mm, y, label, p.width - 12 * mm - pdfmetrics.stringWidth(label, "Sans", 5.2) - 1 * mm)
        y -= 7 * mm
    p.text(cx, 9 * mm, "Gereru", font="Serif", size=6, color=SOFT, align="center")


def back_cover(p):
    cx = W / 2
    p.text(cx, 12 * mm, "Read → Capture → Understand → Connect", size=4.6, color=SOFT, align="center")
    p.text(cx, 9 * mm, "Question → Reflect → Apply → Review", size=4.6, color=SOFT, align="center")


def symbol_row(p, y, x_right, size=6.4, gap=3.6 * mm):
    x = x_right
    for sym, _, _ in reversed(SYMBOLS):
        p.text(x, y, sym, size=size, color=(0.6, 0.6, 0.6), align="right")
        x -= gap


# ---------- Reading insert (Унших) ----------

def reading_entry(p, top):
    """One capture block. Returns its bottom y."""
    y = top
    x = p.x0
    x = p.field(x, y, "Огноо", 11 * mm) + 2 * mm
    x = p.field(x, y, "Ном", 18 * mm) + 2 * mm
    p.field(x, y, "х.", p.x1 - x - pdfmetrics.stringWidth("х.", "Sans", 5.2) - 1 * mm)
    y -= 6.2 * mm
    p.text(p.x0, y + 1.2 * mm, "“", font="Serif-B", size=9, color=RULE)
    y = p.rules(y, 5) - PITCH
    p.text(p.x0, y + 1.0 * mm, "→", size=6, color=SOFT)
    y = p.rules(y, 2) - PITCH
    p.text(p.x0, y + 0.6 * mm, "#", font="Sans-B", size=6.5, color=SOFT)
    p.hline(y - 0.2 * mm, p.x0 + 3 * mm, p.x0 + 30 * mm)
    symbol_row(p, y + 0.4 * mm, p.x1)
    return y


def reading_key(p):
    y = p.heading("Хэрхэн бичих вэ")
    y = p.wrap(p.x0, y, "Энд гол хэллэг, хуудасны дугаар, өөрийн нэг мөр бодлоо бич. "
               "Бүтэн ишлэл Obsidian-д хадгалагдана.", p.width, size=5.6)
    y -= 2 * mm
    p.text(p.x0, y, "Жишээ", font="Sans-B", size=5.6)
    y -= 4 * mm
    ex = [("12.10   DBET   х. __", INK), ("“pain is unavoidable,", INK), (" suffering is optional”", INK),
          ("→ уй гашуу аль сум нь вэ?", INK), ("#suffering                         ?", INK)]
    p.c.setFillColorRGB(0.965, 0.965, 0.965)
    p.c.rect(p.x0, y - 4 * 4.2 * mm - 2.2 * mm, p.width, 5 * 4.2 * mm + 1.6 * mm, stroke=0, fill=1)
    for s, col in ex:
        p.text(p.x0 + 2 * mm, y - 0.6 * mm, s, size=5.6, color=col)
        y -= 4.2 * mm
    y -= 4 * mm
    p.text(p.x0, y, "Тэмдэг: тохирохыг нь дугуйл", font="Sans-B", size=5.6)
    y -= 4.6 * mm
    for sym, tag, mn in SYMBOLS:
        p.text(p.x0 + 1 * mm, y, sym, size=7)
        p.text(p.x0 + 6 * mm, y, tag, font="Sans-B", size=5.6)
        p.text(p.x0 + 22 * mm, y, mn, size=5.6, color=SOFT)
        y -= 4.4 * mm
    y -= 1.5 * mm
    y = p.wrap(p.x0, y, "#: зөвхөн нэг гол tag. Хоёр өөр санаа байвал хоёр тусдаа бич.",
               p.width, size=5.3, color=SOFT)
    p.wrap(p.x0, y, "●: зөвхөн амьдрал дээр бодитоор хэрэгжүүлсэн үед. "
           "Таалагдсан, ойлгосон нь ● биш.", p.width, size=5.3, color=SOFT)


def reading_books(p):
    y = p.heading("Номын товчлол")
    col = 13 * mm
    p.text(p.x0, y, "Товч", font="Sans-B", size=5.4, color=SOFT)
    p.text(p.x0 + col, y, "Ном · Зохиолч", font="Sans-B", size=5.4, color=SOFT)
    y -= 2 * mm
    rows = 15
    for i in range(rows):
        p.hline(y)
        y -= 1 * mm
        if i < len(BOOKS):
            abbr, title, author = BOOKS[i]
            p.text(p.x0 + 0.5 * mm, y - 2.8 * mm, abbr, font="Sans-B", size=5.6)
            p.text(p.x0 + col, y - 2.8 * mm, title, size=5.1)
            p.text(p.x1, y - 2.8 * mm, author, size=4.6, color=SOFT, align="right")
        y -= PITCH
    p.hline(y)
    c = p.c
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(0.35)
    c.line(p.x0 + col - 1.5 * mm, y, p.x0 + col - 1.5 * mm, y + rows * (PITCH + 1 * mm))


def weekly_transfer(p):
    y = p.heading("Obsidian руу шилжүүлэх")
    y = p.wrap(p.x0, y, "Долоо хоногт нэг удаа: зураг эсвэл текстээр илгээж, note болгоно.",
               p.width, size=5.4, color=SOFT)
    y -= 2.5 * mm
    p.text(p.x0, y, "Огноо", font="Sans-B", size=5.2, color=SOFT)
    p.text(p.x0 + 18 * mm, y, "Хуудас", font="Sans-B", size=5.2, color=SOFT)
    p.text(p.x1, y, "✓", font="Sans-B", size=5.6, color=SOFT, align="right")
    y -= 3 * mm
    while y > BOTTOM + 3 * mm:
        p.text(p.x0 + 14 * mm, y - 3.6 * mm, "", size=5)
        p.text(p.x0 + 18 * mm + 12 * mm, y - 3.6 * mm, "–", size=5.5, color=RULE)
        p.c.setStrokeColorRGB(*RULE)
        p.c.rect(p.x1 - 2.6 * mm, y - 4.2 * mm, 2.6 * mm, 2.6 * mm, stroke=1, fill=0)
        y -= PITCH
        p.hline(y)


def tag_list(p):
    y = p.heading("Tag-ууд")
    for group, tags in TAGS:
        p.text(p.x0, y, group, font="Sans-B", size=5.6)
        y = p.wrap(p.x0 + 2 * mm, y - 3.2 * mm, tags, p.width - 2 * mm, size=5.1, color=SOFT)
        y -= 1.6 * mm
    y -= 1 * mm
    p.wrap(p.x0, y, "Шинэ tag зөвхөн үнэхээр өөр санаа гарч ирэхэд. Эхлээд байгаа tag-аа ашигла.",
           p.width, size=5.1, color=SOFT)


def build_reading(c):
    for n in range(1, PAGES + 1):
        p = Page(c, n)
        if n == 1:
            cover(p, "Унших", "Reading log", ["Дугаар", "Эхэлсэн", "Дууссан"])
        elif n == 2:
            reading_key(p)
        elif n == 3:
            reading_books(p)
        elif n == PAGES - 2:
            weekly_transfer(p)
        elif n == PAGES - 1:
            tag_list(p)
        elif n == PAGES:
            back_cover(p)
        else:
            top = H - TOP - 2 * mm
            bottom = reading_entry(p, top)
            p.hline(bottom - 2.6 * mm, color=FAINT, width=0.6)
            reading_entry(p, bottom - 6.4 * mm)
        if 1 < n < PAGES:
            p.folio()
        c.showPage()


# ---------- Practice insert (Хэрэгжүүлэх) ----------

PRACTICE_SECTIONS = [
    "Нөхцөл байдал: юу болсон",
    "Ердийн хариу үйлдэл: хуучин хэв маяг",
    "Юуг өөрөөр хийсэн",
    "Юу анзаарсан · дараагийн удаа",
]


def practice_entry(p):
    y = H - TOP - 2 * mm
    x = p.field(p.x0, y, "Огноо", 13 * mm) + 2 * mm
    p.text(x, y, "#", font="Sans-B", size=6.5, color=SOFT)
    p.hline(y - 0.8 * mm, x + 3 * mm, p.x1)
    y -= 5.4 * mm
    p.field(p.x0, y, "Санаа / note", p.width - pdfmetrics.stringWidth("Санаа / note", "Sans", 5.2) - 1 * mm)
    y -= 6.2 * mm
    for label in PRACTICE_SECTIONS:
        p.text(p.x0, y, label, font="Sans-B", size=5.3, color=SOFT)
        y -= 5.6 * mm
        y = p.rules(y, 3) - 4.6 * mm
    y += 0.6 * mm
    p.text(p.x0, y, "Болсон уу?", font="Sans-B", size=5.3, color=SOFT)
    x = p.x0 + 15 * mm
    for label in ["тийм", "хэсэгчлэн", "үгүй"]:
        p.c.setStrokeColorRGB(*SOFT)
        p.c.setLineWidth(0.4)
        p.c.rect(x, y - 0.4 * mm, 2.4 * mm, 2.4 * mm, stroke=1, fill=0)
        p.text(x + 3.4 * mm, y, label, size=5.3, color=SOFT)
        x += 3.4 * mm + pdfmetrics.stringWidth(label, "Sans", 5.3) + 3.2 * mm


def practice_guide(p):
    y = p.heading("Энэ дэвтэр юунд вэ")
    y = p.wrap(p.x0, y, "Санааг ойлгох, амьдрах хоёр өөр. Энд бодит нөхцөлд туршсан зүйлээ бичнэ. "
               "Эдгээр хуудас бол ● active-ийн нотолгоо.", p.width, size=5.6)
    y -= 3 * mm
    steps = [
        ("★", "Уншаад шинээр ойлгосон", "Унших дэвтэрт"),
        ("1", "Бодит нөхцөлд нэг удаа туршсан", "Энд бич"),
        ("2", "Хэд хэдэн удаа давтаж, хэв маяг өөрчлөгдөж эхэлсэн", "→ ●"),
    ]
    for sym, what, where in steps:
        p.text(p.x0 + 1 * mm, y, sym, font="Sans-B", size=6.5)
        yy = p.wrap(p.x0 + 6 * mm, y, what, p.width - 20 * mm, size=5.5)
        p.text(p.x1, y, where, font="Sans-B", size=5.3, color=SOFT, align="right")
        y = min(yy, y - 4 * mm) - 1.5 * mm
    y -= 2 * mm
    p.text(p.x0, y, "Жишээ: хоёр дахь сум", font="Sans-B", size=5.6)
    y -= 4.4 * mm
    example = [
        ("Нөхцөл", "Шалгалтын дүн муу гарсан (1-р сум)."),
        ("Ердийн", "“Би чадахгүй” гэж хэдэн өдөр бодох (2-р сум)."),
        ("Өөрөөр", "1-р сумаа нэрлээд, 2-р сумаа нэмж байгаагаа анзаарсан."),
        ("Анзаарсан", "Бодол намжихад дараагийн алхам тодорхой болсон."),
    ]
    for k, v in example:
        p.text(p.x0, y, k, font="Sans-B", size=5.1, color=SOFT)
        y = p.wrap(p.x0 + 13 * mm, y, v, p.width - 13 * mm, size=5.1) - 1.2 * mm
    y -= 2 * mm
    p.wrap(p.x0, y, "Нэг удаа туршсан нь ● биш. Шударга бич: “үгүй” гэдэг хариу ч мэдээлэл.",
           p.width, size=5.2, color=SOFT)


def testing_list(p):
    y = p.heading("Туршиж буй санаанууд")
    p.text(p.x0, y, "Санаа / note", font="Sans-B", size=5.2, color=SOFT)
    p.text(p.x1 - 9 * mm, y, "Эхэлсэн", font="Sans-B", size=5.2, color=SOFT, align="right")
    p.text(p.x1, y, "●", size=6, color=SOFT, align="right")
    y -= 2 * mm
    while y > BOTTOM + PITCH:
        y -= PITCH
        p.hline(y)
        p.c.setStrokeColorRGB(*RULE)
        p.c.circle(p.x1 - 1.3 * mm, y + 2 * mm, 1.2 * mm, stroke=1, fill=0)


def monthly_review(p):
    y = p.heading("Сарын эргэн харах")
    prompts = ["Сар", "Юу ● болсон бэ?", "Юу тогтсонгүй, яагаад?"]
    for _ in range(2):
        x = p.field(p.x0, y, prompts[0], 20 * mm)
        y -= 6 * mm
        for label in prompts[1:]:
            p.text(p.x0, y, label, font="Sans-B", size=5.3, color=SOFT)
            y -= 5.4 * mm
            y = p.rules(y, 3) - 5 * mm
        y -= 1.5 * mm


def build_practice(c):
    for n in range(1, PAGES + 1):
        p = Page(c, n)
        if n == 1:
            cover(p, "Хэрэгжүүлэх", "Practice log", ["Дугаар", "Эхэлсэн", "Дууссан"])
        elif n == 2:
            practice_guide(p)
        elif n == 3:
            testing_list(p)
        elif n == PAGES - 1:
            monthly_review(p)
        elif n == PAGES:
            back_cover(p)
        else:
            practice_entry(p)
        if 1 < n < PAGES:
            p.folio()
        c.showPage()


# ---------- output ----------

def render(builder, title):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setTitle(title)
    c.setAuthor("Gereru")
    builder(c)
    c.save()
    buf.seek(0)
    return PdfReader(buf)


A4W, A4H = 210 * mm, 297 * mm
SPREAD_W, SPREAD_H = 2 * W, H
SX = (A4W - SPREAD_W) / 2
SLOT_Y = [A4H / 2, A4H / 2 - SPREAD_H]  # bottom edge of top and bottom spreads


def marks_overlay(labels):
    """Crop marks, fold marks and sheet labels for the front of one A4 sheet."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(A4W, A4H))
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.3)
    L, G = 5 * mm, 1.5 * mm
    xs = [SX, SX + SPREAD_W]
    ys = [SLOT_Y[1], SLOT_Y[0], SLOT_Y[0] + SPREAD_H]
    for x in xs:
        for y in ys:
            c.line(x - L - G if x == SX else x + G, y, x - G if x == SX else x + L + G, y)
        c.line(x, ys[-1] + G, x, ys[-1] + G + L)
        c.line(x, ys[0] - G, x, ys[0] - G - L)
    fx = SX + W  # fold line
    c.setDash(1, 1)
    c.line(fx, ys[-1] + G, fx, ys[-1] + G + L)
    c.line(fx, ys[0] - G, fx, ys[0] - G - L)
    c.setDash()
    c.setFont("Sans", 6)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    for slot, label in enumerate(labels):
        y = SLOT_Y[slot] + SPREAD_H / 2
        c.saveState()
        c.translate(A4W - SX / 2 + 1.5 * mm, y)
        c.rotate(90)
        c.drawCentredString(0, 0, label)
        c.restoreState()
    c.setFont("Sans", 5.5)
    c.drawCentredString(A4W / 2, 6 * mm,
                        "100% (Actual size) · хоёр талд · урт ирмэгээр эргүүлэх (flip on long edge)")
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def impose(reader, name, out_path):
    n = len(reader.pages)
    sheets = []  # each folded sheet: (front[left,right], back[left,right]) as 0-based page indexes
    for k in range(n // 4):
        sheets.append(((n - 1 - 2 * k, 2 * k), (2 * k + 1, n - 2 - 2 * k)))
    writer = PdfWriter()
    total = len(sheets)
    for a in range(0, total, 2):
        pair = sheets[a:a + 2]
        for side in (0, 1):
            page = writer.add_blank_page(A4W, A4H)
            for slot, sheet in enumerate(pair):
                left, right = sheet[side]
                for idx, dx in ((left, 0), (right, W)):
                    page.merge_transformed_page(
                        reader.pages[idx], Transformation().translate(SX + dx, SLOT_Y[slot]))
            if side == 0:
                labels = [f"{name} · {a + s + 1}/{total} ({'гадна' if a + s == 0 else 'дотогш'})"
                          for s in range(len(pair))]
                page.merge_page(marks_overlay(labels))
    writer.add_metadata({"/Title": f"{name} insert · A4 duplex", "/Author": "Gereru"})
    with open(out_path, "wb") as f:
        writer.write(f)


def main():
    reading = render(build_reading, "Унших · Reading log")
    practice = render(build_practice, "Хэрэгжүүлэх · Practice log")

    preview = PdfWriter()
    for r in (reading, practice):
        for pg in r.pages:
            preview.add_page(pg)
    preview.add_metadata({"/Title": "Traveler inserts · 88×125 mm", "/Author": "Gereru"})
    with open(OUT / "Inserts-88x125-preview.pdf", "wb") as f:
        preview.write(f)

    impose(reading, "Унших", OUT / "Reading-insert-A4.pdf")
    impose(practice, "Хэрэгжүүлэх", OUT / "Practice-insert-A4.pdf")


if __name__ == "__main__":
    main()
