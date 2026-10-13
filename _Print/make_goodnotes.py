"""GoodNotes notebooks that look like the real paper notebooks.

Page 1 is the real cover: a straightened photo of the physical notebook (or of the
shop's product photo), read from _Print/GoodNotes/cover-photos/ (kept out of git;
personal use only). The remaining 60 pages are paper edge to edge, no headers,
numbers or icons: grid or blank to match each real notebook, drawn from the
high-resolution paper images made by make_paper.py.

Run: python3 _Print/make_paper.py && python3 _Print/make_goodnotes.py
"""

from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from make_paper import kind_name, paper_path

ROOT = Path(__file__).resolve().parent / "GoodNotes"
PHOTOS = ROOT / "cover-photos"
OUT = ROOT / "notebooks"
PAGES = 60

NOTEBOOKS = [
    # file name, cover photo (None = no cover page), page size (mm), grid (mm, None = blank)
    # Grid and blank pages follow each real notebook's spec.
    ("Унших · Reading log", "yellow-bear.jpg", (88, 125), 3.0),
    ("Хэрэгжүүлэх · Practice log", "pink-swing.jpg", (88, 125), 3.0),
    ("Сэтгэх · Thinking", "meow-cat.jpg", (80, 123), 2.85),
    ("Sport im Haus · 3mm grid", "black-sport-im-haus.jpg", (88, 125), 3.0),
    ("Bloom · 4mm grid", "bloom.jpg", (88, 125), 4.0),
    ("Cherry · 4mm grid", "cherry.jpg", (88, 125), 4.0),
    ("Lucky · blank", "lucky.jpg", (88, 125), None),
    ("Travel Bag · blank", "travel-bag.jpg", (88, 125), None),
    ("B5 · 5mm grid", None, (176, 250), 5.0),
]


def grid_page(c, w, h, size_mm, grid_mm):
    c.drawImage(str(paper_path(size_mm, grid_mm)), 0, 0, w, h)


def build(name, photo, size_mm, grid_mm, path):
    w, h = size_mm[0] * mm, size_mm[1] * mm
    c = canvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle(name)
    if photo:
        c.drawImage(str(PHOTOS / photo), 0, 0, w, h)
        c.showPage()
    c.beginForm("grid")
    grid_page(c, w, h, size_mm, grid_mm)
    c.endForm()
    for _ in range(PAGES):
        c.doForm("grid")
        c.showPage()
    c.save()


def build_template(size_mm, grid_mm, path):
    w, h = size_mm[0] * mm, size_mm[1] * mm
    c = canvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle(f"{size_mm[0]}×{size_mm[1]} {kind_name(grid_mm)}")
    grid_page(c, w, h, size_mm, grid_mm)
    c.showPage()
    c.save()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for _, _, size, grid in NOTEBOOKS:
        if not paper_path(size, grid).exists():
            raise SystemExit(f"missing {paper_path(size, grid).name}: run python3 _Print/make_paper.py first")
    for name, photo, size, grid in NOTEBOOKS:
        build(name, photo, size, grid, OUT / f"{name}.pdf")
    for size, grid in {(s, g) for _, _, s, g in NOTEBOOKS}:
        build_template(size, grid, ROOT / f"template-{size[0]}x{size[1]}-{kind_name(grid)}.pdf")


if __name__ == "__main__":
    main()
