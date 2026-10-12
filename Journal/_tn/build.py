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


# ───────────────────────────── page helpers ─────────────────────────────
# Rule of this layout: every fact lives on exactly one page.
#   p.2 the week   — what happened, day by day (values + quest result)
#   p.3 quests     — the rules and what each quest paid vs could have paid
#   p.4 plan       — the next week, built from the biggest gaps
#   day / gym      — the detail behind one column of p.2
import datetime

W, S, PAGE_NO = {}, {}, {}
MONTH = ""

RULE = {"steps": "10k → 100 · 15k → 150", "food": "logged 50 · ≤2700 + P100 170 · ≤2500 + P150 200",
        "sleep": "8h · score 80 · before 12A — 1 → 50 · 2 → 150 · 3 → 250", "gym": "session 200 · rated 9+ 250",
        "sport": "cardio · basketball · run 100", "burn": "1000+ kcal 100", "pull": "30+ in a day 50",
        "push": "100+ in a day 50", "spend": "≤ ¥80 50", "bike": "5km+ 50", "focus": "2h+ main work 200"}
TARGET = {"steps": "10k steps every day", "food": "≤2500 kcal with 150g protein", "sleep": "Asleep before 12A, 8h+",
          "gym": "Gym 5× · rate one 9+", "sport": "Sport 2+ days", "burn": "Burn 1000+ kcal once",
          "pull": "30 pull-ups every gym day", "push": "100 push-ups in a day", "spend": "Spend ≤ ¥80 on 4 days",
          "bike": "Bike 5km+", "focus": "Focus 2h+ on main work"}


def state(d, q):
    t = d["hit"].get(q)
    if t is None:
        return 0, None
    xp, half = TIER[(q, t)]
    return xp, "h" if half else "f"


def mark(st):
    return {"f": '<i class="mk f">✓</i>', "h": '<i class="mk h">½</i>'}.get(st, '<i class="mk m"></i>')


def bar(frac, cls=""):
    frac = max(0.0, min(1.0, frac))
    return f'<span class="bar {cls}"><b style="width:{frac * 100:.0f}%"></b></span>'


def card(body, key, cls=""):
    return (f'<section class="card {cls}">{body}'
            f'<footer><span>{MONTH}</span><span>{PAGE_NO[key]}</span></footer></section>')


def title(ic, text, right=""):
    return f'<h1 class="t">{icon(ic)}<span>{text}</span><small>{right}</small></h1>'


def k(v):
    return f"{v / 1000:.1f}k"


def wk(offset=0):
    return f'W{W["week"] + offset}'


def next_dates():
    y = W["year"]
    m, dd = map(int, W["days"][-1]["date"].split("."))
    last = datetime.date(y, m, dd)
    return [last + datetime.timedelta(days=i) for i in range(1, 8)]


# ───────────────────────────── p.1 cover ─────────────────────────────
def p_cover():
    toc = [("The week", "every quest, every day · XP missed", "week"), (f'{wk(1)} plan', "three things to fix", "plan")]
    rows = "".join(f'<li><b>{a}</b><em>{b}</em><i></i><span>{PAGE_NO[c]}</span></li>' for a, b, c in toc)
    for d in W["days"]:
        s = d["sess"]
        tag = f'{s["kind"]} {s["rating"]}/10' if s else (d.get("sport") or "rest")
        rows += f'<li class="dy"><b>{d["date"]} {d["dow"].title()}</b><em>{tag}</em><i></i><span>{PAGE_NO[d["date"]]}</span></li>'
    body = f'''
<div class="art pf">{scene("day")}</div>
<div class="ttl"><b>{W["month"]}</b><span>WEEK {W["week"]} · {W["range"]} · {W["year"]}</span></div>
<div class="lvl"><span class="lvb">LV {S["lv"]}</span>
  <div>{bar(S["into"] / 1000, "xpb")}<small>{S["xp"]:,} XP this week · {S["into"]} / 1000 to LV {S["lv"] + 1}</small></div></div>
<ul class="toc">{rows}</ul>'''
    return card(body, "cover", "cover")


# ───────────────────────────── p.2 the week + quests ─────────────────────────────
def cell(d, q):
    s = d["sess"]
    _, st = state(d, q)
    cls = st or "m"
    if q == "steps":
        v, sub = k(d["steps"]), ""
    elif q == "food":
        v, sub = (f'{d["kcal"] / 1000:.1f}k', f'P{d["macros"][0]}') if d.get("kcal") else ("—", "")
    elif q == "sleep":
        v, sub = d["sleep"], str(d["sleep_score"])
    elif q == "gym":
        if not s:
            return '<td class="x">·</td>'
        v, sub = s["kind"].upper(), f'{s["rating"]}/10'
    elif q == "sport":
        v, sub = (d["sport"][:6], "") if d.get("sport") else ("—", "")
    elif q == "burn":
        v, sub = str(d["burn"]), ""
    elif q == "pull":
        v, sub = (str(d["pull"]) if d["pull"] else "—"), ""
    elif q == "push":
        v, sub = (str(d["push"]) if d["push"] else "—"), ""
    elif q == "spend":
        v, sub = f'¥{d["spent"]}', ""
    elif q == "bike":
        v, sub = f'{d.get("bike_km", 0)}km', ""
    else:
        v, sub = f'{d.get("focus_h", 0)}h', ""
    return f'<td class="{cls}">{v}{f"<small>{sub}</small>" if sub else ""}</td>'


