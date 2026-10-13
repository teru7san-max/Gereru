"""Health notes in the user's own notebook style: 88 x 125 mm pages, blank cream paper,
all-caps fineliner handwriting (black, red, green), boxed titles, arrows, braces and
small doodles. Content: supplements, rice vs potatoes, meal plates, sleep.

Grey pencil notes are Claude's additions (fact checks), not part of the source.
Output: _Print/GoodNotes/notes/Health · handwritten.pdf (+ PNG previews with --png)
Run: python3 _Print/make_paper.py && python3 _Print/make_health_notes.py
"""

import math
import subprocess
import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from handwriting import BLACK, GREEN, PENCIL, RED, Hand
from make_paper import paper_path

ROOT = Path(__file__).resolve().parent / "GoodNotes"
OUT = ROOT / "notes" / "Health · handwritten.pdf"
W, H = 88, 125
X0, X1 = 9.0, 80.0
TW = X1 - X0
B, S, T = 1.9, 1.55, 2.3          # body, small and title cap heights (mm)


# ---------- page furniture ----------

def header(h, num, title, side=None):
    y = H - 12
    h.ellipse(X0 + 2.6, y + 1.0, 2.8, 2.4, BLACK, 0.24)
    h.text(X0 + 0.6, y, f"#{num}", 1.8)
    x = h.text(X0 + 8.4, y, title, T, RED, 0.26)
    h.rect(X0 + 7.0, y - 1.4, x + 1.2, y + T + 1.3, RED, 0.24)
    if side:
        yy = y + 1.6
        for line in side:
            h.text(x + 3.5, yy, line, 1.35, BLACK, 0.2)
            yy -= 2.6
    return y - 8.5


def pencil(h, x, y, lines, size=1.3):
    """Claude's fact-check note, in pencil grey."""
    h.text(x - 2.4, y, "?", size * 1.4, PENCIL, 0.2)
    for ln in lines:
        h.text(x, y, ln, size, PENCIL, 0.18)
        y -= size * 1.95
    return y


def person(h, x, y):
    """The little person mark used before a quoted author."""
    h.ellipse(x, y + 1.6, 0.45, 0.45, BLACK, 0.3, overlap=0.6)
    c = h.c
    c.setFillColorRGB(*BLACK)
    p = c.beginPath()
    p.moveTo((x - 0.75) * mm, y * mm)
    p.curveTo((x - 0.75) * mm, (y + 1.1) * mm, (x + 0.75) * mm, (y + 1.1) * mm, (x + 0.75) * mm, y * mm)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def strike_then(h, x, y, crossed, rest, width, size=B):
    """'badly on purpose': a crossed-out ideal, then the easy version."""
    x2 = h.text(x, y, crossed, size, BLACK)
    h.line(x - 0.4, y + size * 0.45, x2 + 0.3, y + size * 0.55, RED, 0.3)
    return h.para(x, y - size * 2.2, rest, width, size)


# ---------- doodles ----------

def sun(h, cx, cy, r=2.2):
    h.ellipse(cx, cy, r, r, BLACK, 0.26)
    for k in range(8):
        a = k * math.pi / 4 + h.rng.gauss(0, 0.08)
        h.line(cx + 1.5 * r * math.cos(a), cy + 1.5 * r * math.sin(a),
               cx + 2.1 * r * math.cos(a), cy + 2.1 * r * math.sin(a), BLACK, 0.26, amp=0.03)


def capsule(h, cx, cy, length=7, width=2.8, ang=35):
    a = math.radians(ang)
    r = width / 2
    half = length / 2 - r
    pts = []
    for k in range(13):
        t = -math.pi / 2 + math.pi * k / 12
        pts.append((half + r * math.cos(t), r * math.sin(t)))
    for k in range(13):
        t = math.pi / 2 + math.pi * k / 12
        pts.append((-half + r * math.cos(t), r * math.sin(t)))
    rot = lambda p: (cx + p[0] * math.cos(a) - p[1] * math.sin(a), cy + p[0] * math.sin(a) + p[1] * math.cos(a))
    h.poly([rot(p) for p in pts], BLACK, 0.26, closed=True)
    h.line(*rot((0, -r)), *rot((0, r)), BLACK, 0.26, amp=0.02)
    for k in range(4):
        x = -half - r * 0.5 + k * 0.9
        h.line(*rot((x, -r * 0.7)), *rot((x + 0.5, r * 0.7)), RED, 0.18, amp=0.02)


