#!/usr/bin/env python3
"""Weekly traveler's-notebook cards (82×116 mm) built from one week's JSON.

usage:  python3 build.py path/to/weekN.json [--pdf]

Scores every day against the XP quest rules, works out the weekly stats and
writes two HTML files next to the JSON:
  <name>-tn.html        one card per page (screen / digital PDF)
  <name>-tn-print.html  4 cards per A4 sheet, crop marks, sheets in reverse order
--pdf also prints both to PDF through print.js (needs Playwright).
"""
import json, math, pathlib, random, subprocess, sys
from statistics import mean

HERE = pathlib.Path(__file__).parent

# ───────────────────────────── quest rules ─────────────────────────────
QUESTS = [  # key, label, mongolian, icon
    ("steps", "10k steps", "алхам", "shoe"),
    ("food", "food", "хоол", "apple"),
    ("sleep", "sleep", "нойр", "moon"),
    ("gym", "gym", "gym", "dumbbell"),
    ("sport", "sport", "спорт", "ball"),
    ("burn", "1000 burn", "шаталт", "flame"),
    ("pull", "30 pull-up", "pull-up", "pullup"),
    ("push", "100 push-up", "push-up", "pushup"),
    ("spend", "≤ ¥80", "зарлага", "coin"),
    ("bike", "bike 5km+", "дугуй", "bike"),
    ("focus", "focus 2h+", "focus", "target"),
]
QLABEL = {k: l for k, l, _, _ in QUESTS}
QICON = {k: i for k, _, _, i in QUESTS}

TIERS = [  # quest, tier, rule text, mongolian, xp, half credit?
    ("steps", "15k", "15k+ steps", "алхам", 150, False),
    ("steps", "10k", "10k+ steps", "алхам", 100, False),
    ("food", "lean", "≤2500 kcal · P150g+", "хоол", 200, False),
    ("food", "ok", "≤2700 kcal · P100g+", "хоол", 170, False),
    ("food", "log", "food logged", "бичсэн", 50, True),
    ("sleep", "3", "8h+ · score 80+ · before 12A", "3 of 3", 250, False),
    ("sleep", "2", "sleep 2 of 3", "нойр", 150, True),
    ("sleep", "1", "sleep 1 of 3", "нойр", 50, True),
    ("gym", "9", "gym rated 9+", "gym", 250, False),
    ("gym", "go", "gym session", "очсон", 200, False),
    ("sport", "x", "cardio · basketball · run", "спорт", 100, False),
    ("burn", "x", "burn 1000+ kcal", "шаталт", 100, False),
    ("pull", "x", "30+ pull-ups", "pull-up", 50, False),
    ("push", "x", "100+ push-ups", "push-up", 50, False),
    ("spend", "x", "spent ≤ ¥80", "зарлага", 50, False),
    ("bike", "x", "bike 5km+", "дугуй", 50, False),
    ("focus", "x", "focus 2h+ main work", "focus", 200, False),
]
TIER = {(q, t): (xp, half) for q, t, _, _, xp, half in TIERS}
TOP_XP = {}
for q, t, _, _, xp, _ in TIERS:
    TOP_XP[q] = max(TOP_XP.get(q, 0), xp)
# the XP a normal "done" day pays, used for next-week targets and the day's "missed" tile
MAIN_XP = {"steps": 100, "food": 200, "sleep": 250, "gym": 200, "sport": 100, "burn": 100,
           "pull": 50, "push": 50, "spend": 50, "bike": 50, "focus": 200}
KIND = {"push": ("PUSH DAY", "#f3c24f", "#7a5410"), "pull": ("PULL DAY", "#8fc0ea", "#1f4f86"),
        "leg": ("LEG DAY", "#f6b77c", "#8a3f12"), "upper": ("UPPER DAY", "#c7a6e6", "#4b2c73"),
        "full": ("FULL BODY", "#b8dca0", "#2f5a22")}


# ───────────────────────────── load + score ─────────────────────────────
def mins(hm):  # "7h12" → 432
    h, m = hm.split("h")
    return int(h) * 60 + int(m or 0)


def hm(m):
    return f"{int(m) // 60}h{int(round(m)) % 60:02d}"


def clock(s):  # "05:46" → 5.77 h; evening times stay < 24, after-midnight times are pushed past 24
    h, m = map(int, s.split(":"))
    v = h + m / 60
    return v + 24 if v < 12 else v


def plain(s):  # "13:05" → 13.08, no day shift
    h, m = map(int, s.split(":"))
    return h + m / 60


def clock_s(v):
    v %= 24
    return f"{int(v):02d}:{int(round((v % 1) * 60)) % 60:02d}"


def reps_of(r):
    return int(str(r).split("/")[0])


def bw_reps(sess, name):
    if not sess:
        return 0
    return sum(reps_of(r) for e in sess["exercises"] if e["name"] == name for w, r in e["sets"])


def load(path):
    W = json.loads(pathlib.Path(path).read_text())
    W["dir"] = pathlib.Path(path).resolve().parent
    W["stem"] = pathlib.Path(path).stem
    locked = set(W.get("locked_quests", []))
    W["active"] = [k for k, *_ in QUESTS if k not in locked]
    W["locked"] = [k for k, *_ in QUESTS if k in locked]
    for d in W["days"]:
        s = W["sessions"].get(d["date"])
        d["sess"] = s
        d["pull"] = d.get("pullups", bw_reps(s, "Pull-ups"))
        d["push"] = d.get("pushups", bw_reps(s, "Push-ups"))
        d["hit"] = score_day(d, s, W)
        d["xp"] = sum(TIER[(q, t)][0] for q, t in d["hit"].items())
        d["pct"] = round(100 * len(d["hit"]) / len(W["active"]))
    return W


def score_day(d, s, W):
    g = W["goals"]
    hit = {}

    def put(q, t):
        if q in W["active"]:
            hit[q] = t
    if d["steps"] >= 15000:
        put("steps", "15k")
    elif d["steps"] >= 10000:
        put("steps", "10k")
    if d.get("kcal"):
        p = d["macros"][0]
        if d["kcal"] <= 2500 and p >= 150:
            put("food", "lean")
        elif d["kcal"] <= 2700 and p >= 100:
            put("food", "ok")
        else:
            put("food", "log")
    n = (mins(d["sleep"]) >= 480) + (d["sleep_score"] >= 80) + (clock(d["bed"]) <= 24)
    if n:
        put("sleep", str(n))
    if s:
        put("gym", "9" if s["rating"] >= 9 else "go")
    if d.get("sport"):
        put("sport", "x")
    if d["burn"] >= 1000:
        put("burn", "x")
    if d["pull"] >= 30:
        put("pull", "x")
    if d["push"] >= 100:
        put("push", "x")
    if d["spent"] <= g["spend_per_day"]:
        put("spend", "x")
    if d.get("bike_km", 0) >= 5:
        put("bike", "x")
    if d.get("focus_h", 0) >= 2:
        put("focus", "x")
    return hit