def p_week():
    """Quests × days in one grid: each cell is the day's value coloured by the quest result,
    each row ends with the XP it earned and the XP it missed (rows sorted by XP missed)."""
    D = W["days"]
    tot = sum(qmax(W, q) for q in W["active"])
    order = sorted(W["active"], key=lambda q: -(qmax(W, q) - qxp(W, q)))
    head = "".join(f'<th>{d["date"]}<small>{d["dow"][:2]}</small></th>' for d in D)
    rows = ""
    for q in order:
        got, lost = qxp(W, q), qmax(W, q) - qxp(W, q)
        rows += (f'<tr><th class="q">{icon(QICON[q])}{QLABEL[q]}</th>{"".join(cell(d, q) for d in D)}'
                 f'<td class="sum">{got:,}</td><td class="lost {"" if lost else "ok"}">{"−" + format(lost, ",") if lost else "✓"}</td></tr>')
    xp = "".join(f'<td>{d["xp"]}</td>' for d in D)
    rules = "".join(f'<li>{icon(QICON[q])}<b>{QLABEL[q]}</b> {RULE[q]}</li>' for q in order)
    p = S["xp"] / tot
    body = (title("calendar", "THE WEEK", W["range"]) +
            f'<div class="qhead"><b>{S["xp"]:,}</b><span>of {tot:,} XP the board could pay · {round(p * 100)}%</span>'
            f'{bar(p, "xpb")}<small>steps {S["steps_tot"]:,} · sleep avg {hm(S["sleep_avg"])} · burn {S["burn_tot"]:,} kcal · '
            f'spent ¥{S["spent_tot"]:,}</small></div>'
            f'<table class="wk"><tr><th></th>{head}<th class="sum">XP</th><th class="lost">missed</th></tr>{rows}'
            f'<tr class="xpr"><th class="q">{icon("gem")}XP</th>{xp}<td class="sum">{S["xp"]:,}</td><td></td></tr></table>'
            f'<p class="key">{mark("f")} done {mark("h")} half {mark(None)} missed · rows sorted by XP missed</p>'
            f'<ul class="rules">{rules}</ul>')
    return card(body, "week")


# ───────────────────────────── p.4 plan ─────────────────────────────
def why(q):
    n = S["n"]
    if q == "sleep":
        return (f'{wk()}: asleep avg {S["bed_avg"]} · before 12A '
                f'{len(days_where(W, lambda d: clock(d["bed"]) <= 24))}/{n} · best score {S["best_sleep"]["sleep_score"]}')
    if q == "food":
        return f'{wk()}: avg {S["kcal_avg"]:,} kcal · protein {S["mac_avg"][0]}g · {len(S["logged"])}/{n} logged'
    if q == "burn":
        pk = max(W["days"], key=lambda d: d["burn"])
        return f'{wk()}: peak {pk["burn"]} kcal ({pk["date"]}) · avg {S["burn_avg"]}'
    if q == "sport":
        return f'{wk()}: {qcount(W, "sport")} days · {dates(days_where(W, lambda d: d.get("sport")))}'
    if q == "push":
        return f'{wk()}: best {max(d["push"] for d in W["days"])} in a day'
    if q == "pull":
        return f'{wk()}: 30+ on {qcount(W, "pull")} of {len(S["sessions"])} gym days'
    if q == "spend":
        return f'{wk()}: {qcount(W, "spend")}/{n} days · avg ¥{S["spent_avg"]}'
    if q == "steps":
        return f'{wk()}: {qcount(W, "steps")}/{n} days'
    if q == "gym":
        return f'{wk()}: {len(S["sessions"])} sessions · best {max((d["sess"]["rating"] for d in S["sessions"]), default=0)}/10'
    return ""


def p_plan():
    order = sorted([q for q in W["active"] if q != "gym"], key=lambda q: -(qmax(W, q) - qxp(W, q)))
    days = next_dates()
    head = "".join(f'<span>{d.day}</span>' for d in days)
    focus = ""
    for i, q in enumerate(order[:3], 1):
        focus += (f'<div class="fc pf"><div class="fh"><span class="no">{i}</span>{icon(QICON[q])}<b>{TARGET[q]}</b>'
                  f'<em>+{MAIN_XP[q]}</em></div><small>{why(q)}</small>'
                  f'<div class="tk">{"".join("<i></i>" for _ in days)}</div></div>')
    keep = [q for q in W["active"] if qcount(W, q) >= (len(S["sessions"]) if q == "gym" else S["n"] - 1)]
    keep_txt = " · ".join(f'{QLABEL[q]} {qcount(W, q)}/{W["goals"]["gym_sessions"] if q == "gym" else S["n"]}'
                          for q in keep) or "—"
    new = [(QICON[q], TARGET[q], MAIN_XP[q]) for q in W["locked"]]
    new += [(i, t, x) for i, t, _, x in W.get("next_week_extra", [])]
    new_html = "".join(f'<li>{icon(i)}<b>{t}</b><em>+{x}</em><i class="box"></i></li>' for i, t, x in new)
    per_day = math.ceil(S["need"] / 7)
    body = (title("leaf", f'{wk(1)} PLAN', f'{days[0].month}.{days[0].day} – {days[-1].month}.{days[-1].day}') +
            f'<div class="goal">LV {S["lv"]} → LV {S["lv"] + 1}<b>{S["need"]} XP to go</b><span>≈ {per_day} XP a day</span></div>'
            f'<div class="dh"><span>FIX · biggest gaps</span><div class="tk lab">{head}</div></div>{focus}'
            f'<div class="keep"><b>KEEP</b> {keep_txt}</div>'
            f'<div class="dh"><span>ALSO THIS WEEK</span></div><ul class="new">{new_html}</ul>')
    return card(body, "plan")