def drop(h, cx, cy, height=6.5):
    r = height * 0.33
    bc = cy - height / 2 + r
    pts = [(cx, cy + height / 2)]
    for k in range(25):
        t = math.radians(30 + 300 * k / 24)
        pts.append((cx + r * math.cos(t - math.pi / 2 + math.pi), bc + r * math.sin(t - math.pi / 2 + math.pi)))
    pts = [(cx, cy + height / 2)] + [(cx + r * math.sin(math.radians(a)), bc - r * math.cos(math.radians(a)))
                                     for a in range(150, -151, -15)] + [(cx, cy + height / 2)]
    h.poly(pts, BLACK, 0.26)
    h.poly([(cx - r * 0.55, bc), (cx - r * 0.45, bc - r * 0.45), (cx - r * 0.1, bc - r * 0.62)], GREEN, 0.22)


def moon(h, cx, cy, r=2.8):
    """Crescent opening to the right, with a small green leaf."""
    a0, a1 = math.radians(55), math.radians(305)
    outer = [(cx + r * math.cos(a0 + (a1 - a0) * k / 24), cy + r * math.sin(a0 + (a1 - a0) * k / 24)) for k in range(25)]
    p1, p2 = outer[0], outer[-1]
    m = (cx + r * 0.25, cy)                      # inner curve passes through here
    ctl = (2 * m[0] - (p1[0] + p2[0]) / 2, 2 * m[1] - (p1[1] + p2[1]) / 2)
    inner = [((1 - t) ** 2 * p2[0] + 2 * (1 - t) * t * ctl[0] + t ** 2 * p1[0],
              (1 - t) ** 2 * p2[1] + 2 * (1 - t) * t * ctl[1] + t ** 2 * p1[1]) for t in [k / 16 for k in range(17)]]
    h.poly(outer + inner[1:], BLACK, 0.26)
    lx, ly = cx + r * 0.55, cy - r * 0.95
    h.poly([(lx, ly), (lx + 1.2, ly + 1.0), (lx + 2.8, ly + 0.6), (lx + 1.6, ly - 0.4), (lx, ly)], GREEN, 0.24)
    h.line(lx, ly, lx + 2.2, ly + 0.5, GREEN, 0.18, amp=0.02)


def bowl(h, cx, cy, w=10, fill=True):
    rx, ry = w / 2, w * 0.1
    h.ellipse(cx, cy, rx, ry, BLACK, 0.26)
    body = [(cx + rx * math.cos(math.radians(a)), cy + w * 0.42 * math.sin(math.radians(a))) for a in range(180, 361, 12)]
    h.poly(body, BLACK, 0.26)
    h.line(cx - w * 0.15, cy - w * 0.47, cx + w * 0.15, cy - w * 0.47, BLACK, 0.26, amp=0.02)
    if fill:
        for k in range(5):
            gx = cx - rx * 0.6 + k * rx * 0.3 + h.rng.uniform(-0.3, 0.3)
            gy = cy + ry * 0.6 + h.rng.uniform(0, 0.8)
            h.ellipse(gx, gy, 0.75, 0.45, BLACK, 0.22)


def potato(h, cx, cy, rx=4.0, ry=3.0):
    h.ellipse(cx, cy, rx, ry, BLACK, 0.26)
    for dx, dy in ((-1.4, 0.8), (1.0, -0.5), (0.3, 1.3)):
        h.line(cx + dx, cy + dy, cx + dx + 0.5, cy + dy + 0.1, BLACK, 0.26, amp=0.02)


def plate(h, cx, cy, w=11, blobs=((RED, -0.18, 0.05), (GREEN, 0.18, 0.1), (BLACK, 0.0, -0.15))):
    h.ellipse(cx, cy, w / 2, w * 0.28, BLACK, 0.26)
    h.ellipse(cx, cy, w * 0.36, w * 0.19, BLACK, 0.18)
    for col, dx, dy in blobs:
        bx, by = cx + dx * w, cy + dy * w
        pts = [(bx + 1.2 * math.cos(a) * h.rng.uniform(0.8, 1.15), by + 0.8 * math.sin(a) * h.rng.uniform(0.8, 1.15))
               for a in [k * math.pi / 4 for k in range(8)]]
        h.poly(pts, col, 0.24, closed=True)
        if col is not BLACK:
            h.hatch(bx - 0.9, by - 0.5, bx + 0.9, by + 0.5, col, 0.15, gap=0.5)


def figure_jump(h, x, y):
    # crouched
    h.ellipse(x, y + 5.2, 0.8, 0.8, BLACK, 0.24)
    h.poly([(x, y + 4.4), (x - 0.5, y + 2.6)], BLACK, 0.24)
    h.poly([(x - 0.5, y + 2.6), (x + 1.0, y + 1.6), (x + 0.3, y)], BLACK, 0.24)
    h.poly([(x - 0.5, y + 2.6), (x - 1.5, y + 1.4), (x - 1.0, y)], BLACK, 0.24)
    h.poly([(x - 0.1, y + 3.9), (x + 1.3, y + 3.0)], BLACK, 0.24)
    h.arrow(x + 2.4, y + 1.0, x + 3.6, y + 5.0, RED, 0.24, head=0.9)
    # jumping
    jx, jy = x + 6.0, y + 1.5
    h.ellipse(jx, jy + 5.6, 0.8, 0.8, BLACK, 0.24)
    h.poly([(jx, jy + 4.8), (jx, jy + 2.4)], BLACK, 0.24)
    h.poly([(jx - 1.1, jy + 6.6), (jx, jy + 4.4), (jx + 1.1, jy + 6.6)], BLACK, 0.24)
    h.poly([(jx - 0.9, jy), (jx, jy + 2.4), (jx + 0.9, jy)], BLACK, 0.24)