def stats(W):
    D, g = W["days"], W["goals"]
    n = len(D)
    S = {"n": n}
    S["xp"] = sum(d["xp"] for d in D)
    total = W.get("xp_before_week", 0) + S["xp"]
    S["lv"], S["into"] = total // 1000 + 1, total % 1000
    S["need"] = 1000 - S["into"]
    phone = W.get("totals_from_phone", {})
    S["steps_tot"] = phone.get("steps", sum(d["steps"] for d in D))
    S["spent_tot"] = phone.get("spent", sum(d["spent"] for d in D))
    S["steps_avg"] = round(S["steps_tot"] / n)
    S["spent_avg"] = round(S["spent_tot"] / n)
    S["burn_tot"] = sum(d["burn"] for d in D)
    S["burn_avg"] = round(S["burn_tot"] / n)
    S["sleep_avg"] = mean(mins(d["sleep"]) for d in D)
    S["score_avg"] = round(mean(d["sleep_score"] for d in D))
    S["bed_avg"] = clock_s(mean(clock(d["bed"]) for d in D))
    S["wake_avg"] = clock_s(mean(plain(d["wake"]) for d in D))
    logged = [d for d in D if d.get("kcal")]
    S["logged"] = logged
    S["kcal_avg"] = round(mean(d["kcal"] for d in logged)) if logged else 0
    S["mac_avg"] = [round(mean(d["macros"][i] for d in logged)) for i in range(3)] if logged else [0, 0, 0]
    S["sessions"] = [d for d in D if d["sess"]]
    S["rating_avg"] = round(mean(d["sess"]["rating"] for d in S["sessions"]), 1) if S["sessions"] else 0
    S["pct_avg"] = round(mean(d["pct"] for d in D))
    best = max(D, key=lambda d: d["sleep_score"])
    S["best_sleep"] = best
    return S


def days_where(W, f):
    return [d for d in W["days"] if f(d)]


def dates(ds, empty="none"):
    return " · ".join(d["date"] for d in ds) or empty


def qcount(W, q):
    return sum(1 for d in W["days"] if q in W["active"] and q in d["hit"])


def qxp(W, q):
    return sum(TIER[(q, d["hit"][q])][0] for d in W["days"] if q in d["hit"])


def qmax(W, q):
    times = W["goals"]["gym_sessions"] if q == "gym" else len(W["days"])
    return TOP_XP[q] * times


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
W, S, PAGE_NO = {}, {}, {}
MONTH = ""
GOOD, MID, BAD = "#4f8a3a", "#d9822b", "#c4473a"


def segbar(frac, color, segs=10):
    frac = max(0.0, min(1.0, frac))
    full = frac * segs
    cells = []
    for i in range(segs):
        f = max(0.0, min(1.0, full - i))
        cells.append(f'<i style="background:linear-gradient(90deg,{color} {f * 100:.0f}%,transparent {f * 100:.0f}%)"></i>')
    return f'<span class="seg">{"".join(cells)}</span>'


def state(d, q):
    t = d["hit"].get(q)
    if t is None:
        return 0, None
    xp, half = TIER[(q, t)]
    return xp, "half" if half else "full"


def checkbox(st):
    return f'<span class="cb {st or ""}">{icon("check", "ck") if st else ""}</span>'


def sections():
    D = W["days"]
    return [("1", "ДҮГНЭЛТ", "SUMMARY", "glance", "board", "week at a glance · averages · habit grid · XP rules"),
            ("2", "ӨДӨР БҮР", "DAY BY DAY", D[0]["date"], D[-1]["date"], "day card + gym card for each day"),
            ("3", "ДУТСАН ЗҮЙЛ", "WHAT I LACKED", "lack1", "next", "XP left on the table · days hit · next week")]


def section_of(page):
    for n, mn, en, a, z, _ in sections():
        if PAGE_NO[a] <= page <= PAGE_NO[z]:
            return f"{n} · {mn}"
    return ""


def card(body, key, cls=""):
    page = PAGE_NO[key]
    sec = section_of(page)
    left = f"{MONTH} · {sec}" if sec else MONTH
    return (f'<section class="card {cls}">{body}'
            f'<div class="foot"><span>{left}</span><span>{page}</span></div></section>')


def hdr(ic, title, right=""):
    return f'<div class="hdr">{icon(ic)}<h1>{title}</h1><span class="r">{right}</span></div>'


def k(v):
    return f"{v / 1000:.1f}k"


def wk():
    return f'W{W["week"]}'


# ───────────────────────────── 1 · summary ─────────────────────────────
def p_cover():
    rows = ""
    for n, mn, en, a, z, what in sections():
        rows += (f'<div class="toc"><span class="tn">{n}</span><div><b>{mn} <small>{en}</small></b>'
                 f'<em>{what}</em></div><span class="tp">p.{PAGE_NO[a]}–{PAGE_NO[z]}</span></div>')
        if n == "2":
            rows += '<div class="tocdays">' + "".join(
                f'<span>{d["date"]}<small>p.{PAGE_NO[d["date"]]}</small></span>' for d in W["days"]) + "</div>"
    body = f'''
<div class="cover-art">{scene("day")}
  <div class="sign"><b>{W["month"]}</b><span>WEEK {W["week"]} · {W["range"]}</span></div>
</div>
<div class="subt">{icon("notes")} WEEKLY QUEST LOG · CHAPTER {W["chapter"]} · WEEK {W["week"]}</div>
<div class="box lv">
  <div class="lvbadge">LV {S["lv"]}</div>
  <div class="lvinfo"><div class="big">{S["xp"]:,} XP <em class="mut">this week</em></div>
    <div class="mut">avg {S["xp"] // S["n"]} / day · 1000 XP = 1 LV</div>
    {segbar(S["into"] / 1000, "#4a78c0", 20)}
    <div class="mut">{S["into"]} / 1,000 → LV {S["lv"] + 1}</div></div>
</div>
<div class="box tocbox"><div class="nh">{icon("notes")}CONTENTS</div>{rows}</div>'''
    return card(body, "cover", "cover")


