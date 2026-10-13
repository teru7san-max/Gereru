"""GoodNotes notebooks that look like the real paper notebooks.

Page 1 is the real cover: a straightened photo of the physical notebook,
read from _Print/GoodNotes/cover-photos/ (kept out of git; personal use only).
The remaining pages are plain square grid, edge to edge, like the paper pages:
no headers, numbers or icons.

Grid spacing (2.85 mm) and colours were measured from a photo of a real page.
Run: python3 _Print/make_goodnotes.py
"""

from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent / "GoodNotes"
PHOTOS = ROOT / "cover-photos"
OUT = ROOT / "notebooks"
PAGES = 60

GRID = 2.85 * mm
PAPER = (0xF5 / 255, 0xF1 / 255, 0xE8 / 255)
LINE = (0xA9 / 255, 0xA5 / 255, 0x9D / 255)
LINE_W = 0.3

NOTEBOOKS = [
    # file name, cover photo, page size (mm): the real size of each notebook
    ("Унших · Reading log", "yellow-bear.jpg", (88, 125)),
    ("Хэрэгжүүлэх · Practice log", "pink-swing.jpg", (88, 125)),
    ("Сэтгэх · Thinking", "meow-cat.jpg", (80, 123)),
]


def grid_page(c, w, h):
    c.setFillColorRGB(*PAPER)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setStrokeColorRGB(*LINE)
    c.setLineWidth(LINE_W)
    # centre the grid so the partial squares at opposite edges are equal
    x = (w % GRID) / 2
    while x < w:
        c.line(x, 0, x, h)
        x += GRID
    y = (h % GRID) / 2
    while y < h:
        c.line(0, y, w, y)
        y += GRID


def build(name, photo, size_mm, path):
    w, h = size_mm[0] * mm, size_mm[1] * mm
    c = canvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle(name)
    c.drawImage(str(PHOTOS / photo), 0, 0, w, h)
    c.showPage()
    c.beginForm("grid")
    grid_page(c, w, h)
    c.endForm()
    for _ in range(PAGES):
        c.doForm("grid")
        c.showPage()
    c.save()


def build_template(size_mm, path):
    w, h = size_mm[0] * mm, size_mm[1] * mm
    c = canvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle(f"Grid {size_mm[0]}×{size_mm[1]}")
    grid_page(c, w, h)
    c.showPage()
    c.save()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, photo, size in NOTEBOOKS:
        build(name, photo, size, OUT / f"{name}.pdf")
    for size in {s for _, _, s in NOTEBOOKS}:
        build_template(size, ROOT / f"grid-{size[0]}x{size[1]}.pdf")


if __name__ == "__main__":
    main()
