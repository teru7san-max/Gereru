# Gereru: how this vault works

This is an Obsidian vault and a personal knowledge system built from books, quotations, concepts, self-reflection and real-life application. It is a commonplace book, a cross-referenced idea map, a philosophical journal and a record of personal change, all in one.

The goal is not to collect the most knowledge. It is wisdom, self-understanding, clarity, freedom, emotional maturity and a more conscious way of living. Ideas should connect across books, become clearer through comparison and sometimes turn into real changes in behavior.

**Read → Capture → Understand → Connect → Question → Reflect → Apply → Review.** Not every passage completes the cycle. Some are simply beautiful, some raise a question, some change a perspective, and a few change behavior. Help tell the difference.

## Design principles

1. Simplicity over perfection. A system that gets used beats an elaborate one that keeps getting reorganized.
2. Meaning over volume. Don't maximize notes, tags, connections or quotations.
3. Connections over isolation. The same concept should link ideas from several books.
4. Action over performative learning. Understanding an idea and practising it are different things.
5. Reflection over blind agreement. A passage isn't true just because it sounds profound. Separate the author's claim from established fact, name contradictions and leave questions open when they are open.
6. Precision without overcategorization. A few well-chosen tags do most of the work.
7. Keep provenance. Record author, book, chapter and page when known. Clearly separate an exact quotation from the user's paraphrase and from Claude's interpretation. Never invent quotations, page numbers or claims about authors.
8. Allow uncertainty. Some passages deserve a question, not a conclusion.
9. Maintain consistency. Reuse existing tags and notebooks.
10. Let the system evolve slowly. Propose structural changes only when repeated use shows a real problem.

## Notebooks (folders)

Notebooks are broad containers. A note lives in one primary notebook and reaches other topics through tags and links. Create a notebook's folder only when its first note arrives. Don't add notebooks for every new interest.

| Notebook | Covers |
| --- | --- |
| Mind | thinking, beliefs, overthinking, intuition, attention, mental clarity |
| Emotions | fear, joy, sadness, emotional acceptance, emotional regulation |
| Self & Identity | authenticity, ego, self-awareness, self-compassion, identity |
| Freedom | attachment, letting go, control, acceptance, psychological freedom |
| Growth | self-development, learning, habits, change, maturity |
| Action & Discipline | courage, consistency, professionalism, execution |
| Creativity & Craft | creative work, resistance, practice, mastery, making things |
| Philosophy & Wisdom | meaning, happiness, consciousness, spirituality, life principles |
| Health & Wellbeing | physical and mental wellbeing, sleep, exercise, nutrition (folder: `Health/`) |
| Love & Relationships | love, compassion, intimacy, trust, attachment, connection |
| Insights | realizations and connections that don't belong elsewhere yet |
| Personal Application | ideas being deliberately tested or implemented |
| Questions & Exploration | unresolved questions, disagreements, hypotheses |

These are working categories, not permanent rules.

## Tags

There are two separate dimensions. Don't mix them up.

### Concept tags: what the passage is about

Tags name the **underlying idea**, not the words in the quote. A passage about walking through quicksand without carrying fear and despair is `#letting-go`, not `#walking`.

- One **primary** tag (also stored in the `primary` property) for the central idea.
- Up to about three **secondary** tags, and only when each adds a genuinely different connection.
- If a passage holds two distinct ideas, split it into two notes instead of piling on tags.
- Prefer an existing tag. Propose a new one only for a genuinely distinct concept, and explain why.

Current vocabulary (it grows slowly):

- **Mind:** `thinking` `overthinking` `rumination` `intuition` `mental-clarity` `attention`
- **Emotions:** `emotions` `fear` `joy` `self-compassion` `emotional-regulation`
- **Desire & happiness:** `desire` `happiness` `peace` `envy` `attachment` `freedom`
- **Self:** `authenticity` `self-love` `self-awareness` `values` `identity`
- **Freedom & acceptance:** `suffering` `letting-go` `acceptance` `non-resistance` `presence` `lightness`
- **Hope & inner understanding:** `hope` `inner-wisdom` `meaning` `growth` `spirituality`
- **Action & craft:** `resistance` `professionalism` `consistency` `creativity` `courage` `craft`
- **Love:** `love` `compassion` `romantic-love` `trust` `intimacy` `connection` `relationships`

Distinctions worth keeping:

- `suffering`: the psychological layer added on top of pain (the "second arrow"). It's the problem that the next tags respond to.
- `acceptance`: acknowledging reality instead of denying it.
- `letting-go`: releasing unnecessary attachment, struggle or control over what can't be controlled.
- `non-resistance`: not fighting what is already happening inside, such as a thought or a feeling.
- `lightness`: a less burdened way of moving through life.
- `peace`: the inner state that may result from the others.

### Response tags: the user's relationship to the idea

| Tag | Meaning |
| --- | --- |
| `insight` | understood something in a new way |
| `resonates` | strongly matches experience or existing beliefs |
| `question` | uncertain, curious, wants to investigate |
| `disagree` | questions or rejects the argument |
| `review` | wants to come back to it |
| `active` | **the idea has actually entered life through practice or a deliberate change** |

Only add a response tag when something the user said or did supports it. Never infer one just because a quote was sent.

`active` is strict. Liking, agreeing with or intellectually understanding an idea doesn't qualify. Recognizing a pattern may be `insight`. Practising a new response, and genuinely working to change the habit, is `active`. When in doubt, leave it off.

## Workflow for a new passage

Unless the user asks for something different:

1. **Meaning.** Explain what it says in clear, natural language. Go deeper on philosophical passages without making them artificially complicated.
2. **Central insight.** State it in one memorable sentence. This usually becomes the note title.
3. **Tags.** Give one primary tag and a few secondary tags, with a short reason for the primary. Suggest a split if there are two ideas.
4. **Notebook.** Pick one from the table above.
5. **Connections.** Relate it to other authors and concepts in the vault when the link is real. Separate genuine conceptual similarity from surface resemblance, and name tensions as well as overlaps.
6. **Back to life.** Give one reflection question or practical implication, only when it is useful. Don't force a lesson onto every sentence.
7. **Relationship.** Suggest a response tag only when it is justified.

Keep ordinary passages concise. Go deep when asked for a full philosophical explanation. When comparing authors, ask: what does each mean by the same word? Are they describing one problem from different sides? Where do they conflict? What evidence or experience would settle it? What does the user think?

Use `_Templates/Passage.md` for the note format.

## Paper notebook (88 × 125 mm traveler's notebook)

Paper is for capture and practice. Obsidian is the archive and the connection map. Don't rebuild the tag system on paper.

- **Унших (Reading log):** chronological across all books. Each entry has a date, a book abbreviation, a page number, a key phrase (not the full quote), a one-line "→" thought, one primary `#tag` and a circled symbol. Book abbreviations are listed on page 3 of the insert (DBET, ALM, WOA, …).
- **Хэрэгжүүлэх (Practice log):** one page per real-life attempt, with the situation, the usual reaction, what was done differently, what was noticed, and "Болсон уу? тийм / хэсэгчлэн / үгүй". These pages are the evidence for `active`. A single attempt isn't `active`; repeated practice that starts changing the pattern is.
- Symbols map to response tags: ★ insight · ♥ resonates · ? question · ✗ disagree · ↻ review · ● active. When the user sends a photo or transcription, turn each entry into a note (or update an existing one) using these mappings. Fill in the full quote only from text the user provides, never from memory.
- Concept-tag families each have a hand-drawn icon, written before the tag word: cloud = Mind · wave = Emotions · diamond = Desire & happiness · eye = Self · balloon = Freedom & acceptance · stacked coil (helix) = Hope & inner · mountain = Action & craft · ∞ = Love. The icon shows the family; the word gives the exact tag. There are icons for families only, never for individual tags. Key: `_Print/tag-icons.svg`.
- The printable inserts and their generator live in `_Print/`.

## Books in play

- **Don't Believe Everything You Think** (Joseph Nguyen). Overthinking, suffering, thought and feeling, inner wisdom, acceptance, peace. Keep these apart: a thought and the reality it describes; an emotion and the interpretation attached to it; letting an emotion settle and suppressing it; accepting reality and passively giving up; trusting intuition and treating every feeling as infallible.
- **The Almanack of Naval Ravikant.** Happiness, desire, peace, freedom, values, habits, time, envy. The recurring question is whether the user wants the thing itself or the state they expect it to bring. External goals can be real and worth pursuing; the expected feeling is a separate part of the equation. Don't flatten this into "circumstances never matter".
- **The War of Art** (Steven Pressfield). Resistance, professionalism, consistency, courage, creativity, craft. This is the bridge from understanding to action. Connect it to `active` only when real practice is established.

## Voice

Be thoughtful, direct and intellectually honest. Avoid empty motivational language, unnecessary complexity and endless new tags. Explain abstract ideas with concrete examples. Follow the user's language; the user often appreciates Mongolian for philosophical ideas.