def figure_climber(h, x, y):
    h.ellipse(x + 7.0, y + 3.2, 0.8, 0.8, BLACK, 0.24)
    h.poly([(x + 6.3, y + 2.8), (x + 2.0, y + 1.7)], BLACK, 0.24)       # body
    h.poly([(x + 6.0, y + 2.6), (x + 6.2, y)], BLACK, 0.24)             # arm
    h.poly([(x + 2.0, y + 1.7), (x, y)], BLACK, 0.24)                   # back leg
    h.poly([(x + 2.0, y + 1.7), (x + 4.2, y + 1.4), (x + 3.6, y)], BLACK, 0.24)  # knee in
    h.line(x - 1.0, y - 0.3, x + 8.5, y - 0.3, BLACK, 0.2)
    for k in range(3):
        h.line(x - 2.6, y + 1.0 + k * 0.8, x - 1.4, y + 1.0 + k * 0.8, RED, 0.2, amp=0.02)


# ---------- pages ----------

def p_supplements_1(h):
    y = header(h, 1, "SUPPLEMENTS", ["NO GIMMICKS,", "JUST FUNDAMENTALS."])
    y -= 2
    sun(h, X0 + 3.5, y - 0.5)
    h.text(X0 + 9.5, y - 1.5, "VITAMIN D", 2.4, GREEN, 0.28)
    y -= 7.5
    x = h.text(X0 + 10.5, y, "5,000 IU · 1X A DAY · MORNING/AFTERNOON", S)
    h.rect(X0 + 9.3, y - 1.1, x + 1.0, y + S + 1.0)
    y -= 5.5
    y = h.para(X0 + 9.5, y, [("LOW VITAMIN D → YOUR HEALTH SUFFERS. WINTER SUN ISN'T ENOUGH FOR MOST PEOPLE.", BLACK)],
               TW - 9.5, B)
    h.text(X0 + 9.5, y, "NOT AT NIGHT!", B, RED)
    h.line(X0 + 9.2, y - 0.8, X0 + 29, y - 0.9, RED, 0.24)
    y -= 6
    y = pencil(h, X0 + 12, y, ["5,000 IU IS ABOVE THE 4,000 IU/DAY", "UPPER LIMIT (US NIH). TEST YOUR LEVEL,", "ASK A DOCTOR BEFORE HIGH DOSES."])
    y -= 6

    capsule(h, X0 + 3.5, y - 0.5)
    h.text(X0 + 9.5, y - 1.5, "MAGNESIUM", 2.4, GREEN, 0.28)
    y -= 7.5
    x = h.text(X0 + 10.5, y, "DAILY · DON'T BE DEFICIENT", S)
    h.rect(X0 + 9.3, y - 1.1, x + 1.0, y + S + 1.0)
    y -= 5.5
    y = h.para(X0 + 9.5, y, [("BEING LOW MESSES WITH", BLACK), ("300+ ENZYME PROCESSES", RED, "u"),
                             (": BRAIN, SKIN, LUNGS, EVERYTHING.", BLACK)], TW - 9.5, B)


