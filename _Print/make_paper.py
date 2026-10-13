"""Realistic paper for the GoodNotes notebooks.

Modelled on close-up photos of the real pages: a bumpy, fibrous cream surface and
grid lines printed as rows of tiny irregular marks (about 0.3 mm apart) over a faint
hairline. Rendered as a high-resolution image so it still reads as paper when zoomed in.

Each paper is (size in mm, grid spacing in mm or None for blank, pixels per mm).
Outputs _Print/GoodNotes/paper-<w>x<h>-<kind>.jpg.
Run: python3 _Print/make_paper.py   (needs numpy, scipy, Pillow)
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

OUT = Path(__file__).resolve().parent / "GoodNotes"
BASE_PPM = 28.35           # the look was tuned at 720 dpi; other resolutions scale from it
MARK_STEP_MM = 0.3         # spacing of the printed marks along a grid line
PAPER_RGB = np.array([236, 230, 219], float)
INK_RGB = np.array([98, 94, 89], float)

PAPERS = [
    # (w, h) mm, grid mm (None = blank), px per mm
    ((88, 125), 3.0, 28.35),     # Benstore passport, 3 mm grid (yellow, pink, black)
    ((88, 125), 4.0, 28.35),     # Benstore passport, 4 mm grid (Bloom, Cherry)
    ((88, 125), None, 28.35),    # Benstore passport, blank (Lucky, Bag)
    ((80, 123), 2.85, 28.35),    # Meow notebook
    ((176, 250), 5.0, 14.0),     # B5, 5 mm grid
]


def kind_name(grid_mm):
    return "blank" if grid_mm is None else f"{grid_mm:g}mm"


def paper_path(size_mm, grid_mm):
    return OUT / f"paper-{size_mm[0]}x{size_mm[1]}-{kind_name(grid_mm)}.jpg"


def surface(w, h, rng, ppm):
    """Luminance multiplier around 1.0: emboss shading, mottling, fibres and specks."""
    k = ppm / BASE_PPM
    noise = rng.standard_normal((h, w)).astype(np.float32)
    height = (gaussian_filter(noise, 1.6 * k) * 0.8 + gaussian_filter(noise, 5 * k) * 1.6
              + gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 11 * k) * 1.0)
    del noise
    # light from the top-left: slope of the height map gives the shading
    shade = (np.roll(height, 1, 1) - np.roll(height, -1, 1)) + (np.roll(height, 1, 0) - np.roll(height, -1, 0))
    del height
    shade /= shade.std() + 1e-9
    lum = 1 + 0.03 * shade
    del shade
    mottle = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 90 * k)
    lum += 0.010 * mottle / (mottle.std() + 1e-9)
    del mottle
    grain = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), max(0.7 * k, 0.4))
    lum += 0.010 * grain / (grain.std() + 1e-9)
    del grain

    # fibres: short slightly curved strands, a little lighter or darker than the paper
    fib = Image.new("L", (w, h), 128)
    d = ImageDraw.Draw(fib)
    area_mm2 = (w / ppm) * (h / ppm)
    for _ in range(int(area_mm2 * 6)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ang = rng.uniform(0, np.pi)
        length = rng.uniform(0.25, 1.4) * ppm
        bend = rng.uniform(-0.6, 0.6)
        tone = 128 + (rng.uniform(10, 26) if rng.random() < 0.6 else -rng.uniform(8, 20))
        pts = []
        for t in np.linspace(0, 1, 6):
            a = ang + bend * (t - 0.5)
            pts.append((x + np.cos(a) * length * t, y + np.sin(a) * length * t))
        d.line(pts, fill=int(tone), width=1)
    fibres = gaussian_filter((np.asarray(fib, np.float32) - 128) / 128, max(0.6 * k, 0.4))
    lum += 0.18 * fibres
    del fibres

    # a few tiny specks
    for _ in range(int(area_mm2 * 0.03)):
        x, y = int(rng.uniform(2, w - 3)), int(rng.uniform(2, h - 3))
        lum[y - 1:y + 2, x - 1:x + 2] *= rng.uniform(0.82, 0.93)
    return lum


def stamps(rng, size, n=96):
    """Tiny glyph-like ink marks (~0.2 mm): squares, triangles, rings and letter-like strokes,
    like the printed microtext the real grid lines are made of."""
    bank = []
    S = 48
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
        bank.append(np.asarray(small, np.float32) / 255)
    return bank


def ink_layer(w, h, rng, ppm, grid_mm):
    k = ppm / BASE_PPM
    alpha = np.zeros((h, w), np.float32)
    step = grid_mm * ppm
    bank = stamps(rng, size=max(3, int(round(6 * k))))
    s = bank[0].shape[0]
    mark = MARK_STEP_MM * ppm
    xs = np.arange((w % step) / 2, w, step)
    ys = np.arange((h % step) / 2, h, step)

    def stamp(cx, cy, strength):
        g = bank[rng.integers(len(bank))]
        if rng.random() < 0.5:
            g = g.T
        x0, y0 = int(round(cx - s / 2)), int(round(cy - s / 2))
        if x0 < 0 or y0 < 0 or x0 + s > w or y0 + s > h:
            return
        region = alpha[y0:y0 + s, x0:x0 + s]
        np.maximum(region, g * strength, out=region)

    for x in xs:
        drift = gaussian_filter(rng.standard_normal(int(h / mark) + 2), 6) * 4
        hair = slice(int(round(x)), int(round(x)) + 1)
        alpha[:, hair] = np.maximum(alpha[:, hair], 0.10)
        for i, y in enumerate(np.arange(rng.uniform(0, mark), h, mark)):
            if rng.random() < 0.03:
                continue  # occasional missing mark
            stamp(x + rng.normal(0, 0.25 * k), y + rng.normal(0, 0.3 * k), np.clip(0.92 + 0.08 * drift[i], 0.6, 1.0))
    for y in ys:
        drift = gaussian_filter(rng.standard_normal(int(w / mark) + 2), 6) * 4
        row = slice(int(round(y)), int(round(y)) + 1)
        alpha[row, :] = np.maximum(alpha[row, :], 0.10)
        for i, x in enumerate(np.arange(rng.uniform(0, mark), w, mark)):
            if rng.random() < 0.03:
                continue
            stamp(x + rng.normal(0, 0.3 * k), y + rng.normal(0, 0.25 * k), np.clip(0.92 + 0.08 * drift[i], 0.6, 1.0))
    # ink sits unevenly on the fibres
    alpha *= np.clip(0.9 + 0.15 * gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 1.2 * k) * 3,
                     0.6, 1.1)
    return np.clip(gaussian_filter(alpha, max(0.55 * k, 0.4)) * 1.15, 0, 1)


def make(size_mm, grid_mm, ppm, seed=7):
    rng = np.random.default_rng(seed)
    w, h = int(round(size_mm[0] * ppm)), int(round(size_mm[1] * ppm))
    lum = surface(w, h, rng, ppm)
    img = PAPER_RGB.astype(np.float32)[None, None, :] * lum[..., None]
    del lum
    if grid_mm is not None:
        a = ink_layer(w, h, rng, ppm, grid_mm)[..., None]
        # multiply blend: ink darkens the paper underneath, so the texture shows through
        img *= 1 - a * (1 - INK_RGB / PAPER_RGB).astype(np.float32)
    return Image.fromarray(np.clip(img, 0, 255).astype("uint8"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for size, grid, ppm in PAPERS:
        path = paper_path(size, grid)
        make(size, grid, ppm).save(path, quality=88, subsampling=0, optimize=True,
                                   dpi=(round(ppm * 25.4), round(ppm * 25.4)))
        print(path.name)


if __name__ == "__main__":
    main()
