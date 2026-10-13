"""Fineliner-style handwriting for PDF pages (reportlab), modelled on the user's notebooks.

All-caps, single-stroke letters with small random variation per letter and a slow
wobble along every stroke, so no two letters are identical. Latin letters, digits and
punctuation come from the Hershey 'futural' single-stroke font; Cyrillic capitals
(including Mongolian Ө and Ү) are drawn here in the same pen. Also hand-drawn boxes,
arrows, braces, underlines, strike-throughs, circles and hatching.

Coordinates are in millimetres, y up. Requires: reportlab, Hershey-Fonts.
"""

import math
import random

from HersheyFonts import HersheyFonts
from reportlab.lib.units import mm

BLACK = (0.13, 0.12, 0.15)
RED = (0.78, 0.13, 0.22)
GREEN = (0.19, 0.42, 0.27)
PENCIL = (0.52, 0.51, 0.50)

_F = HersheyFonts()
_F.load_default_font("futural")
_CAP = 21.0


def _hershey(ch):
    g = _F.all_glyphs.get(ch)
    if g is None:
        return None
    lo = g.left_offset
    strokes = [[((x - lo) / _CAP, (9 - y) / _CAP) for x, y in s] for s in g.strokes]
    return strokes, g.char_width / _CAP


def _ellipse(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(2 * math.pi * k / n + math.pi / 2), cy + ry * math.sin(2 * math.pi * k / n + math.pi / 2))
            for k in range(n + 1)]


_O = _hershey("O")[0]
_E = _hershey("E")[0]