# ───────────────────────────── day + gym (v2 cards) ─────────────────────────────
GOOD, MID, BAD = "#4f8a3a", "#d9822b", "#c4473a"


def segbar(frac, color, segs=10):
    frac = max(0.0, min(1.0, frac))
    full = frac * segs
    cells = []
    for i in range(segs):
        f = max(0.0, min(1.0, full - i))
        cells.append(f'<i style="background:linear-gradient(90deg,{color} {f * 100:.0f}%,transparent {f * 100:.0f}%)"></i>')
    return f'<span class="seg">{"".join(cells)}</span>'


def state2(d, q):
    t = d["hit"].get(q)
    if t is None:
        return 0, None
    xp, half = TIER[(q, t)]
    return xp, "half" if half else "full"


def checkbox2(st):
    return f'<span class="cb {st or ""}">{icon("check", "ck") if st else ""}</span>'


def hdr(ic, title, right=""):
    return f'<div class="hdr">{icon(ic)}<h1>{title}</h1><span class="r">{right}</span></div>'


def sleep_track(d):
    b = clock(d["bed"]) - 24
    x0 = max(0, b) / 20 * 100
    x1 = min(20, plain(d["wake"])) / 20 * 100
    ticks = "".join(f'<span style="left:{h / 20 * 100}%">{lab}</span>'
                    for h, lab in [(0, "12A"), (4, "4A"), (8, "8A"), (12, "12P"), (16, "4P"), (20, "8P")])
    return (f'<div class="strack"><div class="ticks">{ticks}</div><div class="rail"><i class="night"></i>'
            f'<b style="left:{x0:.1f}%;width:{x1 - x0:.1f}%"></b></div>'
            f'<div class="bw"><span>{d["bed"]}</span><span>{d["wake"]}</span></div></div>')


def photos2(d, maxh=22, maxw=74):
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
    halves = [q for q in daily if state2(d, q)[1] == "half"]
    lost = sum(MAIN_XP[q] for q in missed) + sum(MAIN_XP[q] - state2(d, q)[0] for q in halves)
    mtxt = " · ".join(QLABEL[q] for q in missed) or "nothing"
    if halves:
        mtxt += " · ½ " + " · ½ ".join(QLABEL[q] for q in halves)
    qcells = "".join(f'<div class="qc">{checkbox2(state2(d, q)[1])}{icon(QICON[q])}<small>{QLABEL[q].split()[-1]}</small></div>'
                     for q in W["active"])
    xchips = "".join(f'<span class="xchip">{icon(QICON[q])}+{state2(d, q)[0]}</span>' for q in W["active"] if q in d["hit"])
    sc = d["sleep_score"]
    scol = GOOD if sc >= 75 else ("#3d78b8" if sc >= 70 else MID)
    body = f'''
<div class="dtop"><span class="date">{d["date"]}<small>{d["dow"]}</small></span>
  <span class="chip q">{icon("check")}{done}/{len(W["active"])}</span>{gchip}<span class="xp">{icon("gem")}+{d["xp"]} XP</span></div>
{photos2(d)}
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
    return card(body, d["date"], "day v2")


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
    return card(body, d["date"] + "x", "exday v2")




def p_notes(key):
    return card(title("notes", "NOTES") + '<div class="lines"></div>', key)


# ───────────────────────────── assemble ─────────────────────────────
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;500;600;700'
         '&family=Nunito:wght@500;600;700;800;900&family=Noto+Sans+SC:wght@500;700&display=swap" rel="stylesheet">')
SLOT_X = (18, 110)   # A4 = 210 × 297 mm, two 82 mm cards + 10 mm gutter
SLOT_Y = (32, 160)   # two 116 mm cards + 12 mm gutter


def build_cards():
    order = ["cover", "week", "plan"]
    for d in W["days"]:
        order.append(d["date"])
        if d["sess"]:
            order.append(d["date"] + "x")
    while len(order) % 4:  # a printed sheet holds 4 cards; pad with note pages
        order.append(f"notes{len(order)}")
    PAGE_NO.clear()
    PAGE_NO.update({k_: i for i, k_ in enumerate(order, 1)})
    pages = {"cover": p_cover, "week": p_week, "plan": p_plan}
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