def p_glance():
    D, g = W["days"], W["goals"]

    def cell(v, cls):
        return f'<td class="{cls}">{v}</td>'

    def lvl(ok, mid):
        return "g" if ok else ("m" if mid else "b")

    rows = []

    def row(ic, label, vals, avg):
        rows.append(f'<tr><th>{icon(ic)}{label}</th>{"".join(vals)}<td class="av">{avg}</td></tr>')

    row("gem", "XP", [cell(d["xp"], lvl(d["xp"] >= 400, d["xp"] >= 200)) for d in D], S["xp"] // S["n"])
    row("check", "quests", [cell(f'{d["pct"]}%', lvl(d["pct"] >= 50, d["pct"] >= 30)) for d in D], f'{S["pct_avg"]}%')
    row("shoe", "steps", [cell(k(d["steps"]), lvl(d["steps"] >= 10000, d["steps"] >= 7500)) for d in D], k(S["steps_avg"]))
    row("flame", "burn", [cell(d["burn"], lvl(d["burn"] >= g["burn_per_day"], d["burn"] >= 550)) for d in D], S["burn_avg"])
    row("moon", "sleep", [cell(d["sleep"], lvl(mins(d["sleep"]) >= 480, mins(d["sleep"]) >= 420)) for d in D], hm(S["sleep_avg"]))
    row("heart", "score", [cell(d["sleep_score"], lvl(d["sleep_score"] >= 80, d["sleep_score"] >= 70)) for d in D], S["score_avg"])
    row("sun", "asleep", [cell(d["bed"], lvl(clock(d["bed"]) <= 24, clock(d["bed"]) <= 26)) for d in D], S["bed_avg"])
    row("apple", "kcal", [cell(f'{d["kcal"]:,}', lvl(d["kcal"] <= g["kcal_line"], d["kcal"] <= 2700)) if d.get("kcal")
                          else cell("—", "n") for d in D], f'{S["kcal_avg"]:,}')
    row("apple", "protein", [cell(f'{d["macros"][0]}g', lvl(d["macros"][0] >= g["protein_g"], d["macros"][0] >= 100))
                             if d.get("kcal") else cell("—", "n") for d in D], f'{S["mac_avg"][0]}g')
    row("coin", "spent", [cell(f'¥{d["spent"]}', lvl(d["spent"] <= g["spend_per_day"], d["spent"] <= 120)) for d in D],
        f'¥{S["spent_avg"]}')
    tr = []
    for d in D:
        s = d["sess"]
        if s:
            name, bg, fg = KIND[s["kind"]]
            tr.append(f'<td class="kd" style="background:{bg};color:{fg}">{s["kind"].upper()}<small>{s["rating"]}/10</small></td>')
        elif d.get("sport"):
            tr.append(f'<td class="kd" style="background:#f9d2ad;color:#8a3f12">{d["sport"][:6].upper()}</td>')
        else:
            tr.append('<td class="kd n">rest</td>')
    rows.append(f'<tr><th>{icon("dumbbell")}training</th>{"".join(tr)}<td class="av">{len(S["sessions"])}×</td></tr>')
    head = "".join(f'<td>{d["date"]}<small>{d["dow"]}</small></td>' for d in D)
    best = max(D, key=lambda d: d["xp"])
    low = min(D, key=lambda d: d["xp"])
    steady = max(W["active"], key=lambda q: qcount(W, q))
    weak = min((q for q in W["active"] if q != "gym"), key=lambda q: qxp(W, q) - qmax(W, q))
    body = (hdr("calendar", "WEEK AT A GLANCE", W["range"]) +
            f'<table class="gl"><tr class="gh"><th></th>{head}<td class="av">avg</td></tr>{"".join(rows)}</table>'
            f'<div class="legend"><i class="lg g"></i>on goal · <i class="lg m"></i>close · <i class="lg b"></i>off · — not logged</div>'
            f'<div class="glb">'
            f'<div class="box best">{icon("star")}<small>BEST DAY</small><b>{best["date"]} · +{best["xp"]} XP</b></div>'
            f'<div class="box best">{icon("leaf")}<small>LOWEST</small><b>{low["date"]} · +{low["xp"]} XP</b></div>'
            f'<div class="box best">{icon("check")}<small>MOST STEADY</small><b>{QLABEL[steady]} {qcount(W, steady)}/{S["n"]}</b></div>'
            f'<div class="box best">{icon("target")}<small>WEAKEST</small><b>{QLABEL[weak]} −{qmax(W, weak) - qxp(W, weak):,} XP</b></div>'
            f'</div>')
    return card(body, "glance")


def tile(color, ic, title, big, unit, lines, frac, pct_label):
    return f'''<div class="tile"><div class="th" style="background:{color}">{icon(ic)}{title}</div>
<div class="tb"><div class="big">{big}<em>{unit}</em></div>{lines}
<div class="tbar">{segbar(frac, color, 10)}<b>{pct_label}</b></div></div></div>'''


def tl(a, b):
    return f'<div class="tl"><u>{a}</u></div><div class="tl">{b}</div>'


def pct(f):
    return f"{round(f * 100)}%"


def p_avg():
    D, g, n = W["days"], W["goals"], S["n"]
    n7 = len(days_where(W, lambda d: mins(d["sleep"]) >= 420))
    nb = len(days_where(W, lambda d: clock(d["bed"]) <= 24))
    n10 = len(days_where(W, lambda d: d["steps"] >= 10000))
    nburn = days_where(W, lambda d: d["burn"] >= g["burn_per_day"])
    peak = max(D, key=lambda d: d["burn"])
    nsp = len(days_where(W, lambda d: d["spent"] <= g["spend_per_day"]))
    kinds = {}
    for d in S["sessions"]:
        kinds[d["sess"]["kind"]] = kinds.get(d["sess"]["kind"], 0) + 1
    bestq = max(d["pct"] for d in D)
    lowq = min(D, key=lambda d: d["pct"])
    bs = S["best_sleep"]
    t = [
        tile("#5c9a3c", "moon", "SLEEP / NIGHT", hm(S["sleep_avg"]).replace("h", "h "), "m",
             tl(f'sleep score {S["score_avg"]} / 100', f'best {bs["sleep_score"]} ({bs["date"]}) · 7h+ {n7}/{n}'),
             S["sleep_avg"] / 480, pct(S["sleep_avg"] / 480)),
        tile("#4a5aa8", "sun", "BED → WAKE", f'{S["bed_avg"]}→{S["wake_avg"]}', "",
             tl("avg asleep → wake up", f"asleep before 12A · {nb}/{n}"), nb / n, pct(nb / n)),
        tile("#3d78b8", "shoe", "STEPS / DAY", f'{S["steps_avg"]:,}', "",
             tl("GOAL 10,000 / day", f'10k+ {n10}/{n} · total {S["steps_tot"]:,}'),
             S["steps_avg"] / 10000, pct(S["steps_avg"] / 10000)),
        tile("#8a5cb8", "flame", "BURN / DAY", S["burn_avg"], "kcal",
             tl(f'GOAL {g["burn_per_day"]} kcal / day', f'{g["burn_per_day"]}+ {len(nburn)}/{n} · peak {peak["burn"]} ({peak["date"]})'),
             S["burn_avg"] / g["burn_per_day"], pct(S["burn_avg"] / g["burn_per_day"])),
        tile("#c4473a", "coin", "SPENT / DAY", f'¥{S["spent_avg"]}', "",
             tl(f'GOAL ≤ ¥{g["spend_per_day"]} / day', f'within · {nsp}/{n} · total ¥{S["spent_tot"]:,}'),
             min(1, g["spend_per_day"] / S["spent_avg"]), pct(min(1, g["spend_per_day"] / S["spent_avg"]))),
        tile("#d9822b", "apple", "CALORIES / DAY", f'{S["kcal_avg"]:,}', "kcal",
             tl(f'LINE {g["kcal_line"]:,} · {len(S["logged"])}/{n} logged',
                f'P {S["mac_avg"][0]}g · C {S["mac_avg"][1]}g · F {S["mac_avg"][2]}g'),
             min(1, g["kcal_line"] / max(S["kcal_avg"], 1)), pct(min(1, g["kcal_line"] / max(S["kcal_avg"], 1)))),
        tile("#b5652b", "dumbbell", "GYM", len(S["sessions"]), f'/ {g["gym_sessions"]}',
             tl(f'avg rating {S["rating_avg"]} / 10', " · ".join(f"{k_} ×{v}" for k_, v in kinds.items())),
             len(S["sessions"]) / g["gym_sessions"], pct(len(S["sessions"]) / g["gym_sessions"])),
        tile("#5c9a3c", "check", "QUESTS / DAY", S["pct_avg"], "%",
             tl(f'best {bestq}% · ' + " ".join(d["date"] for d in D if d["pct"] == bestq),
                f'lowest {lowq["pct"]}% ({lowq["date"]})'), S["pct_avg"] / 100, f'{S["pct_avg"]}%'),
    ]
    body = hdr("star", "WEEKLY AVERAGE", "% = how close to the goal") + f'<div class="tiles t8">{"".join(t)}</div>'
    return card(body, "avg")


def p_habits():
    D, n = W["days"], S["n"]
    cols = "".join(f'<th>{d["date"].split(".")[1]}<small>{d["dow"][0]}</small></th>' for d in D)
    rows = []
    for q in W["active"]:
        cells = "".join(f"<td>{checkbox(state(d, q)[1])}</td>" for d in D)
        c = qcount(W, q)
        goal = W["goals"]["gym_sessions"] if q == "gym" else n
        p = round(100 * c / goal)
        pc = GOOD if p >= 70 else (MID if p >= 30 else BAD)
        rows.append(f'<tr><td class="ql">{icon(QICON[q])}{QLABEL[q]}</td>{cells}<td>{goal}</td><td>{c}</td>'
                    f'<td style="color:{pc}">{p}%</td></tr>')
    for q in W["locked"]:
        rows.append(f'<tr class="locked"><td class="ql">{icon(QICON[q])}{QLABEL[q]}</td>'
                    f'<td colspan="{n}" class="lk">{icon("lock")} unlocks week {W["week"] + 1}</td><td>–</td><td>–</td><td>–</td></tr>')
    pct_row = "".join(f'<td>{d["pct"]}</td>' for d in D)
    xp_row = "".join(f'<td class="{"hot" if d["xp"] >= 500 else ""}">{d["xp"]}</td>' for d in D)
    Wd, H = 70, 30
    bw = Wd / n
    bars, hearts, pts = [], [], []
    for i, d in enumerate(D):
        for b in range(int(round(d["pct"] / 10))):
            bars.append(f'<rect x="{i * bw + 2:.2f}" y="{H - 2 - (b + 1) * 2.6:.2f}" width="{bw - 4:.2f}" height="2.2" '
                        f'fill="{"#4f8a3a" if b % 2 else "#6fae4f"}"/>')
        hy = H - 2 - d["sleep_score"] / 100 * 26
        hx = i * bw + bw / 2
        pts.append(f"{hx:.2f},{hy:.2f}")
        hearts.append(f'<g transform="translate({hx - 1.6:.2f},{hy - 1.4:.2f}) scale(.4)">'
                      + icon("heart").split(">", 1)[1].replace("</svg>", "") + "</g>")
    grid = "".join(f'<line x1="0" x2="{Wd}" y1="{H - 2 - f * 26:.1f}" y2="{H - 2 - f * 26:.1f}" stroke="#d8c7a6" stroke-width=".15"/>'
                   for f in (0, .5, 1))
    labels = "".join(f'<text x="{i * bw + bw / 2:.2f}" y="{H + 1.6}" text-anchor="middle">{d["date"]}</text>'
                     for i, d in enumerate(D))
    chart = (f'<svg class="hchart" viewBox="-6 0 {Wd + 6} {H + 3}" shape-rendering="crispEdges">'
             f'{grid}<text x="-1" y="{H - 2 - 26 + 1}" text-anchor="end">100%</text>'
             f'<text x="-1" y="{H - 2 - 13 + 1}" text-anchor="end">50%</text>'
             f'<text x="-1" y="{H - 1}" text-anchor="end">0%</text>{"".join(bars)}'
             f'<polyline points="{" ".join(pts)}" fill="none" stroke="#c4473a" stroke-width=".3" stroke-dasharray=".8 .6"/>'
             f'{"".join(hearts)}{labels}</svg>')
    body = (hdr("leaf", "HABIT GRID", W["range"]) +
            f'<table class="hg"><tr><th class="ql">QUESTS</th>{cols}<th>goal</th><th>done</th><th>%</th></tr>'
            f'{"".join(rows)}<tr class="pr"><td class="ql">daily %</td>{pct_row}<td colspan="3">{S["pct_avg"]}%</td></tr>'
            f'<tr class="xr"><td class="ql">{icon("gem")} XP</td>{xp_row}<td colspan="3">{S["xp"]:,}</td></tr></table>'
            f'{chart}<div class="legend">{icon("check")} = done · pale = half credit · '
            f'<span class="sw"></span> daily quests done % · {icon("heart")} sleep score</div>')
    return card(body, "habits")


def p_board():
    rows = ""
    for q, t, text, mn, xp, _ in TIERS:
        if q in W["locked"]:
            rows += (f'<div class="rule new">{icon(QICON[q])}<span>{text} <small>{mn}</small></span>'
                     f'<b>+{xp}</b><em>W{W["week"] + 1}</em></div>')
            continue
        c = sum(1 for d in W["days"] if d["hit"].get(q) == t)
        rows += (f'<div class="rule {"grey" if c == 0 else ""}">{icon(QICON[q])}<span>{text} <small>{mn}</small></span>'
                 f'<b>+{xp}</b><em>{f"×{c}" if c else "–"}</em></div>')
    lv = "".join(f'<div class="lvc {"on" if i == S["lv"] else ""}"><span>LV{i}</span><b>{(i - 1) * 1000:,}</b></div>'
                 for i in range(1, 9))
    body = (hdr("notes", "XP QUEST BOARD", "action · тууштай байдал") + f'<div class="rules">{rows}</div>'
            f'<div class="legend">grey = not earned · ×n = times earned in {wk()} · one tier per quest a day</div>'
            f'<div class="sub">LEVEL TABLE · 1000 XP = 1 LV</div><div class="lvt">{lv}</div>')
    return card(body, "board")


# ───────────────────────────── 2 · day by day ─────────────────────────────
def sleep_track(d):
    b = clock(d["bed"]) - 24
    x0 = max(0, b) / 20 * 100
    x1 = min(20, plain(d["wake"])) / 20 * 100
    ticks = "".join(f'<span style="left:{h / 20 * 100}%">{lab}</span>'
                    for h, lab in [(0, "12A"), (4, "4A"), (8, "8A"), (12, "12P"), (16, "4P"), (20, "8P")])
    return (f'<div class="strack"><div class="ticks">{ticks}</div><div class="rail"><i class="night"></i>'
            f'<b style="left:{x0:.1f}%;width:{x1 - x0:.1f}%"></b></div>'
            f'<div class="bw"><span>{d["bed"]}</span><span>{d["wake"]}</span></div></div>')


def photos(d, maxh=22, maxw=74):
    n = d.get("photos", 0)
    if not n:
        return ""
    rows = 1 if n <= 4 else 2
    cols = -(-n // rows)
    h = min(maxh / rows - 0.6, (maxw / max(cols, 2) - 0.8) * 0.75)
    w = h / 0.75
    imgs = "".join(f'<img src="photos/{d["date"]}-{i}.jpg" style="width:{w:.2f}mm;height:{h:.2f}mm">'
                   for i in range(1, n + 1))
    return f'<div class="strip" style="max-width:{cols * (w + 0.8):.2f}mm">{imgs}</div>'


def journal_html(s):
    for t in "gorb":
        s = s.replace(f"<{t}>", f'<span class="hl {t}">').replace(f"</{t}>", "</span>")
    return s


def p_day(d):
    g = W["goals"]
    s = d["sess"]
    if s:
        name, bg, fg = KIND[s["kind"]]
        gchip = (f'<span class="chip" style="background:{bg};color:{fg}">{icon("dumbbell")}{s["kind"].upper()} → '
                 f'p.{PAGE_NO[d["date"] + "x"]}</span>')
    elif d.get("sport"):
        gchip = f'<span class="chip" style="background:#f6b77c;color:#8a3f12">{icon("ball")}{d["sport"].upper()}</span>'
    else:
        gchip = '<span class="chip" style="background:#e8dcc2;color:#7a6a55">REST DAY</span>'
    daily = [q for q in W["active"] if q != "gym"]  # a rest day is not a missed gym day
    done = len(d["hit"])
    chips = "".join(f'<span class="pchip">{icon(ic)}{t}</span>' for ic, t in d.get("chips", []))
    if d.get("kcal"):
        p, c, f = d["macros"]
        kc = (f'<div class="tv">{d["kcal"]:,}<em>kcal</em></div><div class="tm">P {p}g · C {c}g · F {f}g</div>'
              f'{segbar(min(1, d["kcal"] / g["kcal_line"]), MID if d["kcal"] > 2700 else "#5c9a3c", 10)}'
              f'<div class="tm">line {g["kcal_line"]:,}</div>')
    else:
        kc = '<div class="tv">—</div><div class="tm">not logged</div>'
    if s:
        extra = f' + {d["sport"]}' if d.get("sport") else ""
        tr = (f'<div class="tv">{s["rating"]}<em>/10</em></div><div class="tm">{KIND[s["kind"]][0].lower()} · '
              f'{s["sets"]} sets{extra}</div><div class="tm">pull-ups {d["pull"]} · push-ups {d["push"]}</div>')
    elif d.get("sport"):
        tr = f'<div class="tv sm">{d["sport"]}</div><div class="tm">no gym · sport day</div>'
    else:
        tr = '<div class="tv">—</div><div class="tm">rest day</div>'
    missed = [q for q in daily if q not in d["hit"]]
    halves = [q for q in daily if state(d, q)[1] == "half"]
    lost = sum(MAIN_XP[q] for q in missed) + sum(MAIN_XP[q] - state(d, q)[0] for q in halves)
    mtxt = " · ".join(QLABEL[q] for q in missed) or "nothing"
    if halves:
        mtxt += " · ½ " + " · ½ ".join(QLABEL[q] for q in halves)
    qcells = "".join(f'<div class="qc">{checkbox(state(d, q)[1])}{icon(QICON[q])}<small>{QLABEL[q].split()[-1]}</small></div>'
                     for q in W["active"])
    xchips = "".join(f'<span class="xchip">{icon(QICON[q])}+{state(d, q)[0]}</span>' for q in W["active"] if q in d["hit"])
    sc = d["sleep_score"]
    scol = GOOD if sc >= 75 else ("#3d78b8" if sc >= 70 else MID)
    body = f'''
<div class="dtop"><span class="date">{d["date"]}<small>{d["dow"]}</small></span>
  <span class="chip q">{icon("check")}{done}/{len(W["active"])}</span>{gchip}<span class="xp">{icon("gem")}+{d["xp"]} XP</span></div>
{photos(d)}
<div class="jrow"><div class="box journal">{chips}{journal_html(d["journal"])}</div>
  <div class="box qring"><div class="ring" style="--p:{d["pct"]}"><b>{d["pct"]}%</b></div><small>quests</small></div></div>
<div class="box sleep"><div class="sl">{icon("moon")}SLEEP</div>{sleep_track(d)}
  <div class="sr"><b style="color:{scol}">{d["sleep"].replace("h", ":")}</b><span class="sc" style="border-color:{scol};color:{scol}">{sc}</span><small>score</small></div></div>
<div class="t3">
  <div class="box tt"><div class="tl2" style="color:#3d78b8">{icon("shoe")}STEPS</div><div class="tv">{k(d["steps"])}</div>
    {segbar(d["steps"] / 10000, "#3d78b8", 10)}<div class="tm">goal 10k</div></div>
  <div class="box tt"><div class="tl2" style="color:#8a5cb8">{icon("flame")}BURN</div><div class="tv">{d["burn"]}<em>kcal</em></div>
    {segbar(d["burn"] / g["burn_per_day"], "#8a5cb8", 10)}<div class="tm">goal {g["burn_per_day"]} · quest 1000</div></div>
  <div class="box tt"><div class="tl2" style="color:#b5652b">{icon("dumbbell")}TRAINING</div>{tr}</div>
</div>
<div class="t3">
  <div class="box tt"><div class="tl2" style="color:#c4473a">{icon("coin")}SPENT</div><div class="tv">¥{d["spent"]}</div>
    {segbar(min(1, d["spent"] / (2 * g["spend_per_day"])), "#5c9a3c" if d["spent"] <= g["spend_per_day"] else "#c4473a", 10)}
    <div class="tm cn">{d.get("spent_items", "")}</div></div>
  <div class="box tt"><div class="tl2" style="color:#d9822b">{icon("apple")}KCAL</div>{kc}</div>
  <div class="box tt miss"><div class="tl2" style="color:#c4473a">{icon("target")}MISSED</div>
    <div class="tv">{"−" + str(lost) if lost else "0"}<em>XP</em></div><div class="tm">{mtxt}</div></div>
</div>
<div class="box quests"><div class="qgrid" style="grid-template-columns:repeat({len(W["active"])},1fr)">{qcells}</div>
  <div class="xrow">{xchips or '<span class="tm">no XP today</span>'}<b>= {d["xp"]} XP</b></div></div>'''
    return card(body, d["date"], "day")


def top_set(sets):
    """(unit, weight, reps, label) of the heaviest set; body-weight moves count total reps."""
    if all(w == "BW" for w, _ in sets):
        tot = sum(reps_of(r) for _, r in sets)
        return "BW", 0, tot, f"BW × {tot}"

    def num(w):
        try:
            return float(str(w).replace("lb", "").split("+")[0])
        except ValueError:
            return 0
    w, r = max(sets, key=lambda s_: (num(s_[0]), reps_of(s_[1])))
    unit = "lb" if "lb" in str(w) else "kg"
    return unit, num(w), reps_of(r), f"{w} × {r}"


def p_ex(d):
    s = d["sess"]
    name, bg, fg = KIND[s["kind"]]
    boxes = []
    for e in s["exercises"]:
        rt = ""
        if e.get("rating"):
            r = e["rating"]
            rc = "#4f8a3a" if r >= 8.5 else ("#3d6fb0" if r >= 7 else "#d9622b")
            rt = f'<i class="srt" style="background:{rc}">{r}</i>'
        ws = "".join(f"<td>{w}</td>" for w, _ in e["sets"])
        rs = "".join(f"<td>{r}R</td>" for _, r in e["sets"])
        boxes.append(f'<div class="ex"><div class="exn" style="background:{bg};color:{fg}">{e["name"]}{rt}</div>'
                     f'<table><tr class="w">{ws}</tr><tr class="rp">{rs}</tr></table></div>')
    rc = "#4f8a3a" if s["rating"] >= 8 else ("#3d6fb0" if s["rating"] >= 7 else "#d9622b")
    notes = "".join(f'<div class="nt {k_}">{icon(k_)}{t}</div>' for k_, t in s.get("notes", []))
    earlier = [x for x in W["days"] if x["sess"] and x["date"] != d["date"] and W["days"].index(x) < W["days"].index(d)]
    vrows = ""
    for e in s["exercises"]:
        u, wv, rv, lab = top_set(e["sets"])
        prev = None
        for x in reversed(earlier):
            pe = next((pe for pe in x["sess"]["exercises"] if pe["name"] == e["name"]), None)
            if pe:
                prev = (x["date"], top_set(pe["sets"]))
                break
        if not prev:
            vrows += f'<tr><td>{e["name"]}</td><td>{lab}</td><td class="first">—</td></tr>'
            continue
        pd, (pu, pw, pr, plab) = prev
        if pu != u:
            cls, txt = "eq", f"≈ {pd} · {plab} · other unit"
        elif (wv, rv) > (pw, pr):
            cls, txt = "up", f"↑ {pd} · {plab}"
        elif (wv, rv) < (pw, pr):
            cls, txt = "dn", f"↓ {pd} · {plab}"
        else:
            cls, txt = "eq", f"= {pd} · {plab}"
        vrows += f'<tr><td>{e["name"]}</td><td>{lab}</td><td class="{cls}">{txt}</td></tr>'
    xp = TIER[("gym", d["hit"]["gym"])][0]
    body = f'''
<div class="dtop"><span class="date">{d["date"]}<small>{d["dow"]}</small></span>
  <span class="chip" style="background:{bg};color:{fg}">{icon("dumbbell")}{name}</span>
  <span class="xp">{icon("gem")}+{xp} XP</span></div>
<div class="hdr ex-h">{icon("dumbbell")}<h1>EXERCISE</h1><span class="r">top kg · bottom reps · tag = set rating</span></div>
<div class="exs">{"".join(boxes)}</div>
<div class="rate"><div class="medal" style="background:{rc}"><b>{s["rating"]}</b><small>/10</small></div>
  <div><div>{s["sets"]} sets · {len(s["exercises"])} exercises</div><div>{icon("flame")}burn <b>{d["burn"]}</b> kcal that day</div></div></div>
<div class="box notes"><div class="nh">{icon("notes")}NOTES</div>{notes}
  <div class="vh">TOP SET · vs LAST TIME THIS WEEK</div><table class="vs">{vrows}</table></div>'''
    return card(body, d["date"] + "x", "exday")


# ───────────────────────────── 3 · what I lacked ─────────────────────────────
def gap_text(q):
    D, g, n = W["days"], W["goals"], S["n"]
    if q == "sleep":
        return (f'avg asleep {S["bed_avg"]} · before 12A {len(days_where(W, lambda d: clock(d["bed"]) <= 24))}/{n} · '
                f'score 80+ {len(days_where(W, lambda d: d["sleep_score"] >= 80))}/{n} (best {S["best_sleep"]["sleep_score"]}) · '
                f'8h+ {len(days_where(W, lambda d: mins(d["sleep"]) >= 480))}/{n}')
    if q == "food":
        miss = [d for d in D if not d.get("kcal")]
        hi = max(S["logged"], key=lambda d: d["kcal"]) if S["logged"] else None
        return (f'avg {S["kcal_avg"]:,} kcal vs {g["kcal_line"]:,} line · ≤2500 + P150g '
                f'{sum(1 for d in D if d["hit"].get("food") == "lean")} days · not logged {dates(miss)}'
                + (f' · max {hi["kcal"]:,} ({hi["date"]})' if hi else ""))
    if q == "burn":
        pk = max(D, key=lambda d: d["burn"])
        return f'1000+ kcal {qcount(W, q)}/{n} · peak {pk["burn"]} ({pk["date"]}) · avg {S["burn_avg"]}'
    if q == "sport":
        return f'{qcount(W, q)} sport days · {dates(days_where(W, lambda d: d.get("sport")))}'
    if q == "steps":
        lo = min(D, key=lambda d: d["steps"])
        return f'10k+ {qcount(W, q)}/{n} · 15k+ {sum(1 for d in D if d["hit"].get("steps") == "15k")} · lowest {k(lo["steps"])} ({lo["date"]})'
    if q == "push":
        return f'100+ {qcount(W, q)}/{n} · best {max(d["push"] for d in D)} · week total {sum(d["push"] for d in D)}'
    if q == "pull":
        return f'30+ {qcount(W, q)} days · best {max(d["pull"] for d in D)} · week total {sum(d["pull"] for d in D)}'
    if q == "gym":
        return (f'{len(S["sessions"])}/{g["gym_sessions"]} sessions · 9+ rated {sum(1 for d in D if d["hit"].get("gym") == "9")} · '
                f'best {max((d["sess"]["rating"] for d in S["sessions"]), default=0)}/10')
    if q == "spend":
        hi = max(D, key=lambda d: d["spent"])
        return f'≤ ¥{g["spend_per_day"]} {qcount(W, q)}/{n} · avg ¥{S["spent_avg"]} · top ¥{hi["spent"]} ({hi["date"]})'
    return f"{qcount(W, q)}/{n} days"


FIX = {"sleep": "Lights out before 2A first, then 12A · even 1 of 3 = +50 a night",
       "food": "Log every meal · 150g protein under 2,500 kcal = +200",
       "burn": "One long walk or cardio day to cross 1,000 kcal = +100",
       "sport": "Add cardio, basketball or a run 2–3 days = +100 each",
       "steps": "Keep 10k every day; push one day to 15k = +150",
       "push": "Spread push-ups: 4 × 25 through the day = 100",
       "pull": "Finish 30 pull-ups every gym day = +50",
       "gym": "Aim for one session rated 9+ = +250",
       "spend": "Cap snacks & taxis to stay ≤ ¥80 = +50 a day",
       "bike": "Ride 5km+ on rest days = +50",
       "focus": "Block 2h for the main project = +200"}


def lack_order():
    return sorted(W["active"], key=lambda q: -(qmax(W, q) - qxp(W, q)))


def p_lack1():
    rows, tot_max = [], 0
    for q in lack_order():
        got, mx = qxp(W, q), qmax(W, q)
        tot_max += mx
        rows.append(f'<div class="lrow">{icon(QICON[q])}<span>{QLABEL[q]}</span><i><b style="width:{got / mx * 100:.0f}%"></b></i>'
                    f'<em>{got:,}<small> / {mx:,}</small></em><strong>−{mx - got:,}</strong></div>')
    p = round(100 * S["xp"] / tot_max)
    g = "".join(f'<div class="box gap">{icon(QICON[q])}<div><b>{QLABEL[q].upper()} <em>−{qmax(W, q) - qxp(W, q):,} XP</em></b>'
                f'<small>{gap_text(q)}</small></div></div>' for q in lack_order()[:3])
    body = (hdr("target", "WHAT I LACKED", "1 / 2 · XP left on the table") +
            f'<div class="box lackbox"><div class="lhead"><div class="ring" style="--p:{p}"><b>{p}%</b></div>'
            f'<div><b>{S["xp"]:,} of {tot_max:,} XP</b><small>earned vs the most the quest board could pay in {wk()}</small></div></div>'
            f'{"".join(rows)}<div class="legend"><span class="sw"></span> earned · empty = missed · red = XP lost</div></div>'
            f'<div class="sub">3 BIGGEST GAPS</div>{g}')
    return card(body, "lack1")


def p_lack2():
    D, g, n = W["days"], W["goals"], S["n"]
    ses = S["sessions"]
    eb = min(D, key=lambda d: clock(d["bed"]))
    bs = S["best_sleep"]
    prot = days_where(W, lambda d: d.get("kcal") and d["macros"][0] >= g["protein_g"])
    items = [
        ("moon", "Asleep before 12A", len(days_where(W, lambda d: clock(d["bed"]) <= 24)), n, f'earliest {eb["bed"]} ({eb["date"]})'),
        ("moon", "Sleep score 80+", len(days_where(W, lambda d: d["sleep_score"] >= 80)), n, f'best {bs["sleep_score"]} ({bs["date"]})'),
        ("moon", "8h+ sleep", len(days_where(W, lambda d: mins(d["sleep"]) >= 480)), n,
         dates(days_where(W, lambda d: mins(d["sleep"]) >= 480))),
        ("apple", "Food logged", len(S["logged"]), n, "missed " + dates([d for d in D if not d.get("kcal")])),
        ("apple", f'Protein {g["protein_g"]}g+', len(prot), n, " · ".join(f'{d["date"]} {d["macros"][0]}g' for d in prot) or "none"),
        ("apple", "Under 2,700 kcal", len(days_where(W, lambda d: d.get("kcal") and d["kcal"] <= 2700)), n,
         dates(days_where(W, lambda d: d.get("kcal") and d["kcal"] <= 2700))),
        ("flame", "Burn 1000+ kcal", qcount(W, "burn"), n, gap_text("burn").split(" · ")[1]),
        ("pushup", "100 push-ups", qcount(W, "push"), n, f'best {max(d["push"] for d in D)} · total {sum(d["push"] for d in D)}'),
        ("coin", f'Spend ≤ ¥{g["spend_per_day"]}', qcount(W, "spend"), n, f'avg ¥{S["spent_avg"]} / day'),
        ("dumbbell", "Gym rated 9+", sum(1 for d in ses if d["hit"]["gym"] == "9"), len(ses),
         f'best {max((d["sess"]["rating"] for d in ses), default=0)} · avg {S["rating_avg"]}'),
        ("pullup", "30 pull-ups on gym day", sum(1 for d in ses if d["pull"] >= 30), len(ses),
         " · ".join(f'{d["date"]} = {d["pull"]}' for d in ses if d["pull"] < 30) or "all ✓"),
        ("ball", "Sport day", qcount(W, "sport"), n, dates(days_where(W, lambda d: d.get("sport")))),
        ("shoe", "10k steps", qcount(W, "steps"), n,
         " · ".join(f'{d["date"]} = {k(d["steps"])}' for d in D if d["steps"] < 10000) or "every day ✓"),
    ]
    rows = "".join(
        f'<div class="lk2">{icon(i)}<span>{t}<small>{s_}</small></span>'
        f'<i>{"".join("<b class=on></b>" if j < c else "<b></b>" for j in range(m))}</i>'
        f'<em class="{"zero" if c == 0 else ("ok" if m and c / m >= .7 else "")}">{c}/{m}</em></div>'
        for i, t, c, m, s_ in items)
    f = "".join(f'<div class="fix">{icon(QICON[q])}{FIX[q]}</div>' for q in lack_order()[:4])
    body = (hdr("target", "WHAT I LACKED", "2 / 2 · days hit") + f'<div class="box lk2box">{rows}</div>'
            f'<div class="box fixbox"><div class="nh">{icon("pen")}FIX NEXT WEEK · biggest gaps first</div>{f}</div>')
    return card(body, "lack2")


def p_next():
    n = S["n"]
    sub = {
        "steps": f'{wk()}: {qcount(W, "steps")}/{n} days' + (" ✓ keep it" if qcount(W, "steps") >= n - 1 else ""),
        "food": f'{wk()}: lean days {sum(1 for d in W["days"] if d["hit"].get("food") == "lean")} · logged {len(S["logged"])}/{n}',
        "sleep": f'{wk()}: before 12A {len(days_where(W, lambda d: clock(d["bed"]) <= 24))}/{n} · avg {S["bed_avg"]}',
        "gym": f'{wk()}: {len(S["sessions"])} sessions · rate one 9+ → +250',
        "sport": f'{wk()}: {qcount(W, "sport")} days · cardio · basketball · run',
        "burn": f'{wk()} peak {max(d["burn"] for d in W["days"])}',
        "pull": f'{wk()}: 30+ on {qcount(W, "pull")} days',
        "push": f'{wk()} best {max(d["push"] for d in W["days"])}',
        "spend": f'{wk()}: {qcount(W, "spend")}/{n} days · avg ¥{S["spent_avg"]}',
    }
    title = {"steps": "Walk 10k steps a day", "food": "≤2500 kcal + 150g protein", "sleep": "Asleep before 12A · 8h+",
             "gym": f'Gym {W["goals"]["gym_sessions"]} sessions', "sport": "Sport 2+ days", "burn": "Burn 1000+ kcal once",
             "pull": "30 pull-ups every gym day", "push": "100 push-ups in a day", "spend": "Spend ≤ ¥80 · 4 days",
             "bike": "Bike 5km+", "focus": "Focus 2h+ on main work"}
    qs = [(QICON[q], title[q], sub[q], MAIN_XP[q], False) for q in lack_order()]
    qs += [(i, t, s_, x, False) for i, t, s_, x in W.get("next_week_extra", [])]
    qs += [(QICON[q], title[q], "NEW quest", MAIN_XP[q], True) for q in W["locked"]]
    rows = "".join(f'<div class="box nq">{icon(i)}<div><b>{t}</b><small class="{"new" if new else ""}">{s_}</small></div>'
                   f'<em>+{x}</em><span class="cb"></span></div>' for i, t, s_, x, new in qs)
    per_day = math.ceil(S["need"] / 7)
    body = (hdr("leaf", f'WEEK {W["week"] + 1} QUESTS', "biggest gaps first") +
            f'<div class="box lvbar">{icon("gem")}LV {S["lv"]} → LV {S["lv"] + 1} · {S["need"]} XP to go · about {per_day} XP a day</div>'
            f'<div class="nqs">{rows}</div>')
    return card(body, "next")


def p_notes(key):
    body = hdr("notes", "NOTES", "") + '<div class="lines"></div>'
    return card(body, key)


# ───────────────────────────── assemble ─────────────────────────────
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;500;600;700'
         '&family=Press+Start+2P&family=Nunito:wght@500;600;700;800&family=Noto+Sans+SC:wght@500;700&display=swap" rel="stylesheet">')
SLOT_X = (18, 110)   # A4 = 210 × 297 mm, two 82 mm cards + 10 mm gutter
SLOT_Y = (32, 160)   # two 116 mm cards + 12 mm gutter


def build_cards():
    order = ["cover", "glance", "avg", "habits", "board"]
    for d in W["days"]:
        order.append(d["date"])
        if d["sess"]:
            order.append(d["date"] + "x")
    order += ["lack1", "lack2", "next"]
    while len(order) % 4:  # a printed sheet holds 4 cards; pad with note pages
        order.append(f"notes{len(order)}")
    PAGE_NO.clear()
    PAGE_NO.update({k_: i for i, k_ in enumerate(order, 1)})
    pages = {"cover": p_cover, "glance": p_glance, "avg": p_avg, "habits": p_habits, "board": p_board,
             "lack1": p_lack1, "lack2": p_lack2, "next": p_next}
    days = {d["date"]: d for d in W["days"]}
    out = []
    for k_ in order:
        if k_ in pages:
            out.append(pages[k_]())
        elif k_.startswith("notes"):
            out.append(p_notes(k_))
        elif k_.endswith("x"):
            out.append(p_ex(days[k_[:-1]]))
        else:
            out.append(p_day(days[k_]))
    return out


def main():
    global MONTH
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    W.update(load(args[0]))
    S.update(stats(W))
    MONTH = f'{W["month"]} {W["year"]} · {wk()}'
    css = (HERE / "tn.css").read_text()
    cards = build_cards()
    head = f'<!doctype html><html lang="mn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{FONTS}'
    out_dir, stem = W["dir"], W["stem"]
    digital, printed = out_dir / f"{stem}-tn.html", out_dir / f"{stem}-tn-print.html"
    digital.write_text(f'{head}<title>{W["month"].title()} {wk()} TN</title><style>{css}\n@page{{size:82mm 116mm;margin:0}}</style></head>'
                       f'<body class="digital">{"".join(cards)}</body></html>')
    n = len(cards) // 4
    sheets = []
    for s_ in range(n, 0, -1):  # reversed: last sheet first
        p = (s_ - 1) * 4
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
        sheets.append(f'<div class="sheet"><div class="shh">sheet {s_}/{n} · p.{p + 1}–{p + 4} · print 100% · card 82×116 mm</div>'
                      f'<div class="ruler"><i></i><span>this bar = 90 mm (check scale)</span></div>{marks}{slots}</div>')
    printed.write_text(f'{head}<title>{W["month"].title()} {wk()} TN print</title><style>{css}\n@page{{size:A4;margin:0}}</style></head>'
                       f'<body class="print">{"".join(sheets)}</body></html>')
    print(f'{len(cards)} cards · {n} sheets · {S["xp"]:,} XP · LV {S["lv"]}')
    if "--pdf" in sys.argv:
        name = W.get("pdf_name", stem)
        subprocess.run(["node", str(HERE / "print.js"), str(digital), str(out_dir / f"{name}.pdf"),
                        str(printed), str(out_dir / f"{name}_print_A4_reversed.pdf")], check=True)


if __name__ == "__main__":
    main()
