#!/usr/bin/env python3
"""October 2026 · Week 1 → traveler's-notebook cards (82×116 mm).

Builds two HTML files next to this script:
  week1-tn.html        one card per page (screen / digital PDF)
  week1-tn-print.html  4 cards per A4 sheet, crop marks, sheets in reverse order
Then run `node print.js` to turn both into PDFs.
"""
import pathlib, random

HERE = pathlib.Path(__file__).parent
MONTH = "OCTOBER 2026 · W1"

# ───────────────────────────── data ─────────────────────────────
# quests: key, label, mongolian, icon
QUESTS = [
    ("steps", "10k steps", "алхам", "shoe"),
    ("food", "food", "хоол", "apple"),
    ("sleep", "sleep", "нойр", "moon"),
    ("gym", "gym", "gym", "dumbbell"),
    ("sport", "sport", "спорт", "ball"),
    ("burn", "1000 burn", "шаталт", "flame"),
    ("pull", "30 pull-up", "pull-up", "pullup"),
    ("push", "100 push-up", "push-up", "pushup"),
    ("spend", "≤ ¥80", "зарлага", "coin"),
]
LOCKED = [("bike", "bike 5km+", "дугуй", "bike"), ("focus", "focus 2h+", "focus", "target")]

# journal markup: <g> gym·cardio  <o> sport  <r> place·event  <b> people
DAYS = [
    dict(d="10.1", dow="THU", xp=450, photos=3,
         journal="Мэдэхгүйээ уул нь сарыг ууж эхлүүлэхгүй гэж бодож байгаад л уучихлаа даа хөөрхий. "
                 "<b>Хулан, Золоо, тэгээд Төгөлдөр</b> байсан байхаа. <r>Дэнисийн төрсөн өдөр</r> болсон юм байна, "
                 "<g>жимдээ</g> явчихаад иртэл шүү.",
         chips=[("heart", "Дэнис b-day")],
         steps=10.4, burn=651, spent=35, spent_items="一团火 ¥21 · 悦生活 ¥12",
         bed=7.00, wake=13 + 5 / 60, bed_s="07:00", wake_s="13:05", score=64, hrs="5h54",
         kcal=4372, macro=(180, 539, 82), gym=("push", 8), sport=None,
         q=dict(steps=100, food=(50, "h"), gym=200, pull=50, spend=50)),
    dict(d="10.2", dow="FRI", xp=500, photos=5,
         journal="Аймар <g>жимд</g> явсан өдөр, нуруу хийсэн, тэгээд <g>кардио</g>.",
         chips=[("dumbbell", "back day"), ("ball", "cardio")],
         steps=11.9, burn=803, spent=126, spent_items="好想来 ¥35 · 提现 ¥30 · KFC ¥29",
         bed=9 + 33 / 60, wake=18.1, bed_s="09:33", wake_s="18:06", score=77, hrs="8h23",
         kcal=2647, macro=(83, 309, 109), gym=("pull", 7), sport="cardio",
         q=dict(steps=100, food=(50, "h"), sleep=(50, "h"), gym=200, sport=100)),
    dict(d="10.3", dow="SAT", xp=470, photos=8,
         journal="Юмаа хийж жаахан суусан, орой нь <g>жимдсэн</g>.",
         chips=[],
         steps=12.8, burn=824, spent=156, spent_items="card ¥33 · KFC ¥30 · 凯德 ¥28 · 西西弗 ¥26",
         bed=4.6, wake=11 + 32 / 60, bed_s="04:36", wake_s="11:32", score=66, hrs="6h50",
         kcal=2630, macro=(115, 240, 134), gym=("leg", 6), sport=None,
         q=dict(steps=100, food=170, gym=200)),
    dict(d="10.4", dow="SUN", xp=0, photos=5,
         journal="Өдөр сэрээд <r>эгчийнд</r> очсон, <r>кино</r> үзээд юм идээд л өнгөрлөө дөө.",
         chips=[("pin", "эгчийнд"), ("film", "кино")],
         steps=4.6, burn=575, spent=100, spent_items="好想来 ¥31 · 打车 ¥28 · 便利店 ¥24",
         bed=6 + 19 / 60, wake=12.2, bed_s="06:19", wake_s="12:12", score=64, hrs="5h51",
         kcal=None, macro=None, gym=None, sport=None, q={}),
    dict(d="10.5", dow="MON", xp=400, photos=4,
         journal="<b>Золоо, Хулан</b> хоёртой <r>Kaide</r> орж хичээл хийсэн, орой нь <g>жимдээ</g> явсан.",
         chips=[("pin", "Kaide")],
         steps=12.5, burn=687, spent=115, spent_items="西西弗 ¥80 (2×) · 好想来 ¥23",
         bed=3.25, wake=11 + 56 / 60, bed_s="03:15", wake_s="11:56", score=65, hrs="8h32",
         kcal=None, macro=None, gym=("push", 8), sport=None,
         q=dict(steps=100, sleep=(50, "h"), gym=200, pull=50)),
    dict(d="10.6", dow="TUE", xp=570, photos=4,
         journal="Хүйтэн өдөр байсан, орой <g>жимдээ</g> явсан, хүмүүсийн аймар түүх сонссон хаха.",
         chips=[("snow", "хүйтэн")],
         steps=10.1, burn=542, spent=53, spent_items="书店 ¥16 · 瑞幸 ¥15 · 好想来 ¥13",
         bed=4.35, wake=12 + 7 / 60, bed_s="04:21", wake_s="12:07", score=73, hrs="7h45",
         kcal=2681, macro=(156, 409, 48), gym=("pull", 7), sport=None,
         q=dict(steps=100, food=170, gym=200, pull=50, spend=50)),
    dict(d="10.7", dow="WED", xp=250, photos=1,
         journal="Юмаа хийж байгаад гарч <o>сагсдсан</o> юм байна. Амралт дууслаа даа.",
         chips=[("ball", "сагс")],
         steps=11.3, burn=598, spent=132, spent_items="话费 ¥38 · 家家悦 ¥31 · 赵一鸣 ¥18",
         bed=5 + 19 / 60, wake=12.75, bed_s="05:19", wake_s="12:45", score=70, hrs="7h11",
         kcal=2433, macro=(72, 347, 92), gym=None, sport="basketball",
         q=dict(steps=100, food=(50, "h"), sport=100)),
]

