---
title: October 2026 · Week 1 (TN)
tags: [journal, weekly, tn, gym]
created: 2026-10-12
---

# October 2026 · Week 1 → TN cards

10.1–10.7 as 82×116 mm traveler's-notebook cards.

- **PDF, one card per page:** [[October_2026_W1_TN.pdf]]
- **PDF to print (A4, 4 cards per sheet, crop marks, sheets in reverse order):** [[October_2026_W1_TN_print_A4_reversed.pdf]]. Print at 100% and check the 90 mm scale bar.

16 pages:

| Page | What it is |
|------|------------|
| 1 | Cover: LV, XP this week and contents |
| 2 | **The week**: quests × days in one grid, each value coloured by done / half / missed. Each row ends with the XP it earned and the XP it missed, rows sorted by XP missed, with the quest rules underneath |
| 3 | **W2 plan**: the 3 biggest gaps with tick boxes for 10.8–10.14, what to keep, and new quests |
| 4–15 | **Days**: one day card per day, plus a gym card on gym days |
| 16 | Notes |

## How it's built

- `week1.json` holds **only the raw week**: each day's steps, sleep, food, spending, journal and photo count, plus every gym session's sets.
- `../_tn/build.py` scores each day against the XP rules and works out every average, best day, gap, "what I lacked" line and next-week quest from that data. Nothing in the cards is typed by hand.
- `photos/` holds `<date>-<n>.jpg`, for example `10.3-2.jpg`.

## Making week 2

1. Create a `2026-10 Week 2` folder with a `photos/` subfolder.
2. Copy `week1.json` into it as `week2.json`.
3. Change `week`, `range`, `pdf_name` and `xp_before_week` to `2640`. Empty `locked_quests` so bike and focus count.
4. Fill in the 7 `days` and the `sessions`.
5. Run:

```sh
python3 ../_tn/build.py week2.json --pdf
```

If the page count isn't a multiple of 4, blank NOTES pages are added so every A4 sheet is full.