def p_supplements_2(h):
    y = H - 13
    drop(h, X0 + 3.5, y + 0.5)
    h.text(X0 + 9.5, y - 1.5, "ELECTROLYTES", 2.4, GREEN, 0.28)
    y -= 7.5
    x = h.text(X0 + 10.5, y, "PICK IF: YOU TRAIN HARD & SWEAT A LOT", S)
    h.rect(X0 + 9.3, y - 1.1, x + 1.0, y + S + 1.0)
    top = y + 9
    y -= 8.5
    moon(h, X0 + 3.5, y - 0.5)
    h.text(X0 + 9.5, y - 1.5, "STRESS SUPPORT", 2.4, GREEN, 0.28)
    y -= 7.5
    x = h.text(X0 + 10.5, y, "PICK IF: ANXIETY / HIGH STRESS · AT NIGHT", S)
    h.rect(X0 + 9.3, y - 1.1, x + 1.0, y + S + 1.0)
    y -= 5.5
    y = h.para(X0 + 9.5, y, [("ASHWAGANDHA, LEMON BALM, PASSIONFLOWER, L-THEANINE.", BLACK)], TW - 12, B)
    y = h.para(X0 + 9.5, y, [("LOWER CORTISOL →", BLACK), ("RECOVERY, HORMONES, OVERALL HEALTH.", RED)], TW - 12, B)
    h.brace(X1 - 1.0, y + 3, top, BLACK, 0.24, depth=1.8)
    y -= 2
    h.hook(X0 + 10.5, y + 2.6, y + 0.6, 3.0)
    y = h.para(X0 + 15, y, [("CHOOSE ONE, THE OTHER OR", BLACK), ("BOTH", GREEN, "u"),
                            ("— DEPENDING ON YOUR GOAL.", BLACK)], TW - 15, B)
    y -= 3.5

    h.text(X0, y, "THIS WEEK", 2.4, BLACK, 0.28)
    h.line(X0 - 0.3, y - 0.9, X0 + 17.5, y - 1.0, BLACK, 0.24)
    h.text(X0 + 20, y + 0.2, "TICK WHEN TAKEN ✓", 1.3, BLACK, 0.2)
    y -= 6.5
    days = "MTWTFSS"
    cx0, cw = X0 + 22.5, 7.0
    for i, d in enumerate(days):
        h.text(cx0 + i * cw + 0.9, y, d, 1.7, RED if i >= 5 else BLACK)
    y -= 4.8
    for row in ("VITAMIN D", "MAGNESIUM", "ELECTROLYTES", "STRESS"):
        h.text(X0, y + 0.3, row, 1.5)
        for i in range(7):
            bx = cx0 + i * cw
            h.rect(bx, y - 0.4, bx + 3.4, y + 3.0, BLACK, 0.2)
        y -= 5.6
    y -= 1
    y = strike_then(h, X0, y, "A 9-BOTTLE STACK", [("MISSED A DAY? →", BLACK), ("TAKE IT TOMORROW.", RED, "u")], TW)
    y = h.para(X0, y, [("DON'T DOUBLE UP, DON'T RESTART THE WEEK.", BLACK)], TW, B)
    y -= 3
    h.para(X0, y, [("ON MEDICATION OR HAVE A CONDITION? CHECK DOSES WITH YOUR DOCTOR FIRST. · FROM A SAVED POST.", BLACK)],
           TW, 1.35, lw=0.2)


ROWS = [
    # label, rice, potato, max, unit text
    ("FIBRE", 0.6, 4.7, 4.7, "0.6 / 4.7 G"),
    ("POTASSIUM", 55, 1150, 1150, "55 / 1150 MG"),
    ("VITAMIN C", 0, 21, 21, "0 / ~21 MG"),
    ("VITAMIN B6", 0.14, 0.67, 0.67, "0.14 / 0.67 MG"),
    ("SATIETY", 138, 323, 323, "138 / 323"),
]


def p_rice_1(h):
    y = header(h, 2, "RICE VS POTATOES", ["BOTH GREAT CARBS."])
    y = h.para(X0, y, [("POTATOES WIN ON", BLACK), ("NUTRIENTS, FIBRE & FULLNESS.", GREEN)], TW, B)
    y -= 6
    bowl(h, X0 + 25, y, 9)
    h.text(X0 + 31, y - 1.2, "RICE", 1.9, BLACK)
    potato(h, X0 + 50, y - 1)
    h.text(X0 + 55.5, y - 1.8, "POTATO", 1.9, RED)
    y -= 8.5
    h.text(X0, y, "PER ~200 KCAL · TOP = RICE, BOTTOM = POTATO", 1.3, BLACK, 0.2)
    y -= 6
    bx, bl = X0 + 21, 34.0
    for label, rice, pot, mx, txt in ROWS:
        h.text(X0, y - 0.9, label, 1.5)
        lr = max(bl * rice / mx, 0.4)
        h.rect(bx, y + 0.2, bx + lr, y + 1.9, BLACK, 0.2)
        if lr > 1:
            h.hatch(bx, y + 0.2, bx + lr, y + 1.9, BLACK, 0.14, gap=0.9)
        lp = bl * pot / mx
        h.rect(bx, y - 2.3, bx + lp, y - 0.6, RED, 0.22)
        h.hatch(bx, y - 2.3, bx + lp, y - 0.6, RED, 0.15, gap=0.6)
        h.text(bx + bl + 2.2, y - 1.0, txt, 1.25, BLACK, 0.19)
        y -= 9.5
    y -= 1
    h.para(X0, y, [("VALUES ARE APPROXIMATE: COOKED WHITE RICE VS BAKED POTATO WITH SKIN. SATIETY INDEX: WHITE BREAD = 100.",
                    BLACK)], TW, 1.3, lw=0.2)


