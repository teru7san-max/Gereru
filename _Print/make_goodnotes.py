"""GoodNotes notebooks that look like the real paper notebooks.

Page 1 is the real cover: a straightened photo of the physical notebook,
read from _Print/GoodNotes/cover-photos/ (kept out of git; personal use only).
The remaining pages are plain square grid, edge to edge, like the paper pages:
no headers, numbers or icons. The page itself is a high-resolution paper image
(textured surface, grid printed as tiny marks) made by make_paper.py.

Run: python3 _Print/make_paper.py && python3 _Print/make_goodnotes.py
"""

from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent / "GoodNotes"
PHOTOS = ROOT / "cover-photos"
OUT = ROOT / "notebooks"
PAGES = 60

NOTEBOOKS = [
    # file name, cover photo, page size (mm): the real size of each notebook
    ("Унших · Reading log", "yellow-bear.jpg", (88, 125)),
    ("Хэрэгжүүлэх · Practice log", "pink-swing.jpg", (88, 125)),
    ("Сэтгэх · Thinking", "meow-cat.jpg", (80, 123)),
]


def paper_image(size_mm):
    return ROOT / f"paper-{size_mm[0]}x{size_mm[1]}.jpg"


def grid_page(c, w, h, size_mm):
    c.drawImage(str(paper_image(size_mm)), 0, 0, w, h)


def build(name, photo, size_mm, path):
    w, h = size_mm[0] * mm, size_mm[1] * mm
    c = canvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle(name)
    c.drawImage(str(PHOTOS / photo), 0, 0, w, h)
    c.showPage()
    c.beginForm("grid")
    grid_page(c, w, h, size_mm)
    c.endForm()
    for _ in range(PAGES):
        c.doForm("grid")
        c.showPage()
    c.save()


def build_template(size_mm, path):
    w, h = size_mm[0] * mm, size_mm[1] * mm
    c = canvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle(f"Grid {size_mm[0]}×{size_mm[1]}")
    grid_page(c, w, h, size_mm)
    c.showPage()
    c.save()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for _, _, size in NOTEBOOKS:
        if not paper_image(size).exists():
            raise SystemExit(f"missing {paper_image(size).name}: run python3 _Print/make_paper.py first")
    for name, photo, size in NOTEBOOKS:
        build(name, photo, size, OUT / f"{name}.pdf")
    for size in {s for _, _, s in NOTEBOOKS}:
        build_template(size, ROOT / f"grid-{size[0]}x{size[1]}.pdf")


if __name__ == "__main__":
    main()
