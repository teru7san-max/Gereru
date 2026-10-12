---
title: October 2026 · Week 1 (TN)
tags: [journal, weekly, tn, gym]
created: 2026-10-12
---

# October 2026 · Week 1 → TN cards

10.1–10.7 as 82×116 mm traveler's-notebook cards.

- **PDF, one card per page:** [[October_2026_W1_TN.pdf]]
- **PDF to print (A4, 4 cards per sheet, crop marks, sheets in reverse order):** [[October_2026_W1_TN_print_A4_reversed.pdf]]. Print at 100% and check the 90 mm scale bar.

| # | Section | Pages |
|---|---------|-------|
| — | Cover: LV, XP and contents | 1 |
| 1 | **Дүгнэлт / Summary**: week at a glance, weekly average, habit grid, XP rules | 2–5 |
| 2 | **Өдөр бүр / Day by day**: a day card for each day, followed by its gym card | 6–17 |
| 3 | **Дутсан зүйл / What I lacked**: XP left on the table, days hit, week 2 quests | 18–20 |

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