def p_rice_2(h):
    y = H - 13
    bullets = [
        [("BOTH =", BLACK), ("CARBOHYDRATES,", BLACK, "box"), ("THE BODY'S MAIN ENERGY SOURCE.", BLACK)],
        [("RICE → A \"FORGETTABLE\" MICRONUTRIENT PROFILE.", BLACK)],
        [("POTATOES → SAME CALORIES, FAR MORE", BLACK), ("VITAMINS & MINERALS", RED, "u"),
         ("(POTASSIUM, VITAMIN C, B6).", BLACK)],
        [("POTATOES → REAL", BLACK), ("FIBRE", GREEN), ("(KEEP THE SKIN!) · RICE → ALMOST NONE.", BLACK)],
        [("BOILED POTATO TOPPED THE", BLACK), ("SATIETY INDEX", RED, "u"), ("→ MOST FILLING FOOD TESTED.", BLACK)],
    ]
    for segs in bullets:
        h.ellipse(X0 + 0.6, y + 0.9, 0.35, 0.35, BLACK, 0.4, overlap=0.8)
        y = h.para(X0 + 3, y, segs, TW - 3, B) - 2.2
    person(h, X0 + 4.5, y + 0.6)
    x = h.text(X0 + 6.5, y + 0.6, "HOLT ET AL., 1995.", 1.4, BLACK, 0.2)
    h.line(X0 + 3.5, y - 0.2, x + 0.5, y - 0.3, BLACK, 0.2)
    y -= 9
    top = y + 4.5
    y = h.para(X0 + 2.5, y, [("WHO SHOULD PICK RICE?", RED)], TW - 5, 2.1)
    y = h.para(X0 + 2.5, y, [("INTENSE ATHLETES NEEDING LOTS OF FAST, EASY CARBS.", BLACK)], TW - 5, B)
    h.rect(X0, y + 1.9, X1, top, BLACK, 0.24)
    y -= 3
    h.hook(X0 + 2, y + 2.6, y + 0.6, 3.0)
    h.para(X0 + 6.5, y, [("OTHERWISE", BLACK), ("POTATOES = THE BETTER EVERYDAY CHOICE.", GREEN, "u")], TW - 6.5, B)


BREAKFAST = [
    ("SEED & BERRY YOGURT BOWL", "МААЛИНГЫН ҮРТЭЙ АМТТАН",
     "100 G YOGURT · 100 G COTTAGE CHEESE · 50 G GROUND FLAX · 50 G BANANA · 50 G BLUEBERRIES · 20 G HONEY"),
    ("COLOURFUL LIVER PLATE", "ӨНГӨЛӨГ ТАВАГ", "120 G BEEF LIVER · 100 G BROCCOLI · ½ PEACH OR APPLE · 1 TBSP BUTTER · GREEN ONION"),
    ("EGG WITH MEAT", "МАХТАЙ ӨНДӨГ", "1 EGG · 50 G BEEF · 1 TSP OLIVE OIL · SALT, PEPPER"),
    ("SUNNY-SIDE UP", "ШАР НҮДЭН", "2 EGGS · 100 G FRIED GROUND BEEF · ½ AVOCADO (70 G) · 1 TBSP OLIVE OIL"),
    ("CABBAGE STIR-FRY", "БАЙЦААТАЙ ХУУРГА",
     "150 G BEEF · 200 G CABBAGE · 75 G CARROT · 100 G POTATO · ½ ONION · 2 GARLIC · 1 TBSP BEEF FAT · 20 G CHILI SAUCE"),
    ("JUICY LIVER", "ШҮҮСЛЭГ ЭЛЭГ", "150 G BEEF LIVER · 50 G LAMB TAIL FAT · 2 PICKLED CUCUMBERS. FRY THE FAT FIRST, THEN THE LIVER."),
    ("PROTEIN YOGURT", "ХУУРАЙ УУРАГТАЙ ТАРАГ", "100 G YOGURT · 30 G PROTEIN POWDER · 15 G FLAX · 20 G ALMONDS"),
    ("BLUEBERRY YOGURT", "НЭРСТЭЙ ТАРАГ", "200 G YOGURT · 100 G BLUEBERRIES · 20 G HONEY. STIR IN A BOWL, DONE."),
]
LUNCH = [
    ("CHICKPEA PROTEIN SALAD", "АНГААХАЙ ШОШТОЙ САЛАТ",
     "100 G CHICKPEAS · SMALL CAN TUNA (95 G) · 50 G CORN · 50 G CARROT · 20 G OLIVE-OIL MAYO · SALAD LEAVES"),
    ("CABBAGE CHICKEN", "БАЙЦААТАЙ ТАХИА",
     "150 G CHICKEN · 150 G CABBAGE · 70 G CARROT (FINE-CUT) · GREEN ONION · 1 TBSP OLIVE OIL · 20 G MAYO"),
    ("CHICKEN, VEG & RICE", "БУДААТАЙ НОГООТОЙ ХУУРГА",
     "150 G CHICKEN · 100 G BROCCOLI · 70 G CARROT · 50 G STEAMED RICE · GREEN ONION · BEEF FAT · SOY + CHILI SAUCE"),
    ("PROTEIN SMOOTHIE", "УУРАГЛАГ СМУТИ", "100 G YOGURT · 1 CUP WATER · 1 APPLE · 15 G FLAX · 30 G PROTEIN POWDER. BLEND."),
    ("LIVER & EGGS", "ЭЛЭГТЭЙ ӨНДӨГ", "100 G BEEF LIVER · 2 EGGS · 1 TBSP OLIVE OIL · 1 GREEN ONION"),
]
DINNER = [
    ("MILLET MILK TEA + LAMB RIBS", "ХИЙЦТЭЙ ЦАЙ", "220 G LAMB RIBS · 50 G MILLET · 1 TBSP BUTTER · 1 L WATER · TEA · 1 CUP MILK"),
    ("TOFU & LENTILS (VEGAN)", "ДҮПҮТЭЙ ВЕГАН ХООЛ",
     "250 G SOFT TOFU · 100 G LENTILS · 100 G STEAMED BROCCOLI · GREEN ONION · 1 TBSP BUTTER · SOY SAUCE"),
    ("LENTIL & BEEF STIR-FRY", "ЛЕНТИЛ БУДААТАЙ ХУУРГА",
     "100 G BEEF · LENTILS · 100 G STEAMED BROCCOLI · GREEN ONION · 1 TBSP BUTTER · WATER"),
    ("CHICKEN & POTATOES", "ТӨМСТЭЙ ХУУРГА", "150 G CHICKEN · 200 G POTATO · 100 G BROCCOLI · 1 TBSP BEEF FAT"),
    ("CHICKEN, VEG & RICE", "БУДААТАЙ НОГООТОЙ ХУУРГА", "SAME AS LUNCH: CHICKEN, BROCCOLI, CARROT, 50 G RICE, SOY + CHILI"),
    ("PROTEIN SHAKE", "УСАНД НАЙРУУЛСАН УУРАГ", "40 G PROTEIN POWDER · 500 ML WATER. SHAKE HARD IN A LIDDED CUP."),
]