# Cyrillic capitals that don't share a Latin shape: polylines in cap units, plus advance.
_CYR = {
    "Б": ([[(0.66, 1), (0.08, 1), (0.08, 0), (0.44, 0), (0.6, 0.05), (0.68, 0.16), (0.7, 0.28), (0.68, 0.41),
             (0.6, 0.51), (0.44, 0.56), (0.08, 0.56)]], 0.9),
    "Г": ([[(0.64, 1), (0.08, 1), (0.08, 0)]], 0.8),
    "Д": ([[(0.0, -0.16), (0.0, 0), (0.82, 0), (0.82, -0.16)],
           [(0.1, 0), (0.2, 0.3), (0.26, 0.7), (0.28, 1), (0.7, 1), (0.7, 0)]], 1.0),
    "Ж": ([[(0.04, 1), (0.5, 0.52), (0.02, 0)], [(0.96, 1), (0.5, 0.52), (0.98, 0)], [(0.5, 1), (0.5, 0)]], 1.2),
    "З": ([[(0.06, 0.86), (0.2, 0.97), (0.38, 1), (0.55, 0.96), (0.63, 0.85), (0.62, 0.7), (0.52, 0.59), (0.32, 0.55)],
           [(0.52, 0.57), (0.64, 0.46), (0.68, 0.3), (0.63, 0.13), (0.49, 0.02), (0.3, 0), (0.13, 0.05), (0.03, 0.16)]], 0.9),
    "И": ([[(0.08, 1), (0.08, 0), (0.74, 1), (0.74, 0)]], 1.0),
    "Й": ([[(0.08, 1), (0.08, 0), (0.74, 1), (0.74, 0)], [(0.26, 1.2), (0.33, 1.12), (0.49, 1.12), (0.56, 1.2)]], 1.0),
    "Л": ([[(0.0, 0.02), (0.12, 0.1), (0.2, 0.4), (0.26, 1), (0.72, 1), (0.72, 0)]], 0.98),
    "П": ([[(0.08, 0), (0.08, 1), (0.72, 1), (0.72, 0)]], 0.98),
    "У": ([[(0.04, 1), (0.4, 0.4)], [(0.76, 1), (0.32, 0.12), (0.22, 0.03), (0.08, 0)]], 0.96),
    "Ф": ([[(0.46, 1.04), (0.46, -0.04)], _ellipse(0.46, 0.53, 0.4, 0.3)], 1.12),
    "Ц": ([[(0.08, 1), (0.08, 0), (0.72, 0), (0.72, 1)], [(0.72, 0), (0.84, 0), (0.84, -0.16)]], 1.06),
    "Ч": ([[(0.08, 1), (0.08, 0.66), (0.16, 0.53), (0.36, 0.48), (0.66, 0.52)], [(0.66, 1), (0.66, 0)]], 0.92),
    "Ш": ([[(0.08, 1), (0.08, 0), (0.92, 0), (0.92, 1)], [(0.5, 1), (0.5, 0)]], 1.18),
    "Щ": ([[(0.08, 1), (0.08, 0), (0.92, 0), (0.92, 1)], [(0.5, 1), (0.5, 0)], [(0.92, 0), (1.04, 0), (1.04, -0.16)]], 1.26),
    "Ъ": ([[(0.0, 1), (0.18, 1), (0.18, 0), (0.5, 0), (0.65, 0.06), (0.72, 0.2), (0.72, 0.36), (0.65, 0.5),
             (0.5, 0.56), (0.18, 0.56)]], 0.98),
    "Ы": ([[(0.08, 1), (0.08, 0), (0.38, 0), (0.52, 0.06), (0.58, 0.2), (0.58, 0.36), (0.52, 0.5), (0.38, 0.56),
             (0.08, 0.56)], [(0.86, 1), (0.86, 0)]], 1.12),
    "Ь": ([[(0.08, 1), (0.08, 0), (0.45, 0), (0.6, 0.06), (0.67, 0.2), (0.67, 0.36), (0.6, 0.5), (0.45, 0.56),
             (0.08, 0.56)]], 0.92),
    "Э": ([[(0.06, 0.86), (0.2, 0.97), (0.4, 1), (0.58, 0.95), (0.7, 0.8), (0.76, 0.6), (0.76, 0.4), (0.7, 0.2),
             (0.58, 0.05), (0.4, 0), (0.2, 0.03), (0.06, 0.15)], [(0.3, 0.52), (0.76, 0.52)]], 1.0),
    "Ю": ([[(0.08, 1), (0.08, 0)], [(0.08, 0.52), (0.32, 0.52)], _ellipse(0.62, 0.5, 0.28, 0.5)], 1.12),
    "Я": ([[(0.7, 0), (0.7, 1), (0.3, 1), (0.15, 0.95), (0.08, 0.82), (0.08, 0.68), (0.15, 0.56), (0.3, 0.5),
             (0.7, 0.5)], [(0.4, 0.5), (0.06, 0)]], 0.96),
}
_ALIAS = {"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
          "Х": "X", "Ү": "Y"}
_EXTRA = {
    "→": ([[(0.04, 0.42), (1.0, 0.42)], [(0.74, 0.62), (1.0, 0.42), (0.74, 0.22)]], 1.2),
    "←": ([[(1.0, 0.42), (0.04, 0.42)], [(0.3, 0.62), (0.04, 0.42), (0.3, 0.22)]], 1.2),
    "·": ([_ellipse(0.17, 0.42, 0.045, 0.045, 8)], 0.4),
    "—": ([[(0.06, 0.42), (1.0, 0.42)]], 1.12),
    "–": ([[(0.06, 0.42), (0.62, 0.42)]], 0.74),
    "✓": ([[(0.0, 0.45), (0.25, 0.08), (0.78, 0.92)]], 0.9),
    "×": ([[(0.1, 0.12), (0.6, 0.62)], [(0.6, 0.12), (0.1, 0.62)]], 0.78),
}
_NORMAL = {"“": '"', "”": '"', "‘": "'", "’": "'", "½": "1/2", "≈": "~", "…": "...", "≤": "<=", "≥": ">="}