# exercises: name, set-rating, [(weight, reps)]  ·  "10+10" = per-hand, "10/10R" = per-side reps
SESSIONS = {
    "10.1": dict(kind="push", rating=8, sets=21, burn=651, ex=[
        ("Push-ups", None, [("BW", 30), ("BW", 20), ("BW", 10)]),
        ("Pull-ups", None, [("BW", 12), ("BW", 8), ("BW", 10)]),
        ("Pec fly", 8.5, [("38.5", 10), ("38.5", 8), ("38.5", 8)]),
        ("Incline bench", 7.3, [("80", 6), ("80", 8), ("80", 8)]),
        ("Lateral raise", 7.6, [("10+10", 20), ("10+10", 20), ("10+10", 20)]),
        ("Cable fly ①", 8.6, [("55lb", "15/15"), ("65lb", "12/12")]),
        ("Cable fly ②", 7.3, [("35lb", "8/8"), ("35lb", "10/10")]),
        ("DB sh. press", 6.8, [("20+20", 8), ("20+20", 12), ("20+20", 8)]),
        ("Rear delt", 7.1, [("28.5", 10)]),
        ("Tricep OH", None, [("75lb", 8), ("75lb", 10)]),
        ("Tricep 1-arm", None, [("35lb", "10/10"), ("35lb", "10/10")]),
    ], notes=[("star", "30 pull-ups ✓ · chest, shoulders, triceps all hit"),
              ("star", "your own set avg 7.6 · best cable fly 8.6"),
              ("pen", "DB shoulder press felt weakest (6.8)")],
        vs=None),
    "10.2": dict(kind="pull", rating=7, sets=16, burn=803, ex=[
        ("Push-ups", None, [("BW", 30)]),
        ("Pull-ups", None, [("BW", 10), ("BW", 10), ("BW", 7)]),
        ("Seated T-row", None, [("40", "10/10"), ("40", "10/10"), ("40", "10/10")]),
        ("Wide grip", None, [("125lb", 8), ("125lb", 10), ("125lb", 8)]),
        ("Narrow grip", None, [("63.5", 10), ("63.5", 10)]),
        ("Back ext.", None, [("75", 6), ("50", 10)]),
        ("Seated curl", None, [("12.5", 8), ("12.5", 10)]),
        ("Stand DB curl", None, [("12.5", 10)]),
        ("Abs", None, [("20", 15), ("20", 15), ("20", 10)]),
    ], notes=[("star", "back, biceps and abs covered"),
              ("pen", "pull-ups 27 of 30 · 3 short"),
              ("star", "cardio after")],
        vs=None),
    "10.3": dict(kind="leg", rating=6, sets=9, burn=824, ex=[
        ("Squat", None, [("110", 6), ("110", 4)]),
        ("Leg extension", None, [("70", 8), ("70", 10), ("70", 10)]),
        ("1-leg press", None, [("55", "12/12"), ("65", "12/12")]),
        ("Abductor", None, [("100", 20), ("100", 20)]),
    ], notes=[("star", "squat 110 × 6 is strong"),
              ("pen", "only 9 sets"),
              ("pen", "no hamstring or calf work"),
              ("pen", "no push / pull-ups today")],
        vs=None),
    "10.5": dict(kind="push", rating=8, sets=16, burn=687, ex=[
        ("Pull-ups", None, [("BW", 10), ("BW", 10), ("BW", 10)]),
        ("Push-ups", None, [("BW", 20), ("BW", 20), ("BW", 10)]),
        ("Pec fly", None, [("95lb", 10), ("105lb", 15), ("145lb", 8)]),
        ("Incline DB", None, [("35+35", 6), ("35+35", 6), ("35+35", 6)]),
        ("Lateral raise", None, [("10+10", 20), ("10+10", 20)]),
        ("Rear delt", None, [("28.5", 10), ("28.5", 10)]),
        ("Pushdown", None, [("105lb", 10), ("105lb", 10)]),
        ("Shoulder press", None, [("40", 10), ("40", 10)]),
        ("Cable fly low", None, [("55lb", 12), ("55lb", 12)]),
    ], notes=[("star", "pec fly up to 145 lb"),
              ("star", "every push muscle hit"),
              ("star", "30 pull-ups ✓ · 50 push-ups")],
        vs={"Pull-ups": ("eq", "10.1 · 30 total"), "Push-ups": ("dn", "10.1 · 60 total"),
            "Pec fly": ("eq", "10.1 · 38.5×10 · other unit"), "Lateral raise": ("eq", "10.1 · 10+10×20"),
            "Rear delt": ("eq", "10.1 · 28.5×10")}),
    "10.6": dict(kind="pull", rating=7, sets=13, burn=542, ex=[
        ("Pull-ups", None, [("BW", 17), ("BW", 13)]),
        ("Push-ups", None, [("BW", 30), ("BW", 30)]),
        ("Narrow grip", None, [("38.5", 8), ("38.5", 8)]),
        ("Back ext.", None, [("45", 10), ("45", 10)]),
        ("1-arm lat", None, [("25", "10/10"), ("25", "10/10")]),
        ("Cable pray", None, [("28", 10), ("28", 10)]),
        ("Incline curl", None, [("12.5", "10/10"), ("12.5", "10/10"), ("12.5", "8/8")]),
        ("Hammer curl", None, [("12.5", "8/8"), ("12.5", "8/8")]),
    ], notes=[("star", "pull-ups 17 + 13 ✓ · 60 push-ups"),
              ("pen", "rows were light, half the work was arms")],
        vs={"Pull-ups": ("up", "10.2 · 27 total"), "Push-ups": ("up", "10.2 · 30 total"),
            "Narrow grip": ("dn", "10.2 · 63.5×10"), "Back ext.": ("dn", "10.2 · 75×6")}),
}
KIND = {"push": ("PUSH DAY", "#f3c24f", "#7a5410"), "pull": ("PULL DAY", "#8fc0ea", "#1f4f86"),
        "leg": ("LEG DAY", "#f6b77c", "#8a3f12")}

MOMENTS = [("10.1-2", "10.1", "аниме үзсэн орой"), ("10.2-2", "10.2", "кардио · 30:08"),
           ("10.2-3", "10.2", "нуруу хийсэн өдөр"), ("10.3-1", "10.3", "юмаа хийж суусан"),
           ("10.3-2", "10.3", "нохойтой таарсан"), ("10.3-8", "10.3", "орой нь жимдсэн"),
           ("10.4-3", "10.4", "эгчийнд явах замд"), ("10.4-4", "10.4", "эгчийнд"),
           ("10.4-5", "10.4", "кино үзсэн"), ("10.5-2", "10.5", "Kaide · хичээл"),
           ("10.6-3", "10.6", "хүйтэн өдөр · жим"), ("10.7-1", "10.7", "сагс · амралт дууслаа")]

# ───────────────────────────── pixel icons ─────────────────────────────
PAL = {"K": "#3a2a1f", "W": "#fff9ec", "R": "#d0453a", "O": "#e8862e", "Y": "#f2c443", "G": "#5c9a3c",
       "g": "#9cc65a", "B": "#4a78c0", "b": "#9cc0ea", "P": "#8a5cb8", "N": "#8a5a35", "n": "#c48a54",
       "S": "#9a9a9a", "s": "#dcdcdc", "C": "#f1c9a0", "D": "#2b2b38", "p": "#e7a0b8"}
ICONS = {
    "shoe": ["........", ".KKK....", ".KBK....", ".KBBKK..", ".KBBBBK.", ".KBBBBBK", ".KWWWWWK", ".KKKKKKK"],
    "flame": ["...R....", "...RR...", "..RORR..", "..ROOR.R", ".RROYORR", ".ROYYYOR", ".ROYYYOR", "..RRRRR."],
    "coin": ["..KKKK..", ".KYYYYK.", "KYYKYYOK", "KYYKYYOK", "KYYKYYOK", "KYYYYYOK", ".KOOOOK.", "..KKKK.."],
    "apple": ["....G...", "...G....", ".RRKRR..", "RRWRRRR.", "RWRRRRR.", "RRRRRRR.", ".RRRRR..", "..R.R..."],
    "moon": ["..OYYY..", ".OYY....", "OYY.....", "OYY.....", "OYY.....", "OYYY....", ".OYYYYY.", "..OOOO.."],
    "dumbbell": ["........", ".K....K.", "KRK..KRK", "KRKKKKRK", "KRKKKKRK", "KRK..KRK", ".K....K.", "........"],
    "ball": ["..KKKK..", ".KOKOOK.", "KOOKOOOK", "KKKKKKKK", "KOOOKOOK", "KOOOKOOK", ".KOOKOK.", "..KKKK.."],
    "pullup": ["KKKKKKKK", ".K....K.", ".K.KK.K.", "..KCCK..", "..KCCK..", "...BB...", "..BBBB..", "...BB..."],
    "pushup": ["........", "........", "KK......", "KKBBBBB.", "..BBBBBB", "..K....K", "..K....K", "KKKKKKKK"],
    "gem": ["..BBBB..", ".BbbbbB.", "BbWbbbbB", "BBBBBBBB", ".BbbbbB.", "..BbbB..", "...BB...", "........"],
    "heart": [".RR.RR..", "RWRRRRR.", "RRRRRRR.", "RRRRRRR.", ".RRRRR..", "..RRR...", "...R....", "........"],
    "star": ["...Y....", "...Y....", "..YYY...", "YYYYYYY.", ".YYYYY..", ".YY.YY..", ".Y...Y..", "........"],
    "camera": ["........", "..KKK...", "KKKKKKKK", "KssKKssK", "KsKbbKsK", "KsKbbKsK", "KssKKssK", "KKKKKKKK"],
    "notes": ["KKKKKKK.", "KWWWWWK.", "KWKKKWK.", "KWWWWWK.", "KWKKKWK.", "KWWWWWK.", "KWKKWWK.", "KKKKKKK."],
    "bike": ["....KK..", "...K....", "..KKKKK.", ".K.K..K.", "KKK.K.KK", "K.K..KKK", "KKK...KK", "........"],
    "chest": ["........", ".NNNNNN.", "NnnnnnnN", "NNNYYNNN", "NnnYYnnN", "NnnnnnnN", "NNNNNNNN", "........"],
    "target": ["..RRRR..", ".RWWWWR.", "RWRRRRWR", "RWRWWRWR", "RWRWWRWR", "RWRRRRWR", ".RWWWWR.", "..RRRR.."],
    "leaf": ["......G.", "....OOG.", "..OOYOO.", ".OOYOOO.", ".OYOOO..", "OYOOO...", "YOO.....", "Y......."],
    "trophy": ["KYYYYYK.", "YYYYYYY.", ".YYYYY..", "..YYY...", "...Y....", "...Y....", "..NNN...", ".NNNNN.."],
    "calendar": [".K..K...", "KKKKKKKK", "KRRRRRRK", "KWWWWWWK", "KWKWKWWK", "KWWWWWWK", "KWKWKWWK", "KKKKKKKK"],
    "pin": ["..RRRR..", ".RRWWRR.", ".RWWWWR.", ".RRWWRR.", "..RRRR..", "...RR...", "...RR...", "....R..."],
    "film": ["KKKKKKKK", "KWKWKWKK", "KKKKKKKK", "KbbbbbbK", "KbbbbbbK", "KKKKKKKK", "KWKWKWKK", "KKKKKKKK"],
    "snow": ["...b....", ".b.b.b..", "..bbb...", "bbbWbbb.", "..bbb...", ".b.b.b..", "...b....", "........"],
    "pen": [".......K", "......KY", ".....KYK", "....KYK.", "...KYK..", "..KYK...", ".KnK....", ".KK....."],
    "lock": ["..KKKK..", ".K....K.", ".K....K.", "KKKKKKKK", "KYYYYYYK", "KYYKKYYK", "KYYYYYYK", "KKKKKKKK"],
    "check": ["........", ".......G", "......GG", "G....GG.", "GG..GG..", ".GGGG...", "..GG....", "........"],
    "sun": ["...Y....", ".Y.Y.Y..", "..YYY...", "YYYYYYY.", "..YYY...", ".Y.Y.Y..", "...Y....", "........"],
}