def meal(h, y, n, name, mn, ingr):
    x = h.text(X0, y, f"{n}.", B, RED)
    h.text(x + 1.0, y, name, B, BLACK, 0.25)
    y -= 3.4
    h.text(X0 + 3.6, y, mn, 1.3, GREEN, 0.19)
    y -= 3.4
    y = h.para(X0 + 3.6, y, [(ingr, BLACK)], TW - 3.6, S, pitch=3.2, lw=0.2)
    return y - 2.4


def section(h, y, title, mn, note, doodle):
    h.text(X0, y, title, 2.6, GREEN, 0.3)
    w = h.width(title, 2.6)
    h.line(X0 - 0.3, y - 1.0, X0 + w + 0.6, y - 1.1, GREEN, 0.24)
    h.line(X0 + 0.5, y - 1.7, X0 + w + 1.4, y - 1.75, GREEN, 0.2)
    doodle(h, X1 - 6, y + 1.2)
    y -= 5.2
    h.text(X0, y, mn, 1.35, BLACK, 0.2)
    if note:
        y -= 3.2
        h.text(X0, y, note, 1.35, RED, 0.2)
    return y - 6


def p_meals(h, part):
    if part == 1:
        y = header(h, 3, "PICK ONE PLATE.", ["ANY PLATE.", "FROM THE BOOK."])
        y = section(h, y, "BREAKFAST", "ӨГЛӨӨНИЙ ХООЛ", "NOT IN THE FIRST HOUR AFTER WAKING!",
                    lambda h, x, y: bowl(h, x, y - 0.5, 9))
        for i in range(4):
            y = meal(h, y, i + 1, *BREAKFAST[i])
    elif part == 2:
        y = H - 13
        for i in range(4, 8):
            y = meal(h, y, i + 1, *BREAKFAST[i])
        y -= 1
        top = y + 3.5
        y = h.para(X0 + 2.5, y, [("+ BREAD?", RED), ("50 G WHOLE-GRAIN BREAD + 1 TSP BUTTER = 136 KCAL.", BLACK),
                                 ("PICK WHOLE-GRAIN.", BLACK, "u")], TW - 5, S, pitch=3.3)
        h.rect(X0, y + 1.6, X1, top, BLACK, 0.2)
    elif part == 3:
        y = H - 13
        y = section(h, y, "LUNCH", "ӨДРИЙН ХООЛ · 12–1 PM", None, lambda h, x, y: plate(h, x, y, 11))
        for i in range(5):
            y = meal(h, y, i + 1, *LUNCH[i])
    elif part == 4:
        y = H - 13
        for label, segs in (("ANY DAY", [("EAT SLOWLY, CHEW WELL,", BLACK), ("STOP AT 80% FULL.", RED),
                                          ("DRINK LESS DURING THE MEAL.", BLACK)]),
                            ("RULE OF THUMB", [("EVERY PLATE HAS A", BLACK), ("PROTEIN BLOB.", RED, "u"),
                                               ("30–50 G PROTEIN PER MEAL.", BLACK)]),
                            ("SWAP RICE?", [("POTATOES: MORE VOLUME, FEWER KCAL, MORE FIBRE.", BLACK)])):
            x = h.text(X0, y, label, 2.0, GREEN, 0.26)
            h.arrow(x + 1, y + 0.9, x + 5, y + 0.9, BLACK, 0.22, head=0.9)
            y -= 4.2
            y = h.para(X0 + 3.5, y, segs, TW - 3.5, B) - 4
        y -= 1
        y = section(h, y, "DINNER", "ОРОЙН ХООЛ · 5–7 PM", "LIGHTER!", lambda h, x, y: plate(h, x, y, 11))
        for i in range(2):
            y = meal(h, y, i + 1, *DINNER[i])
    elif part == 5:
        y = H - 13
        for i in range(2, 6):
            y = meal(h, y, i + 1, *DINNER[i])
        y -= 1
        x = h.text(X0, y, "DONE BY 7", 2.0, RED, 0.26)
        h.rect(X0 - 1.0, y - 1.2, x + 1.0, y + 3.2, RED, 0.22)
        y -= 5.5
        y = h.para(X0 + 2, y, [("STOP EATING 2–4 H BEFORE BED. LIGHT PROTEIN, NOT FATTY OR HEAVY.", BLACK)], TW - 2, B)
        y -= 2
        y = h.para(X0 + 2, y, [("TRYPTOPHAN →", GREEN), ("LIGHT DINNERS WITH EGGS, TOFU, CHICKEN, MILK HELP SLEEP.",
                                                       BLACK)], TW - 2, B)
        y -= 3
        strike_then(h, X0, y, "MEAL-PREP 21 PLATES ON SUNDAY",
                    [("CAN'T COOK TONIGHT? →", BLACK), ("2 EGGS + WHATEVER MEAT IS IN THE FRIDGE.", RED, "u"),
                     ("SALT, PEPPER, DONE.", BLACK)], TW, B)