def _glyph(ch):
    if ch in _EXTRA:
        return _EXTRA[ch]
    if ch in _CYR:
        return _CYR[ch]
    if ch in _ALIAS:
        return _hershey(_ALIAS[ch])
    if ch == "Ө":
        strokes, adv = _hershey("O")
        return strokes + [[(0.12, 0.5), (0.86, 0.5)]], adv
    if ch == "Ё":
        strokes, adv = _hershey("E")
        return strokes + [_ellipse(0.3, 1.16, 0.04, 0.04, 6), _ellipse(0.55, 1.16, 0.04, 0.04, 6)], adv
    return _hershey(ch) or _hershey("?")


def normalize(s):
    for a, b in _NORMAL.items():
        s = s.replace(a, b)
    return s.upper()


class Hand:
    """A pen on a reportlab canvas. Units: mm, y up."""

    def __init__(self, c, seed=1, width_k=0.96):
        self.c = c
        self.rng = random.Random(seed)
        self.width_k = width_k

    # ---------- low level ----------

    def _draw(self, pts, color, lw):
        c = self.c
        c.setStrokeColorRGB(*color)
        c.setLineWidth(lw * mm)
        c.setLineCap(1)
        c.setLineJoin(1)
        p = c.beginPath()
        p.moveTo(pts[0][0] * mm, pts[0][1] * mm)
        for x, y in pts[1:]:
            p.lineTo(x * mm, y * mm)
        c.drawPath(p, stroke=1, fill=0)

    def _wobble(self, pts, amp, wavelength, step=None):
        """Densify a polyline and push it sideways by a slow random wave."""
        if len(pts) < 2:
            return pts
        step = step or wavelength / 6
        dense = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            d = math.hypot(x1 - x0, y1 - y0)
            n = max(1, int(d / step))
            for k in range(1, n + 1):
                dense.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
        r = self.rng
        p1, p2 = r.uniform(0, 6.28), r.uniform(0, 6.28)
        l1, l2 = wavelength * r.uniform(0.8, 1.3), wavelength * r.uniform(0.35, 0.6)
        out, s = [], 0.0
        for i, (x, y) in enumerate(dense):
            if i:
                s += math.hypot(x - dense[i - 1][0], y - dense[i - 1][1])
            a = i - 1 if i else 0
            b = i + 1 if i + 1 < len(dense) else i
            tx, ty = dense[b][0] - dense[a][0], dense[b][1] - dense[a][1]
            tl = math.hypot(tx, ty) or 1
            nx, ny = -ty / tl, tx / tl
            off = amp * (0.7 * math.sin(2 * math.pi * s / l1 + p1) + 0.3 * math.sin(2 * math.pi * s / l2 + p2))
            out.append((x + nx * off, y + ny * off))
        return out

    # ---------- text ----------

    def space(self, size):
        return 0.6 * size

    def width(self, s, size, track=1.0):
        w = 0.0
        for ch in normalize(s):
            if ch == " ":
                w += self.space(size)
            else:
                w += _glyph(ch)[1] * self.width_k * size * track * 1.06
        return w

    def text(self, x, y, s, size=2.0, color=BLACK, lw=0.24, track=1.0, slope=None):
        """Write s with its baseline at y; returns the x where writing stopped."""
        r = self.rng
        slope = r.gauss(0.006, 0.02) if slope is None else slope
        wave_a, wave_l, wave_p = r.uniform(0.02, 0.06) * size, r.uniform(15, 30), r.uniform(0, 6.28)
        shear = r.gauss(0, 0.05)
        cx = x
        for ch in normalize(s):
            if ch == " ":
                cx += self.space(size) * r.uniform(0.85, 1.25)
                continue
            strokes, adv = _glyph(ch)
            th = r.gauss(0, 0.06)
            sx = self.width_k * (1 + r.gauss(0, 0.08))
            sy = 1 + r.gauss(0, 0.075)
            by = y + (cx - x) * slope + wave_a * math.sin((cx - x) / wave_l * 6.28 + wave_p) + r.gauss(0, 0.055) * size
            ox = adv * sx * size / 2
            cos_t, sin_t = math.cos(th), math.sin(th)
            # every corner of the letter lands a little off, like a hand does
            kink = {}
            for st in strokes:
                pts = []
                for u, v in st:
                    key = (round(u, 2), round(v, 2))
                    if key not in kink:
                        kink[key] = (r.gauss(0, 0.045), r.gauss(0, 0.045))
                    ku, kv = kink[key] if len(st) < 12 else (0, 0)
                    px, py = (u + ku + shear * v) * sx * size - ox, (v + kv) * sy * size
                    pts.append((cx + ox + px * cos_t - py * sin_t, by + px * sin_t + py * cos_t))
                if len(pts) > 2 or (len(pts) == 2 and math.dist(*pts) > 0.2 * size):
                    pts = self._wobble(pts, amp=0.045 * size, wavelength=0.8 * size)
                self._draw(pts, color, lw)
            cx += adv * sx * size * track * 1.06 + r.gauss(0, 0.035) * size
        return cx

    def lines(self, text, width, size):
        words, out, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if self.width(t, size) <= width or not cur:
                cur = t
            else:
                out.append(cur)
                cur = w
        if cur:
            out.append(cur)
        return out

    def para(self, x, y, segs, width, size=2.0, pitch=None, lw=0.24, indent_next=0.0):
        """Rich, wrapped text. segs: [(text, color) or (text, color, style)], style in
        {'u' underline, 'uu' double underline, 's' strike, 'box'}. Returns y of the next line."""
        pitch = pitch or size * 2.05
        words = []
        for seg in segs:
            t, col = seg[0], seg[1]
            st = seg[2] if len(seg) > 2 else None
            for w in t.split():
                words.append((w, col, st))
        rows, cur, curw = [], [], 0.0
        sp = self.space(size)
        for w in words:
            ww = self.width(w[0], size)
            avail = width - (indent_next if rows else 0)
            if cur and curw + sp + ww > avail:
                rows.append(cur)
                cur, curw = [w], ww
            else:
                curw += (sp if cur else 0) + ww
                cur.append(w)
        if cur:
            rows.append(cur)
        for i, row in enumerate(rows):
            cx = x + (indent_next if i else 0)
            slope = self.rng.gauss(0.006, 0.02)
            runs = []
            for j, (w, col, st) in enumerate(row):
                x0 = cx
                cx = self.text(cx, y, w, size, col, lw, slope=slope)
                if runs and runs[-1][0] == st and runs[-1][3] == col:
                    runs[-1][2] = cx
                else:
                    runs.append([st, x0, cx, col])
                if j < len(row) - 1:
                    cx += sp * self.rng.uniform(0.9, 1.15)
            for st, x0, x1, col in runs:
                if st in ("u", "uu"):
                    self.line(x0 - 0.3, y - 0.75, x1 + 0.4, y - 0.8, col, 0.25)
                    if st == "uu":
                        self.line(x0, y - 1.35, x1 + 0.2, y - 1.4, col, 0.25)
                elif st == "s":
                    self.line(x0 - 0.4, y + size * 0.45, x1 + 0.4, y + size * 0.5, col, 0.3)
                elif st == "box":
                    self.rect(x0 - 0.9, y - 1.0, x1 + 0.9, y + size + 1.0, col, 0.25)
            y -= pitch
        return y

    # ---------- shapes ----------

    def line(self, x0, y0, x1, y1, color=BLACK, lw=0.27, amp=None):
        d = math.hypot(x1 - x0, y1 - y0)
        bow = self.rng.gauss(0, 0.004) * d
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        nx, ny = (-(y1 - y0) / (d or 1), (x1 - x0) / (d or 1))
        pts = [(x0, y0), (mx + nx * bow, my + ny * bow), (x1, y1)]
        pts = self._wobble(pts, amp if amp is not None else 0.1, wavelength=max(6, d / 2), step=0.5)
        self._draw(pts, color, lw)

    def poly(self, pts, color=BLACK, lw=0.27, amp=0.06, closed=False):
        if closed:
            pts = list(pts) + [pts[0]]
        self._draw(self._wobble(pts, amp, wavelength=4, step=0.3), color, lw)

    def rect(self, x0, y0, x1, y1, color=BLACK, lw=0.27):
        r = self.rng
        o = lambda: r.uniform(0.1, 0.8)
        self.line(x0 - o(), y1 + r.gauss(0, 0.1), x1 + o(), y1 + r.gauss(0, 0.1), color, lw)
        self.line(x1 + r.gauss(0, 0.1), y1 + o(), x1 + r.gauss(0, 0.1), y0 - o(), color, lw)
        self.line(x1 + o(), y0 + r.gauss(0, 0.1), x0 - o(), y0 + r.gauss(0, 0.1), color, lw)
        self.line(x0 + r.gauss(0, 0.1), y0 - o(), x0 + r.gauss(0, 0.1), y1 + o(), color, lw)

    def ellipse(self, cx, cy, rx, ry, color=BLACK, lw=0.27, overlap=0.35, start=None):
        r = self.rng
        a0 = r.uniform(0, 2 * math.pi) if start is None else start
        n = max(24, int((rx + ry) * 6))
        k1, k2 = r.uniform(0.02, 0.05), r.uniform(0, 6.28)
        pts = []
        for i in range(n + 1):
            a = a0 + (2 * math.pi + overlap) * i / n
            rr = 1 + k1 * math.sin(2 * a + k2) + 0.02 * i / n
            pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)))
        self._draw(self._wobble(pts, 0.05, 3, step=0.25), color, lw)

    def arrow(self, x0, y0, x1, y1, color=BLACK, lw=0.27, head=1.2):
        self.line(x0, y0, x1, y1, color, lw)
        a = math.atan2(y1 - y0, x1 - x0)
        for s in (1, -1):
            b = a + math.pi - s * 0.5
            self.line(x1, y1, x1 + head * math.cos(b), y1 + head * math.sin(b), color, lw, amp=0.03)

    def hook(self, x, y_top, y, length, color=BLACK, lw=0.27):
        """↳ : down from (x, y_top) to y, then right with an arrowhead."""
        pts = [(x, y_top), (x + 0.05, y + 0.8), (x + 0.4, y + 0.1), (x + 1.2, y)]
        self.poly(pts, color, lw, amp=0.04)
        self.arrow(x + 1.2, y, x + length, y + self.rng.gauss(0, 0.1), color, lw, head=1.0)

    def brace(self, x, y0, y1, color=BLACK, lw=0.27, depth=1.6):
        """'}' from y0 (bottom) to y1 (top) at x, point facing right."""
        ym = (y0 + y1) / 2
        q = depth
        pts = [(x, y1), (x + q * 0.5, y1 - 0.4), (x + q * 0.5, ym + 0.8), (x + q, ym),
               (x + q * 0.5, ym - 0.8), (x + q * 0.5, y0 + 0.4), (x, y0)]
        self.poly(pts, color, lw, amp=0.05)

    def hatch(self, x0, y0, x1, y1, color=BLACK, lw=0.18, gap=0.7, angle=55):
        a = math.radians(angle)
        dx = (y1 - y0) / math.tan(a)
        x = x0 - dx
        while x < x1:
            xa, ya, xb, yb = x, y0, x + dx, y1
            if xa < x0:
                ya = y0 + (x0 - xa) * math.tan(a); xa = x0
            if xb > x1:
                yb = y1 - (xb - x1) * math.tan(a); xb = x1
            if ya < yb:
                self.line(xa, ya, xb, yb, color, lw, amp=0.03)
            x += gap