def icon(name, cls="ic"):
    rows = ICONS[name]
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            c = row[x]
            if c == ".":
                x += 1
                continue
            x2 = x
            while x2 < len(row) and row[x2] == c:
                x2 += 1
            out.append(f'<rect x="{x}" y="{y}" width="{x2 - x}" height="1" fill="{PAL[c]}"/>')
            x = x2
    return (f'<svg class="{cls}" viewBox="0 0 8 8" shape-rendering="crispEdges" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(out)}</svg>')


# ───────────────────────────── pixel scene ─────────────────────────────
def scene(mode="day", W=164, H=96):
    """Autumn hillside with a little house. mode = day | dusk"""
    rnd = random.Random(10 if mode == "day" else 7)
    g = [[None] * W for _ in range(H)]

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c

    def rect(x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                put(xx, yy, c)

    if mode == "day":
        sky = ["#f3b46f", "#f6c381", "#f8d194", "#f9dca8", "#fae5bb", "#fbecc9"]
    else:
        sky = ["#2d2f5e", "#3b3a72", "#5a4a86", "#86598e", "#b76b83", "#e08a72"]
    band = 58 // len(sky)
    for y in range(58):
        i = min(y // band, len(sky) - 1)
        for x in range(W):
            c = sky[i]
            if i + 1 < len(sky) and y % band >= band - 2 and (x + y) % 2 == 0:
                c = sky[i + 1]
            put(x, y, c)
    # sun / moon
    cx, cy, r = (128, 20, 9) if mode == "day" else (130, 16, 6)
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if d <= r * r:
                put(x, y, "#fff3c4" if mode == "day" else "#f6efd0")
            elif d <= (r + 1.2) ** 2 and mode == "day":
                put(x, y, "#ffe39a")
    if mode == "dusk":
        for x, y in [(cx + 2, cy - 2), (cx + 3, cy), (cx + 1, cy + 2)]:
            put(x, y, "#ddd3b0")
        for _ in range(40):
            put(rnd.randrange(W), rnd.randrange(0, 34), rnd.choice(["#f6efd0", "#c9c3e8", "#ffffff"]))
    # clouds
    cloud = "#fff6e2" if mode == "day" else "#7c6a9c"
    for (x0, y0, w) in [(14, 12, 18), (58, 7, 14), (92, 26, 16)]:
        rect(x0 + 3, y0, w - 6, 2, cloud)
        rect(x0, y0 + 2, w, 3, cloud)
    # hills
    import math
    far = "#c98a4b" if mode == "day" else "#5b4673"
    mid = "#b0703a" if mode == "day" else "#4b3a5e"
    near = "#8e9a3e" if mode == "day" else "#3f4a3a"
    near2 = "#a6ad4a" if mode == "day" else "#4d5843"
    for x in range(W):
        h1 = int(48 + 6 * math.sin(x / 13) + 3 * math.sin(x / 5.5))
        h2 = int(58 + 5 * math.sin(x / 17 + 2) + 2 * math.sin(x / 7))
        h3 = int(68 + 3 * math.sin(x / 21 + 1))
        for y in range(h1, H):
            put(x, y, far)
        for y in range(h2, H):
            put(x, y, mid)
        for y in range(h3, H):
            put(x, y, near if (x + y) % 3 else near2)
    # path
    for y in range(76, H):
        w = 3 + (y - 76) // 2
        rect(50 - w // 2 + (y - 76) // 3, y, w, 1, "#d9b77a" if mode == "day" else "#6d5f52")

    def tree(x, base, kind):
        pal = {"o": ("#d9692b", "#f0a03c"), "r": ("#b8432f", "#d9673f"), "y": ("#e2a93a", "#f5d36a"),
               "p": ("#3f6b3a", "#5c8a4a")}[kind]
        if mode == "dusk":
            pal = {"o": ("#9a4a3a", "#b8664a"), "r": ("#7d3236", "#9a4744"), "y": ("#a07a45", "#bf9a5a"),
                   "p": ("#2c4a38", "#3d5e44")}[kind]
        rect(x, base - 4, 2, 4, "#6b4226" if mode == "day" else "#3a2a2a")
        if kind == "p":
            for i in range(9):
                w = 1 + i
                rect(x + 1 - w // 2, base - 13 + i, w, 1, pal[0] if i % 3 else pal[1])
            return
        for yy in range(-6, 5):
            for xx in range(-5, 7):
                if (xx - 0.5) ** 2 / 30 + yy ** 2 / 22 <= 1:
                    put(x + xx, base - 9 + yy, pal[1] if (xx < 0 and yy < 0 and (xx + yy) % 2) else pal[0])

    for (x, b, k) in [(8, 66, "o"), (20, 62, "r"), (74, 66, "y"), (86, 70, "o"), (112, 72, "p"),
                      (140, 70, "r"), (152, 66, "y"), (124, 78, "o"), (30, 86, "y"), (148, 90, "o")]:
        tree(x, b, k)
    # house
    hx, hy = 38, 64
    wall = "#f3e2c4" if mode == "day" else "#b8a890"
    rect(hx, hy, 18, 12, "#5a3a22")
    rect(hx + 1, hy + 1, 16, 10, wall)
    for i in range(8):
        rect(hx - 1 + i, hy - i, 20 - 2 * i, 1, "#c0412f" if mode == "day" else "#8a3a36")
    rect(hx + 12, hy - 9, 3, 5, "#6b4226")
    smoke = "#fdf3df" if mode == "day" else "#9a8fb0"
    for i, (sx, sy) in enumerate([(hx + 13, hy - 11), (hx + 14, hy - 13), (hx + 13, hy - 15), (hx + 15, hy - 17)]):
        rect(sx, sy, 2 if i % 2 else 1, 1, smoke)
    rect(hx + 3, hy + 5, 4, 6, "#7a4a2a")
    rect(hx + 10, hy + 3, 4, 4, "#ffd86a" if mode == "dusk" else "#9cc0ea")
    rect(hx + 11, hy + 3, 1, 4, "#5a3a22")
    # pumpkins
    for px in (hx + 20, hx + 25):
        rect(px, hy + 9, 4, 3, "#e8862e")
        rect(px + 1, hy + 9, 1, 3, "#c96a1e")
        put(px + 2, hy + 8, "#5c9a3c")
    # tiny hero (black hair, dark coat)
    tx, ty = 96, 70
    hero = ["..KKKK..", ".KKKKKK.", ".KCCCCK.", ".KCKCKK.", "..CCCC..", ".DDDDDD.", "DDDDDDDD",
            "C.DDDD.C", "..DDDD..", "..D..D..", "..K..K.."]
    hp = dict(PAL, D="#2b2b38" if mode == "day" else "#1f1f2a")
    for y, row in enumerate(hero):
        for x, c in enumerate(row):
            if c != ".":
                put(tx + x, ty + y, hp[c])
    # falling leaves
    for _ in range(22):
        put(rnd.randrange(W), rnd.randrange(30, 80), rnd.choice(["#e8862e", "#d0453a", "#f2c443"]))

    out = []
    for y in range(H):
        x = 0
        while x < W:
            c = g[y][x]
            x2 = x
            while x2 < W and g[y][x2] == c:
                x2 += 1
            if c:
                out.append(f'<rect x="{x}" y="{y}" width="{x2 - x}" height="1" fill="{c}"/>')
            x = x2
    return (f'<svg class="scene" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
            f'shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg">{"".join(out)}</svg>')


# ───────────────────────────── helpers ─────────────────────────────
def segbar(frac, color, segs=10):
    frac = max(0.0, min(1.0, frac))
    full = frac * segs
    cells = []
    for i in range(segs):
        f = max(0.0, min(1.0, full - i))
        cells.append(f'<i style="background:linear-gradient(90deg,{color} {f * 100:.0f}%,transparent {f * 100:.0f}%)"></i>')
    return f'<span class="seg">{"".join(cells)}</span>'


def qstate(day, key):
    v = day["q"].get(key)
    if v is None:
        return 0, None
    if isinstance(v, tuple):
        return v[0], "half"
    return v, "full"


def card(body, page, cls=""):
    return (f'<section class="card {cls}">{body}'
            f'<div class="foot"><span>{MONTH}</span><span>{page}</span></div></section>')


def hdr(ic, title, right=""):
    return f'<div class="hdr">{icon(ic)}<h1>{title}</h1><span class="r">{right}</span></div>'


PAGES = {}
PAGE_NO = {}


def fmt_k(v):
    return f"{v:.1f}k"


TOTAL_XP = sum(d["xp"] for d in DAYS)
STEPS = 73577
BURN = sum(d["burn"] for d in DAYS)
SPENT = 718
LOGGED = [d for d in DAYS if d["kcal"]]


def qcount(key):
    return sum(1 for d in DAYS if d["q"].get(key) is not None)


def qxp(key):
    return sum(qstate(d, key)[0] for d in DAYS)


def qpct(d):
    return round(100 * len(d["q"]) / len(QUESTS))


# ───────────────────────────── pages ─────────────────────────────
def p_cover():
    lv_frac = (TOTAL_XP % 1000) / 1000
    body = f'''
<div class="cover-art">{scene("day")}
  <div class="sign"><b>OCTOBER</b><span>WEEK 1 · 10.1 – 10.7</span></div>
</div>
<div class="subt">{icon("notes")} WEEKLY QUEST LOG · CHAPTER 10 · WEEK 1</div>
<div class="box lv">
  <div class="lvbadge">LV 3</div>
  <div class="lvinfo"><div class="big">{TOTAL_XP:,} XP</div>
    <div class="mut">avg {TOTAL_XP // 7} / day · 1000 XP = 1 LV</div>
    {segbar(lv_frac, "#4a78c0", 20)}
    <div class="mut">{TOTAL_XP % 1000} / 1,000 → LV 4</div></div>
</div>
<div class="grid2">
  <div class="box stat">{icon("dumbbell")}<small>GYM</small><b>5 <em>/ 7 days</em></b></div>
  <div class="box stat">{icon("shoe")}<small>STEPS / DAY</small><b>10,511</b></div>
  <div class="box stat">{icon("moon")}<small>SLEEP / NIGHT</small><b>7h12m</b></div>
  <div class="box stat">{icon("gem")}<small>TOTAL XP</small><b>{TOTAL_XP:,}</b></div>
</div>
<div class="cnote">10.1 → 10.7 · 7 days logged · 5 gym sessions · 2 sport · 30 snapshots · what I lacked → p.{PAGE_NO["lack1"]}</div>'''
    return card(body, 1, "cover")


def tile(color, ic, title, big, unit, lines, frac, pct_label):
    return f'''<div class="tile"><div class="th" style="background:{color}">{icon(ic)}{title}</div>
<div class="tb"><div class="big">{big}<em>{unit}</em></div>{lines}
<div class="tbar">{segbar(frac, color, 10)}<b>{pct_label}</b></div></div></div>'''


def p_avg1():
    t = [
        tile("#5c9a3c", "moon", "SLEEP / NIGHT", "7h 12m", "",
             '<div class="tl"><u>sleep score 68 / 100</u></div><div class="tl">best 77 (10.2) · 7h+ nights 4 / 7</div>',
             7.2 / 8, "90%"),
        tile("#4a5aa8", "sun", "BED → WAKE", "05:46→13:06", "",
             '<div class="tl"><u>avg asleep → wake up</u></div><div class="tl">asleep before 12A · 0 / 7 nights</div>',
             0, "0%"),
        tile("#3d78b8", "shoe", "STEPS / DAY", "10,511", "",
             '<div class="tl"><u>GOAL 10,000 / day</u></div><div class="tl">10k+ days 6 / 7 · total 73,577</div>',
             1, "105%"),
        tile("#8a5cb8", "flame", "BURN / DAY", "669", "kcal",
             '<div class="tl"><u>GOAL 700 kcal / day</u></div><div class="tl">700+ days 2 / 7 · peak 824 (10.3)</div>',
             669 / 700, "96%"),
        tile("#c4473a", "coin", "SPENT / DAY", "¥103", "",
             '<div class="tl"><u>GOAL ≤ ¥80 / day</u></div><div class="tl">within ¥80 · 2 / 7 · total ¥718</div>',
             80 / 103, "78%"),
        tile("#d9822b", "apple", "CALORIES / DAY", "2,953", "kcal",
             '<div class="tl"><u>LINE 2,400 · 5 / 7 logged</u></div><div class="tl">P 121g · C 369g · F 93g</div>',
             2400 / 2953, "81%"),
    ]
    body = hdr("star", "WEEKLY AVERAGE", "% = how close to the goal") + f'<div class="tiles">{"".join(t)}</div>'
    return card(body, 2)


def p_avg2():
    t = [
        tile("#b5652b", "dumbbell", "GYM", "5", "/ 5",
             '<div class="tl"><u>avg rating 7.2 / 10</u></div><div class="tl">push ×2 · pull ×2 · leg ×1</div>',
             1, "100%"),
        tile("#5c9a3c", "check", "QUESTS / DAY", "40", "%",
             '<div class="tl"><u>best 56% · 10.1 10.2 10.6</u></div><div class="tl">9 daily quests · 0 on 10.4</div>',
             0.4, "40%"),
        tile("#c4473a", "apple", "PROTEIN / DAY", "121", "g",
             '<div class="tl"><u>GOAL 150g · 5 days logged</u></div><div class="tl">peak 180g (10.1)</div>',
             121 / 150, "81%"),
        tile("#3a8f8a", "pullup", "PULL-UPS", "117", "reps",
             '<div class="tl"><u>GOAL 30+ / gym day</u></div><div class="tl">30+ days · 3 (10.1 10.5 10.6)</div>',
             3 / 4, "75%"),
        tile("#4a78c0", "pushup", "PUSH-UPS", "200", "reps",
             '<div class="tl"><u>GOAL 100+ / day</u></div><div class="tl">best 60 · 10.1 & 10.6</div>',
             0.6, "60%"),
        tile("#d9822b", "ball", "SPORT", "2", "days",
             '<div class="tl"><u>cardio 10.2 · basket 10.7</u></div><div class="tl">rest from gym 10.4 · 10.7</div>',
             2 / 7, "29%"),
    ]
    body = hdr("star", "WEEKLY AVERAGE", "2 / 2") + f'<div class="tiles">{"".join(t)}</div>'
    return card(body, 3)


def p_habits():
    cols = "".join(f'<th>{d["d"].split(".")[1]}<small>{d["dow"][0]}</small></th>' for d in DAYS)
    rows = []
    for key, label, mn, ic in QUESTS:
        cells = ""
        for d in DAYS:
            v, st = qstate(d, key)
            cells += f'<td><span class="cb {st or ""}">{icon("check", "ck") if st else ""}</span></td>'
        n = qcount(key)
        pct = round(100 * n / 7)
        pc = "#4f8a3a" if pct >= 70 else ("#d9822b" if pct >= 30 else "#c4473a")
        rows.append(f'<tr><td class="ql">{icon(ic)}{label}</td>{cells}<td>7</td><td>{n}</td>'
                    f'<td style="color:{pc}">{pct}%</td></tr>')
    for key, label, mn, ic in LOCKED:
        rows.append(f'<tr class="locked"><td class="ql">{icon(ic)}{label}</td>'
                    f'<td colspan="7" class="lk">{icon("lock")} unlocks week 2</td><td>–</td><td>–</td><td>–</td></tr>')
    pct_row = "".join(f"<td>{qpct(d)}</td>" for d in DAYS)
    xp_row = "".join(f'<td class="{"hot" if d["xp"] >= 500 else ""}">{d["xp"]}</td>' for d in DAYS)
    tot_pct = round(sum(qpct(d) for d in DAYS) / 7)
    # chart
    W, H = 70, 30
    bw = W / 7
    bars, hearts, pts = [], [], []
    for i, d in enumerate(DAYS):
        p = qpct(d) / 100
        blocks = int(round(p * 10))
        for b in range(blocks):
            bars.append(f'<rect x="{i * bw + 2:.2f}" y="{H - 2 - (b + 1) * 2.6:.2f}" width="{bw - 4:.2f}" height="2.2" '
                        f'fill="{"#4f8a3a" if b % 2 else "#6fae4f"}"/>')
        hy = H - 2 - d["score"] / 100 * 26
        hx = i * bw + bw / 2
        pts.append(f"{hx:.2f},{hy:.2f}")
        hearts.append(f'<g transform="translate({hx - 1.6:.2f},{hy - 1.4:.2f}) scale(.4)">'
                      + icon("heart").split(">", 1)[1].replace("</svg>", "") + "</g>")
    grid = "".join(f'<line x1="0" x2="{W}" y1="{H - 2 - f * 26:.1f}" y2="{H - 2 - f * 26:.1f}" stroke="#d8c7a6" stroke-width=".15"/>'
                   for f in (0, .5, 1))
    labels = "".join(f'<text x="{i * bw + bw / 2:.2f}" y="{H + 1.6}" text-anchor="middle">{d["d"]}</text>'
                     for i, d in enumerate(DAYS))
    chart = (f'<svg class="hchart" viewBox="-6 0 {W + 6} {H + 3}" shape-rendering="crispEdges">'
             f'{grid}<text x="-1" y="{H - 2 - 26 + 1}" text-anchor="end">100%</text>'
             f'<text x="-1" y="{H - 2 - 13 + 1}" text-anchor="end">50%</text>'
             f'<text x="-1" y="{H - 1}" text-anchor="end">0%</text>{"".join(bars)}'
             f'<polyline points="{" ".join(pts)}" fill="none" stroke="#c4473a" stroke-width=".3" stroke-dasharray=".8 .6"/>'
             f'{"".join(hearts)}{labels}</svg>')
    body = (hdr("leaf", "HABIT GRID", "10.1 → 10.7") +
            f'<table class="hg"><tr><th class="ql">QUESTS</th>{cols}<th>goal</th><th>done</th><th>%</th></tr>'
            f'{"".join(rows)}<tr class="pr"><td class="ql">daily %</td>{pct_row}<td colspan="3">{tot_pct}%</td></tr>'
            f'<tr class="xr"><td class="ql">{icon("gem")} XP</td>{xp_row}<td colspan="3">{TOTAL_XP:,}</td></tr></table>'
            f'{chart}<div class="legend">{icon("check")} = quest cleared · pale = half credit · '
            f'<span class="sw"></span> quests done % · {icon("heart")} sleep score (HP)</div>')
    return card(body, 4)


def p_journey():
    W, H = 70, 34
    bw = W / 7
    bars = []
    for i, d in enumerate(DAYS):
        n = d["xp"] // 50
        for b in range(n):
            col = "#2f5e9e" if d["xp"] >= 500 else ("#4a78c0" if b % 2 else "#6f97d6")
            bars.append(f'<rect x="{i * bw + 1.8:.2f}" y="{H - 3 - (b + 1) * 2.4:.2f}" width="{bw - 3.6:.2f}" height="2.1" fill="{col}"/>')
        bars.append(f'<text x="{i * bw + bw / 2:.2f}" y="{H - 4.2 - n * 2.4:.2f}" text-anchor="middle" class="v">{d["xp"]}</text>')
        bars.append(f'<text x="{i * bw + bw / 2:.2f}" y="{H}" text-anchor="middle">{d["d"]}</text>')
    grid = "".join(f'<line x1="0" x2="{W}" y1="{H - 3 - v / 50 * 2.4:.2f}" y2="{H - 3 - v / 50 * 2.4:.2f}" '
                   f'stroke="#d8c7a6" stroke-width=".15"/><text x="-1" y="{H - 2.4 - v / 50 * 2.4:.2f}" text-anchor="end">{v}</text>'
                   for v in (0, 200, 400, 600))
    chart = (f'<div class="box chartbox"><svg class="xchart" viewBox="-6 0 {W + 6} {H + 1}" shape-rendering="crispEdges">'
             f'{grid}{"".join(bars)}</svg></div>')
    src = sorted([(qxp(k), lab, ic) for k, lab, mn, ic in QUESTS], reverse=True)
    mx = src[0][0]
    srows = "".join(f'<div class="src">{icon(ic)}<span>{lab}</span><i><b style="width:{v / mx * 100:.0f}%"></b></i>'
                    f'<em>{v:,}</em></div>' for v, lab, ic in src)
    top = sorted(DAYS, key=lambda d: -d["xp"])[:3]

    def top_icons(d):
        return "".join(icon(dict((k, ic) for k, _, _, ic in QUESTS)[k]) for k in d["q"])
    trows = "".join(f'<div class="box topday"><b>{d["d"]} · +{d["xp"]} XP</b><span>{top_icons(d)}</span></div>' for d in top)
    body = (hdr("gem", "XP JOURNEY", f"LV 3 · {TOTAL_XP:,} XP") + chart +
            f'<div class="sub">XP BY SOURCE</div>{srows}<div class="sub">TOP XP DAYS</div>{trows}')
    return card(body, 5)


def p_board():
    rules = [
        ("shoe", "15k+ steps", "алхам", 150, 0), ("shoe", "10k+ steps", "алхам", 100, 6),
        ("apple", "≤2500 kcal · P150g+", "хоол", 200, 0), ("apple", "≤2700 kcal · P100g+", "хоол", 170, 2),
        ("apple", "food logged", "бичсэн", 50, 3),
        ("moon", "8h+ · score 80+ · before 12A", "3 of 3", 250, 0), ("moon", "sleep 2 of 3", "нойр", 150, 0),
        ("moon", "sleep 1 of 3", "нойр", 50, 2),
        ("dumbbell", "gym rated 9+", "gym", 250, 0), ("dumbbell", "gym session", "очсон", 200, 5),
        ("ball", "cardio · basketball · run", "спорт", 100, 2), ("flame", "burn 1000+ kcal", "шаталт", 100, 0),
        ("pullup", "30+ pull-ups", "pull-up", 50, 3), ("pushup", "100+ push-ups", "push-up", 50, 0),
        ("coin", "spent ≤ ¥80", "зарлага", 50, 2),
        ("bike", "bike 5km+", "дугуй · W2", 50, None), ("target", "focus 2h+ main work", "focus · W2", 200, None),
    ]
    rows = "".join(
        f'<div class="rule {"grey" if n == 0 else ""} {"new" if n is None else ""}">{icon(ic)}<span>{t} <small>{mn}</small></span>'
        f'<b>+{xp}</b><em>{"NEW" if n is None else ("–" if n == 0 else f"×{n}")}</em></div>'
        for ic, t, mn, xp, n in rules)
    lv = "".join(f'<div class="lvc {"on" if i == 3 else ""}"><span>LV{i}</span><b>{(i - 1) * 1000:,}</b></div>'
                 for i in range(1, 9))
    body = (hdr("notes", "XP QUEST BOARD", "action · тууштай байдал") + f'<div class="rules">{rows}</div>'
            f'<div class="legend">grey = not earned yet · ×n = times earned in week 1</div>'
            f'<div class="sub">LEVEL TABLE · 1000 XP = 1 LV</div><div class="lvt">{lv}</div>')
    return card(body, 6)


def sleep_track(d, tall=False):
    x0 = d["bed"] / 20 * 100
    x1 = d["wake"] / 20 * 100
    ticks = "".join(f'<span style="left:{h / 20 * 100}%">{lab}</span>'
                    for h, lab in [(0, "12A"), (4, "4A"), (8, "8A"), (12, "12P"), (16, "4P"), (20, "8P")])
    return (f'<div class="strack"><div class="ticks">{ticks}</div><div class="rail"><i class="night"></i>'
            f'<b style="left:{x0:.1f}%;width:{x1 - x0:.1f}%"></b></div>'
            f'<div class="bw"><span>{d["bed_s"]}</span><span>{d["wake_s"]}</span></div></div>')


def photos(d, maxh=22, maxw=74):
    n = d["photos"]
    rows = 1 if n <= 4 else 2
    cols = -(-n // rows)
    h = min(maxh / rows - 0.6, (maxw / max(cols, 2) - 0.8) * 0.75)
    w = h / 0.75
    imgs = "".join(f'<img src="photos/{d["d"]}-{i}.jpg" style="width:{w:.2f}mm;height:{h:.2f}mm">'
                   for i in range(1, n + 1))
    return f'<div class="strip" style="max-width:{cols * (w + 0.8):.2f}mm">{imgs}</div>'


def journal_html(s):
    for t in "gorb":
        s = s.replace(f"<{t}>", f'<span class="hl {t}">').replace(f"</{t}>", "</span>")
    return s


def p_day(d):
    gym = d["gym"]
    if gym:
        name, bg, fg = KIND[gym[0]]
        gchip = (f'<span class="chip" style="background:{bg};color:{fg}">{icon("dumbbell")}{gym[0].upper()} → '
                 f'p.{PAGE_NO[d["d"] + "x"]}</span>')
    elif d["sport"]:
        gchip = f'<span class="chip" style="background:#f6b77c;color:#8a3f12">{icon("ball")}{d["sport"].upper()}</span>'
    else:
        gchip = '<span class="chip" style="background:#e8dcc2;color:#7a6a55">REST DAY</span>'
    done = len(d["q"])
    pct = qpct(d)
    chips = "".join(f'<span class="pchip">{icon(ic)}{t}</span>' for ic, t in d["chips"])
    # tiles
    steps_frac = d["steps"] / 10
    sport_txt = {"cardio": "cardio after<br>back day", "basketball": "basketball<br>outside · сагс"}.get(d["sport"], "—<br>rest day" if not gym else "—<br>gym only")
    if d["kcal"]:
        p, c, f = d["macro"]
        kc = (f'<div class="tv">{d["kcal"]:,}<em>kcal</em></div><div class="tm">P {p}g · C {c}g · F {f}g</div>'
              f'{segbar(min(1, d["kcal"] / 2400), "#d9822b" if d["kcal"] > 2700 else "#5c9a3c", 10)}<div class="tm">line 2400</div>')
    else:
        kc = '<div class="tv">—</div><div class="tm">not logged</div>'
    gtxt = (f'<div class="tv">{gym[1]}<em>/10</em></div><div class="tm">{KIND[gym[0]][0].lower()} · '
            f'{SESSIONS[d["d"]]["sets"]} sets</div>') if gym else '<div class="tv">—</div><div class="tm">no gym</div>'
    qcells = ""
    for key, label, mn, ic in QUESTS:
        v, st = qstate(d, key)
        qcells += (f'<div class="qc"><span class="cb {st or ""}">{icon("check", "ck") if st else ""}</span>'
                   f'{icon(ic)}<small>{label.split()[-1] if key not in ("spend",) else "≤¥80"}</small></div>')
    xchips = "".join(f'<span class="xchip">{icon(dict((k, i) for k, _, _, i in QUESTS)[k])}+{qstate(d, k)[0]}</span>'
                     for k in d["q"])
    sc = d["score"]
    scol = "#4f8a3a" if sc >= 75 else ("#3d78b8" if sc >= 70 else "#d9822b")
    body = f'''
<div class="dtop"><span class="date">{d["d"]}<small>{d["dow"]}</small></span>
  <span class="chip q">{icon("check")}{done}/9</span>{gchip}<span class="xp">{icon("gem")}+{d["xp"]} XP</span></div>
{photos(d)}
<div class="jrow"><div class="box journal">{chips}{journal_html(d["journal"])}</div>
  <div class="box qring"><div class="ring" style="--p:{pct}"><b>{pct}%</b></div><small>quests</small></div></div>
<div class="box sleep"><div class="sl">{icon("moon")}SLEEP</div>{sleep_track(d)}
  <div class="sr"><b style="color:{scol}">{d["hrs"].replace("h", ":")}</b><span class="sc" style="border-color:{scol};color:{scol}">{sc}</span><small>score</small></div></div>
<div class="t3">
  <div class="box tt"><div class="tl2" style="color:#3d78b8">{icon("shoe")}STEPS</div><div class="tv">{fmt_k(d["steps"])}</div>
    {segbar(steps_frac, "#3d78b8", 10)}<div class="tm">goal 10k</div></div>
  <div class="box tt"><div class="tl2" style="color:#8a5cb8">{icon("flame")}BURN</div><div class="tv">{d["burn"]}<em>kcal</em></div>
    {segbar(d["burn"] / 700, "#8a5cb8", 10)}<div class="tm">goal 700 · quest 1000</div></div>
  <div class="box tt"><div class="tl2" style="color:#3a8f8a">{icon("ball")}SPORT</div><div class="tm big2">{sport_txt}</div></div>
</div>
<div class="t3">
  <div class="box tt"><div class="tl2" style="color:#c4473a">{icon("coin")}SPENT</div><div class="tv">¥{d["spent"]}</div>
    {segbar(min(1, d["spent"] / 160), "#5c9a3c" if d["spent"] <= 80 else "#c4473a", 10)}<div class="tm cn">{d["spent_items"]}</div></div>
  <div class="box tt"><div class="tl2" style="color:#d9822b">{icon("apple")}KCAL</div>{kc}</div>
  <div class="box tt"><div class="tl2" style="color:#b5652b">{icon("dumbbell")}GYM</div>{gtxt}</div>
</div>
<div class="box quests"><div class="qgrid">{qcells}</div>
  <div class="xrow">{xchips or '<span class="tm">rest · no XP today</span>'}<b>= {d["xp"]} XP</b></div></div>'''
    return card(body, PAGE_NO[d["d"]], "day")


def top_set(sets):
    def num(w):
        try:
            return float(str(w).replace("lb", "").split("+")[0])
        except ValueError:
            return 0

    def reps(r):
        return int(str(r).split("/")[0])
    if all(w == "BW" for w, _ in sets):
        return f"BW × {sum(reps(r) for _, r in sets)}"
    w, r = max(sets, key=lambda s: (num(s[0]), reps(s[1])))
    return f"{w} × {r}"


def p_ex(day):
    d = next(x for x in DAYS if x["d"] == day)
    s = SESSIONS[day]
    name, bg, fg = KIND[s["kind"]]
    boxes = []
    for nm, rating, sets in s["ex"]:
        rt = ""
        if rating:
            rc = "#4f8a3a" if rating >= 8.5 else ("#3d6fb0" if rating >= 7 else "#d9622b")
            rt = f'<i class="srt" style="background:{rc}">{rating}</i>'
        ws = "".join(f"<td>{w}</td>" for w, _ in sets)
        rs = "".join(f"<td>{r}R</td>" for _, r in sets)
        boxes.append(f'<div class="ex"><div class="exn" style="background:{bg};color:{fg}">{nm}{rt}</div>'
                     f'<table><tr class="w">{ws}</tr><tr class="rp">{rs}</tr></table></div>')
    rc = "#4f8a3a" if s["rating"] >= 8 else ("#3d6fb0" if s["rating"] >= 7 else "#d9622b")
    notes = "".join(f'<div class="nt {k}">{icon(k)}{t}</div>' for k, t in s["notes"])
    vs = s["vs"] or {}
    vrows = ""
    for nm, rating, sets in s["ex"]:
        if nm in vs:
            k, t = vs[nm]
            arrow = {"up": "↑", "dn": "↓", "eq": "="}[k]
            vrows += f'<tr><td>{nm}</td><td>{top_set(sets)}</td><td class="{k}">{arrow} {t}</td></tr>'
        else:
            vrows += f'<tr><td>{nm}</td><td>{top_set(sets)}</td><td class="first">first time this month</td></tr>'
    body = f'''
<div class="dtop"><span class="date">{d["d"]}<small>{d["dow"]}</small></span>
  <span class="chip" style="background:{bg};color:{fg}">{icon("dumbbell")}{name}</span>
  <span class="xp">{icon("gem")}+200 XP</span></div>
<div class="hdr ex-h">{icon("dumbbell")}<h1>EXERCISE</h1><span class="r">top kg · bottom reps · tag = set rating</span></div>
<div class="exs">{"".join(boxes)}</div>
<div class="rate"><div class="medal" style="background:{rc}"><b>{s["rating"]}</b><small>/10</small></div>
  <div><div>{s["sets"]} sets · {len(s["ex"])} exercises</div><div>{icon("flame")}burn <b>{s["burn"]}</b> kcal that day</div></div></div>
<div class="box notes"><div class="nh">{icon("notes")}NOTES</div>{notes}
  <div class="vh">TOP SET · vs LAST TIME</div><table class="vs">{vrows}</table></div>'''
    return card(body, PAGE_NO[day + "x"], "exday")


def p_moments(part):
    items = MOMENTS[(part - 1) * 4: part * 4]
    tilt = [-1.6, 1.2, 1.4, -1.1]
    pol = "".join(f'<div class="pol" style="transform:rotate({tilt[i]}deg)"><img src="photos/{f}.jpg">'
                  f'<div class="cap"><b>{dd}</b> {c}</div></div>' for i, (f, dd, c) in enumerate(items))
    body = hdr("camera", "BEST MOMENTS", f"{part} / 3") + f'<div class="pols">{pol}</div>'
    return card(body, PAGE_NO[f"m{part}"])


def p_totals():
    srows = "".join(f'<tr><td>{d["d"]}</td><td>{d["bed_s"]}</td><td>{d["wake_s"]}</td><td>{d["hrs"]}</td>'
                    f'<td class="{"good" if d["score"] >= 70 else "meh"}">{d["score"]}</td></tr>' for d in DAYS)
    mx = max(d["spent"] for d in DAYS)
    sp = "".join(f'<div class="srow"><span>{d["d"]}</span><i><b style="width:{d["spent"] / mx * 100:.0f}%;'
                 f'background:{"#5c9a3c" if d["spent"] <= 80 else "#c4473a"}"></b><s style="left:{80 / mx * 100:.0f}%"></s></i>'
                 f'<em>¥{d["spent"]}</em></div>' for d in DAYS)
    shops = [("西西弗", "books · café", 2, 106), ("好想来", "snacks", 4, 102), ("KFC", "food", 2, 59),
             ("话费", "phone", 1, 38), ("打车", "taxi", 1, 28)]
    shop = "".join(f'<div class="srow shop"><span>{n} <small>×{c}</small></span><i><b style="width:{v / 106 * 100:.0f}%;'
                   f'background:#b5652b"></b></i><em>¥{v}</em></div>' for n, k, c, v in shops)
    body = (hdr("chest", "WEEK 1 Σ", "totals") +
            f'<div class="tot2"><div class="box"><div class="nh">{icon("moon")}SLEEP LOG</div>'
            f'<table class="slog"><tr><th>day</th><th>bed</th><th>wake</th><th>hrs</th><th>sc</th></tr>{srows}'
            f'<tr class="avg"><td>Σ</td><td>05:46</td><td>13:06</td><td>7h12</td><td>68</td></tr></table></div>'
            f'<div class="col"><div class="box mini">{icon("shoe")}<small>STEPS</small><b>{STEPS:,}</b><em>avg 10.5k · 6 / 7 over 10k</em></div>'
            f'<div class="box mini">{icon("flame")}<small>BURN</small><b>{BURN:,}<em> kcal</em></b><em>avg 669 · peak 824</em></div>'
            f'<div class="box mini">{icon("apple")}<small>EATEN</small><b>2,953<em> /day</em></b><em>5 logged · P 121g</em></div></div></div>'
            f'<div class="box spent"><div class="nh">{icon("coin")}SPENT ¥{SPENT} · ≈ ¥103 / day · line = ¥80</div>{sp}</div>'
            f'<div class="box spent"><div class="nh">{icon("coin")}TOP PLACES · from the receipts listed</div>{shop}</div>')
    return card(body, PAGE_NO["tot"])


def p_achieve():
    ach = [("star", "Pull-ups 17 in one set", "10.6 · 17 + 13 = 30"), ("star", "Pec fly 145 lb × 8", "10.5 · up from 95 lb"),
           ("star", "Squat 110 × 6", "10.3 · leg day"), ("shoe", "Peak 12.8k steps", "10.3"),
           ("flame", "Peak burn 824 kcal", "10.3"), ("moon", "Best sleep score 77", "10.2 · 8h23"),
           ("coin", "Cheapest day ¥35", "10.1"), ("pullup", "30 pull-ups × 3 days", "10.1 · 10.5 · 10.6")]
    a = "".join(f'<div class="box ach">{icon(i)}<div><b>{t}</b><small>{s}</small></div></div>' for i, t, s in ach)
    nums = [("gem", f"{TOTAL_XP:,}", "XP earned"), ("shoe", "73,577", "steps"), ("flame", f"{BURN:,}", "kcal burned"),
            ("coin", "¥718", "spent"), ("dumbbell", "5", "gym sessions"), ("ball", "2", "sport days"),
            ("pushup", "200", "push-ups"), ("camera", "30", "snapshots")]
    n = "".join(f'<div class="box num">{icon(i)}<b>{v}</b><small>{l}</small></div>' for i, v, l in nums)
    body = (hdr("trophy", "WEEK 1 Σ", "achievements") + f'<div class="achs">{a}</div>'
            f'<div class="sub">WEEK IN NUMBERS</div><div class="nums">{n}</div>'
            f'<div class="bl"><div class="box best">{icon("heart")}<small>BEST DAYS (XP)</small><b>10.6 +570 · 10.2 +500</b></div>'
            f'<div class="box best">{icon("leaf")}<small>LOWEST</small><b>10.4 · rest</b></div></div>')
    return card(body, PAGE_NO["ach"])


def p_next():
    qs = [("shoe", "Walk 10k steps a day", "W1: 6 / 7 days ✓ keep it", 100),
          ("apple", "≤2500 kcal + 150g protein", "W1: 0 days · closest 10.6", 200),
          ("moon", "Asleep before 12A", "W1: 0 / 7 · avg 05:46", 150),
          ("dumbbell", "Gym 5 sessions", "rate one 9+ → +250", 200),
          ("ball", "Sport 2+ days", "cardio · basketball · run", 100),
          ("flame", "Burn 1000+ kcal once", "W1 peak 824", 100),
          ("pushup", "100 push-ups in a day", "W1 best 60", 50),
          ("dumbbell", "Leg day + hamstring & calf", "fix from 10.3 note", 200),
          ("coin", "Spend ≤ ¥80 · 4 days", "W1: 2 days", 50),
          ("bike", "Bike 5km+", "NEW quest", 50),
          ("target", "Focus 2h+ on main work", "NEW quest", 200)]
    rows = "".join(f'<div class="box nq">{icon(i)}<div><b>{t}</b><small class="{"new" if "NEW" in s else ""}">{s}</small></div>'
                   f'<em>+{x}</em><span class="cb"></span></div>' for i, t, s, x in qs)
    body = (hdr("leaf", "WEEK 2 QUESTS", "next chapter") +
            f'<div class="box lvbar">{icon("gem")}LV 3 → LV 4 · 360 XP to go · that is about 52 XP a day</div>{rows}')
    return card(body, PAGE_NO["next"])


def p_clear():
    body = f'''
<div class="cover-art clear">{scene("dusk")}
  <div class="sign blue"><b>WEEK 1</b><b>CLEARED!</b></div></div>
<div class="grid2 cl">
  <div class="box stat">{icon("gem")}<b>{TOTAL_XP:,} XP · LV 3</b></div>
  <div class="box stat">{icon("check")}<b>40% quests / day</b></div>
  <div class="box stat">{icon("dumbbell")}<b>5 gym sessions</b></div>
  <div class="box stat">{icon("shoe")}<b>73,577 steps</b></div>
</div>
<div class="quote">“Амралт дууслаа даа.” — 10.7</div>
<div class="cnote">to be continued in week 2 …</div>'''
    return card(body, PAGE_NO["clear"], "cover")


# what was missing: earned XP vs the most each quest could pay this week
LACK_MAX = [("sleep", 1750, "250 × 7 nights"), ("food", 1400, "200 × 7 days"), ("burn", 700, "100 × 7"),
            ("sport", 700, "100 × 7"), ("steps", 1050, "150 × 7"), ("push", 350, "50 × 7"),
            ("gym", 1250, "250 × 5 sessions"), ("spend", 350, "50 × 7"), ("pull", 350, "50 × 7")]


def p_lack1():
    lab = {k: (l, ic) for k, l, _, ic in QUESTS}
    rows, tot_max = [], 0
    for k, mx, note in sorted(LACK_MAX, key=lambda r: -(r[1] - qxp(r[0]))):
        got = qxp(k)
        tot_max += mx
        l, ic = lab[k]
        rows.append(f'<div class="lrow">{icon(ic)}<span>{l}</span><i><b style="width:{got / mx * 100:.0f}%"></b></i>'
                    f'<em>{got:,}<small> / {mx:,}</small></em><strong>−{mx - got:,}</strong></div>')
    pct = round(100 * TOTAL_XP / tot_max)
    gaps = [
        ("moon", "SLEEP", "−1,650 XP", "avg bed 05:46 · before 12A 0 / 7 · score 80+ 0 / 7 (best 77) · 8h+ only 2 / 7"),
        ("apple", "FOOD", "−910 XP", "avg 2,953 kcal vs 2,400 line · ≤2500 + P150g 0 days · 10.4, 10.5 not logged · 10.1 = 4,372"),
        ("flame", "BURN & PUSH-UPS", "−1,050 XP", "1000 kcal never (peak 824) · 100 push-ups never (best 60)"),
    ]
    g = "".join(f'<div class="box gap">{icon(i)}<div><b>{t} <em>{x}</em></b><small>{s}</small></div></div>'
                for i, t, x, s in gaps)
    body = (hdr("target", "WHAT I LACKED", "1 / 2 · XP left on the table") +
            f'<div class="box lackbox"><div class="lhead"><div class="ring" style="--p:{pct}"><b>{pct}%</b></div>'
            f'<div><b>{TOTAL_XP:,} of {tot_max:,} XP</b><small>earned vs the most the quest board could pay in week 1</small></div></div>'
            f'{"".join(rows)}<div class="legend"><span class="sw"></span> earned · empty = missed · red = XP lost</div></div>'
            f'<div class="sub">3 BIGGEST GAPS</div>{g}')
    return card(body, PAGE_NO["lack1"])


def p_lack2():
    items = [
        ("moon", "Asleep before 12A", 0, 7, "earliest 03:15 (10.5)"),
        ("moon", "Sleep score 80+", 0, 7, "best 77 (10.2)"),
        ("moon", "8h+ sleep", 2, 7, "10.2 · 10.5"),
        ("apple", "Food logged", 5, 7, "missed 10.4 · 10.5"),
        ("apple", "Protein 150g+", 2, 7, "10.1 180g · 10.6 156g"),
        ("apple", "Under 2,700 kcal", 3, 7, "10.3 · 10.6 · 10.7"),
        ("flame", "Burn 1000+ kcal", 0, 7, "peak 824 (10.3)"),
        ("pushup", "100 push-ups", 0, 7, "best 60 · total 200"),
        ("coin", "Spend ≤ ¥80", 2, 7, "avg ¥103 / day"),
        ("dumbbell", "Gym rated 9+", 0, 5, "best 8 (10.1 · 10.5)"),
        ("pullup", "30 pull-ups on gym day", 3, 5, "10.2 = 27 · 10.3 = 0"),
        ("ball", "Sport day", 2, 7, "cardio 10.2 · basket 10.7"),
        ("shoe", "10k steps", 6, 7, "10.4 = 4.6k"),
    ]
    rows = "".join(
        f'<div class="lk2">{icon(i)}<span>{t}<small>{s}</small></span>'
        f'<i>{"".join(f"<b class=on></b>" if j < n else "<b></b>" for j in range(m))}</i>'
        f'<em class="{"zero" if n == 0 else ("ok" if n / m >= .7 else "")}">{n}/{m}</em></div>'
        for i, t, n, m, s in items)
    fixes = [("moon", "Lights out before 2A first, then 12A · even 1 of 3 = +50 a night"),
             ("apple", "Log every meal · hit 150g protein under 2,500 kcal = +200"),
             ("dumbbell", "Legs need hamstring + calf · aim one session rated 9+"),
             ("pushup", "Spread push-ups: 4 × 25 through the day = 100")]
    f = "".join(f'<div class="fix">{icon(i)}{t}</div>' for i, t in fixes)
    body = (hdr("target", "WHAT I LACKED", "2 / 2 · days hit") + f'<div class="box lk2box">{rows}</div>'
            f'<div class="box fixbox"><div class="nh">{icon("pen")}FIX NEXT WEEK</div>{f}</div>')
    return card(body, PAGE_NO["lack2"])


def p_log():
    days = [("10.8", "THU"), ("10.9", "FRI"), ("10.10", "SAT"), ("10.11", "SUN"), ("10.12", "MON"),
            ("10.13", "TUE"), ("10.14", "WED")]
    keys = QUESTS + LOCKED
    head = "".join(f"<th>{icon(ic)}</th>" for _, _, _, ic in keys)
    rows = "".join(f'<tr><td class="dd">{d}<small>{w}</small></td>' + "".join('<td><span class="cb"></span></td>' for _ in keys)
                   + '<td class="xpw"></td></tr><tr class="nl"><td></td><td colspan="12"></td></tr>' for d, w in days)
    body = (hdr("notes", "WEEK 2 XP LOG", "write it down") +
            f'<table class="wlog"><tr><th>day</th>{head}<th>XP</th></tr>{rows}</table>'
            f'<div class="box wsum"><span>Σ week 2</span><i></i><span>XP · LV 3 → 4 needs 360</span></div>')
    return card(body, PAGE_NO["log"])


# page order
ORDER = ["cover", "avg1", "avg2", "habits", "journey", "board"]
for d in DAYS:
    ORDER.append(d["d"])
    if d["d"] in SESSIONS:
        ORDER.append(d["d"] + "x")
ORDER += ["m1", "m2", "m3", "tot", "ach", "lack1", "lack2", "next", "log", "clear"]
for i, k in enumerate(ORDER, 1):
    PAGE_NO[k] = i


def build_cards():
    out = []
    for k in ORDER:
        if k == "cover":
            out.append(p_cover())
        elif k == "avg1":
            out.append(p_avg1())
        elif k == "avg2":
            out.append(p_avg2())
        elif k == "habits":
            out.append(p_habits())
        elif k == "journey":
            out.append(p_journey())
        elif k == "board":
            out.append(p_board())
        elif k.endswith("x"):
            out.append(p_ex(k[:-1]))
        elif k[0] == "1":
            out.append(p_day(next(d for d in DAYS if d["d"] == k)))
        elif k in ("m1", "m2", "m3"):
            out.append(p_moments(int(k[1])))
        elif k == "tot":
            out.append(p_totals())
        elif k == "ach":
            out.append(p_achieve())
        elif k == "lack1":
            out.append(p_lack1())
        elif k == "lack2":
            out.append(p_lack2())
        elif k == "log":
            out.append(p_log())
        elif k == "next":
            out.append(p_next())
        elif k == "clear":
            out.append(p_clear())
    return out


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Pixelify+Sans:wght@400;500;600;700'
         '&family=Press+Start+2P&family=Nunito:wght@500;600;700;800&family=Noto+Sans+SC:wght@500;700&display=swap" rel="stylesheet">')


SLOT_X = (18, 110)   # A4 = 210 × 297 mm, two 82 mm cards + 10 mm gutter
SLOT_Y = (32, 160)   # two 116 mm cards + 12 mm gutter


def main():
    css = (HERE / "tn.css").read_text()
    cards = build_cards()
    assert len(cards) % 4 == 0, len(cards)
    head = f'<!doctype html><html lang="mn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{FONTS}'
    (HERE / "week1-tn.html").write_text(
        f'{head}<title>October W1 TN</title><style>{css}\n@page{{size:82mm 116mm;margin:0}}</style></head>'
        f'<body class="digital">{"".join(cards)}</body></html>')
    n = len(cards) // 4
    sheets = []
    for s in range(n, 0, -1):  # reversed: last sheet first
        p = (s - 1) * 4
        slots, marks = "", ""
        for i in range(4):
            x, y = SLOT_X[i % 2], SLOT_Y[i // 2]
            slots += f'<div class="slot" style="left:{x}mm;top:{y}mm">{cards[p + i]}</div>'
            for yy in (y, y + 116):  # horizontal ticks left / right of the card
                marks += f'<i class="cm" style="left:{x - 5}mm;top:{yy}mm;width:3mm;height:0"></i>'
                marks += f'<i class="cm" style="left:{x + 84}mm;top:{yy}mm;width:3mm;height:0"></i>'
            for xx in (x, x + 82):  # vertical ticks above / below the card
                marks += f'<i class="cm" style="left:{xx}mm;top:{y - 5}mm;width:0;height:3mm"></i>'
                marks += f'<i class="cm" style="left:{xx}mm;top:{y + 118}mm;width:0;height:3mm"></i>'
        sheets.append(f'<div class="sheet"><div class="shh">sheet {s}/{n} · p.{p + 1}–{p + 4} · print 100% · card 82×116 mm</div>'
                      f'<div class="ruler"><i></i><span>this bar = 90 mm (check scale)</span></div>{marks}{slots}</div>')
    (HERE / "week1-tn-print.html").write_text(
        f'{head}<title>October W1 TN print</title><style>{css}\n@page{{size:A4;margin:0}}</style></head>'
        f'<body class="print">{"".join(sheets)}</body></html>')
    print(f"{len(cards)} cards · {n} sheets")


if __name__ == "__main__":
    main()