def p_sleep_1(h):
    y = header(h, 4, "SLEEP", ["IS PART OF", "THE DIET."])
    top = y + 4.2
    y = h.para(X0 + 2.5, y, [("WITHOUT ENOUGH SLEEP, THE BODY TURNS FOOD INTO FAT, EVEN ON A PERFECT DIET.", RED)],
               TW - 5, B)
    h.rect(X0, y + 1.8, X1, top, RED, 0.24)
    y -= 2.5
    y = h.para(X0, y, [("GHRELIN & LEPTIN GO OFF → HUNGER RISES WHEN YOU DON'T NEED FOOD. CORTISOL SAYS \"CONSERVE\".",
                        BLACK)], TW, B)
    y = h.para(X0, y, [("SAME FOOD →", BLACK), ("MORE FAT, LESS MUSCLE.", RED, "u")], TW, B)
    y -= 1.5
    y = pencil(h, X0 + 3, y, ["STRONG CLAIM. A STUDY (NEDELTCHEVA 2010):", "DIETING ON 5.5 H SLEEP LOST LESS FAT",
                              "AND MORE MUSCLE THAN ON 8.5 H."])
    y -= 6

    x = h.text(X0, y, "1.", 2.2, RED)
    h.text(x + 1, y, "WIND-DOWN TIMELINE", 2.2, BLACK, 0.27)
    y -= 15
    lx0, lx1 = X0 + 1, X1 - 7
    px = lambda hr: lx0 + (lx1 - lx0) * (hr - 18) / 4.5      # 6 PM .. 10:30 PM
    h.line(lx0, y, X1 - 1, y, BLACK, 0.26)
    for lab, hr in (("6 PM", 18), ("8", 20), ("9", 21), ("10", 22)):
        h.line(px(hr), y - 0.8, px(hr), y + 0.8, BLACK, 0.22)
        h.text(px(hr) - h.width(lab, 1.4) / 2, y - 3.6, lab, 1.4, BLACK, 0.2)
    h.line(px(18), y + 2.2, px(20.8), y + 2.1, RED, 0.3)
    h.text(px(18), y + 3.6, "LAST FOOD (2–4 H BEFORE BED)", 1.3, RED, 0.2)
    h.ellipse(px(21), y, 0.9, 0.9, BLACK, 0.3)
    h.text(px(21) - 13, y - 7.4, "MELATONIN RISES", 1.3, GREEN, 0.2)
    h.arrow(px(21) - 3.5, y - 5.6, px(21) - 0.4, y - 1.4, GREEN, 0.2, head=0.7)
    pts = [(px(21.3) + k * 0.3, y + 1.6 + math.sin(k / 10 * math.pi) * 1.4) for k in range(11)]
    h.poly(pts, BLACK, 0.22)
    h.text(px(21.1) - 1, y + 4.2, "SHORT WALK", 1.2, BLACK, 0.18)
    h.line(px(21.95), y + 1.5, px(22.45), y + 1.5, GREEN, 0.3)
    h.text(px(21.6), y - 10.4, "SCREENS OFF 30 MIN", 1.2, GREEN, 0.18)
    h.arrow(px(22.2) + 1.0, y - 8.6, px(22.2), y + 0.9, GREEN, 0.2, head=0.6)
    h.rect(px(22.5), y - 1.2, X1 - 1.5, y + 1.6, BLACK, 0.26)
    h.text(px(22.5) + 0.2, y - 3.6, "10:30", 1.4, BLACK, 0.2)
    h.text(px(22.5), y + 3.2, "IN BED", 1.4, BLACK, 0.2)
    y -= 16
    y = h.para(X0, y, [("CORTISOL IS HIGH IN THE MORNING, AND THAT'S FINE. AIM FOR BED BY", BLACK),
                       ("10–10:30 PM.", RED, "box")], TW, B)


