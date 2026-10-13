"""Realistic grid paper for the GoodNotes notebooks.

Modelled on close-up photos of the real pages: a bumpy, fibrous cream surface and
grid lines printed as rows of tiny irregular marks (about 0.2 mm apart) over a faint
hairline, 2.85 mm squares. Rendered as a high-resolution image so it still reads as
paper when zoomed in.

Outputs _Print/GoodNotes/paper-<w>x<h>.jpg for each notebook size.
Run: python3 _Print/make_paper.py   (needs numpy, scipy, Pillow)
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

OUT = Path(__file__).resolve().parent / "GoodNotes"
PX_PER_MM = 28.35          # 720 dpi
GRID_MM = 2.85
MARK_STEP_MM = 0.3         # spacing of the printed marks along a grid line
PAPER_RGB = np.array([236, 230, 219], float)
INK_RGB = np.array([98, 94, 89], float)


def surface(w, h, rng):
    """Luminance multiplier around 1.0: emboss shading, mottling, fibres and specks."""
    noise = rng.standard_normal((h, w))
    height = (gaussian_filter(noise, 1.6) * 0.8 + gaussian_filter(noise, 5) * 1.6
              + gaussian_filter(rng.standard_normal((h, w)), 11) * 1.0)
    # light from the top-left: slope of the height map gives the shading
    shade = (np.roll(height, 1, 1) - np.roll(height, -1, 1)) + (np.roll(height, 1, 0) - np.roll(height, -1, 0))
    shade /= shade.std() + 1e-9
    mottle = gaussian_filter(rng.standard_normal((h, w)), 90)
    mottle /= mottle.std() + 1e-9
    grain = gaussian_filter(rng.standard_normal((h, w)), 0.7)
    grain /= grain.std() + 1e-9
    lum = 1 + 0.03 * shade + 0.010 * mottle + 0.010 * grain

    # fibres: short slightly curved strands, a little lighter or darker than the paper
    fib = Image.new("L", (w, h), 128)
    d = ImageDraw.Draw(fib)
    area_mm2 = (w / PX_PER_MM) * (h / PX_PER_MM)
    for _ in range(int(area_mm2 * 6)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ang = rng.uniform(0, np.pi)
        length = rng.uniform(0.25, 1.4) * PX_PER_MM
        bend = rng.uniform(-0.6, 0.6)
        tone = 128 + (rng.uniform(10, 26) if rng.random() < 0.6 else -rng.uniform(8, 20))
        pts = []
        for t in np.linspace(0, 1, 6):
            a = ang + bend * (t - 0.5)
            pts.append((x + np.cos(a) * length * t, y + np.sin(a) * length * t))
        d.line(pts, fill=int(tone), width=1)
    fibres = gaussian_filter((np.asarray(fib, float) - 128) / 128, 0.6)
    lum += 0.18 * fibres

    # a few tiny specks
    for _ in range(int(area_mm2 * 0.03)):
        x, y = int(rng.uniform(2, w - 3)), int(rng.uniform(2, h - 3))
        lum[y - 1:y + 2, x - 1:x + 2] *= rng.uniform(0.82, 0.93)
    return lum


def stamps(rng, n=96, size=6):
    """Tiny glyph-like ink marks (~0.2 mm): squares, triangles, rings and letter-like strokes,
    like the printed microtext the real grid lines are made of."""
    bank = []
    S = size * 8
    lw = 13
    for _ in range(n):
        im = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(im)
        lo, hi = S * 0.2, S * 0.8
        jit = lambda: rng.uniform(-7, 7)
        kind = rng.integers(0, 5)
        if kind == 0:      # square-ish
            d.polygon([(lo + jit(), lo + jit()), (hi + jit(), lo + jit()), (hi + jit(), hi + jit()),
                       (lo + jit(), hi + jit())], outline=255, width=lw)
        elif kind == 1:    # triangle
            d.polygon([(S / 2 + jit(), lo + jit()), (hi + jit(), hi + jit()), (lo + jit(), hi + jit())],
                      outline=255, width=lw)
        elif kind == 2:    # ring
            d.ellipse([lo + jit(), lo + jit(), hi + jit(), hi + jit()], outline=255, width=lw)
        elif kind == 3:    # letter-like: a stem and one or two arms
            x = S / 2 + jit()
            d.line([(x, lo), (x + jit(), hi)], fill=255, width=lw)
            for _ in range(rng.integers(1, 3)):
                y = rng.uniform(lo, hi)
                d.line([(x, y), (x + rng.choice([-1, 1]) * rng.uniform(12, 24), y + jit())], fill=255, width=lw)
        else:              # cross / x
            d.line([(lo + jit(), lo + jit()), (hi + jit(), hi + jit())], fill=255, width=lw)
            d.line([(hi + jit(), lo + jit()), (lo + jit(), hi + jit())], fill=255, width=lw)
        small = im.resize((size, size), Image.LANCZOS)
        bank.append(np.asarray(small, float) / 255)
    return bank


def ink_layer(w, h, rng):
    alpha = np.zeros((h, w))
    step = GRID_MM * PX_PER_MM
    bank = stamps(rng)
    s = bank[0].shape[0]
    mark = MARK_STEP_MM * PX_PER_MM
    xs = np.arange((w % step) / 2, w, step)
    ys = np.arange((h % step) / 2, h, step)

    def stamp(cx, cy, strength):
        k = bank[rng.integers(len(bank))]
        if rng.random() < 0.5:
            k = k.T
        x0, y0 = int(round(cx - s / 2)), int(round(cy - s / 2))
        if x0 < 0 or y0 < 0 or x0 + s > w or y0 + s > h:
            return
        region = alpha[y0:y0 + s, x0:x0 + s]
        np.maximum(region, k * strength, out=region)

    for x in xs:
        drift = gaussian_filter(rng.standard_normal(int(h / mark) + 2), 6) * 4
        hair = slice(max(int(round(x)) - 0, 0), int(round(x)) + 1)
        alpha[:, hair] = np.maximum(alpha[:, hair], 0.10)
        for i, y in enumerate(np.arange(rng.uniform(0, mark), h, mark)):
            if rng.random() < 0.03:
                continue  # occasional missing mark
            stamp(x + rng.normal(0, 0.25), y + rng.normal(0, 0.3), np.clip(0.92 + 0.08 * drift[i], 0.6, 1.0))
    for y in ys:
        drift = gaussian_filter(rng.standard_normal(int(w / mark) + 2), 6) * 4
        row = slice(int(round(y)), int(round(y)) + 1)
        alpha[row, :] = np.maximum(alpha[row, :], 0.10)
        for i, x in enumerate(np.arange(rng.uniform(0, mark), w, mark)):
            if rng.random() < 0.03:
                continue
            stamp(x + rng.normal(0, 0.3), y + rng.normal(0, 0.25), np.clip(0.92 + 0.08 * drift[i], 0.6, 1.0))
    # ink sits unevenly on the fibres
    alpha *= np.clip(0.9 + 0.15 * gaussian_filter(rng.standard_normal((h, w)), 1.2) * 3, 0.6, 1.1)
    return np.clip(gaussian_filter(alpha, 0.55) * 1.15, 0, 1)


def make(size_mm, seed=7):
    rng = np.random.default_rng(seed)
    w, h = int(round(size_mm[0] * PX_PER_MM)), int(round(size_mm[1] * PX_PER_MM))
    lum = surface(w, h, rng)
    paper = PAPER_RGB[None, None, :] * lum[..., None]
    a = ink_layer(w, h, rng)[..., None]
    # multiply blend: ink darkens the paper underneath, so the texture shows through
    img = paper * (1 - a * (1 - INK_RGB / PAPER_RGB))
    return Image.fromarray(np.clip(img, 0, 255).astype("uint8"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for size in ((88, 125), (80, 123)):
        make(size).save(OUT / f"paper-{size[0]}x{size[1]}.jpg", quality=88, subsampling=0, optimize=True,
                        dpi=(720, 720))


if __name__ == "__main__":
    main()