def p_sleep_2(h):
    y = H - 13
    x = h.text(X0, y, "2.", 2.2, RED)
    h.text(x + 1, y, "STRESS", 2.2, BLACK, 0.27)
    y -= 6
    y = h.para(X0, y, [("CORTISOL MAKES YOU WANT TO EAT. THAT'S WHY BAD DAYS END IN SWEETS OR A DRINK.", BLACK)], TW, B)
    y = h.para(X0, y, [("FOOD EATEN STRESSED DIGESTS BADLY: BLOATING, STOMACH ACHE.", BLACK)], TW, B)
    y -= 1
    x = h.text(X0 + 3, y, "CALM DOWN FIRST, THEN EAT!", 2.1, RED, 0.26)
    h.line(X0 + 2.6, y - 0.9, x + 0.5, y - 1.0, RED, 0.24)
    y -= 9

    x = h.text(X0, y, "3.", 2.2, RED)
    x = h.text(x + 1, y, "MOVE", 2.2, BLACK, 0.27)
    h.text(x + 2, y + 0.2, "(SECOND, NOT FIRST)", 1.5, BLACK, 0.2)
    y -= 6
    top = y + 4.2
    y = h.para(X0 + 2.5, y, [("80–90% OF WEIGHT LOSS IS FOOD.", RED), ("CARRYING A LOT OF WEIGHT? LEARN TO FIX THE FOOD FIRST, THEN ADD EXERCISE.",
                                                                       BLACK)], TW - 5, B)
    h.rect(X0, y + 1.8, X1, top, BLACK, 0.24)
    y -= 12
    figure_jump(h, X0 + 6, y)
    figure_climber(h, X0 + 44, y + 0.6)
    y -= 5
    h.text(X0 + 2, y, "HALF SQUAT → JUMP", 1.5)
    h.text(X0 + 3, y - 3.2, "UNTIL YOU'RE SPENT", 1.3, GREEN, 0.2)
    h.text(X0 + 40, y, "MOUNTAIN CLIMBERS", 1.5)
    h.text(X0 + 41, y - 3.2, "FAST, HEART PUMPING", 1.3, GREEN, 0.2)
    y -= 13
    strike_then(h, X0, y, "8 HOURS FROM TONIGHT",
                [("PHONE DOWN", BLACK), ("15 MINUTES EARLIER THAN YESTERDAY.", RED, "u"), ("THEN 15 MORE TOMORROW.", BLACK)],
                TW, B)


PAGES = [p_supplements_1, p_supplements_2, p_rice_1, p_rice_2,
         lambda h: p_meals(h, 1), lambda h: p_meals(h, 2), lambda h: p_meals(h, 3), lambda h: p_meals(h, 4),
         lambda h: p_meals(h, 5), p_sleep_1, p_sleep_2]


def main(png=False):
    paper = paper_path((88, 125), None)
    if not paper.exists():
        raise SystemExit(f"missing {paper.name}: run python3 _Print/make_paper.py first")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W * mm, H * mm))
    c.setTitle("Health · handwritten")
    c.setAuthor("Gereru")
    c.beginForm("paper")
    c.drawImage(str(paper), 0, 0, W * mm, H * mm)
    c.endForm()
    for i, page in enumerate(PAGES):
        c.doForm("paper")
        page(Hand(c, seed=100 + i))
        c.showPage()
    c.save()
    print(OUT)
    if png:
        subprocess.run(["pdftoppm", "-r", "200", "-png", str(OUT), str(OUT.with_suffix(""))], check=True)


if __name__ == "__main__":
    main(png="--png" in sys.argv)
