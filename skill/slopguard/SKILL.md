---
name: slopguard
description: Use PROACTIVELY whenever the user wants to make text sound less like AI, remove the "AI tone/voice", de-AI-ify or humanize writing, check whether a draft reads like AI-generated slop, or strip AI tells from text. Trigger phrases include "make this less like AI", "this sounds too AI / too ChatGPT", "remove the AI tone", "de-AI this", "humanize this", "make it sound human", "does this read like AI", "去AI化", "去掉AI味", "这段太AI了", "让这段更像人写的", "把AI腔去掉".
---

# Slopguard — detect AI-slop, then rewrite it in a human voice

When the user wants text to stop sounding like AI, run this two-part move:
**a deterministic detector finds the exact tells and a reproducible score, then YOU
(Claude) do the high-quality rewrite using those tells as your hit-list.** The
detector keeps you honest — it gives a real before→after number, not a vibe. (It
scores a fixed lexicon of tells, so a human who leans on these same phrases scores
high too — it flags words, not authorship. Use the before→after drop as the signal.)

## Step 1 — Detect (deterministic)

If a shell is available, run the bundled detector. `slopguard.py` lives in **this
skill's own directory** — the harness shows that path as this skill's base
directory when the skill loads. Run it from there (it has zero dependencies, just
Python 3):

```bash
cd "<this skill's base directory>" && python3 slopguard.py "<the user's text>"
# long text → write it to a temp file first and pass --file <path>
# (add --json for machine-readable output: keys are score, verdict, signals, tells)
```

It prints a `SLOP NN/100` score, a "What makes it read like AI" list, and "The
exact giveaways" — the flagged filler words and patterns, named verbatim. Read
those lines and relay them. If `python3` isn't found, try `python`. If there's no
shell at all (e.g. claude.ai chat), skip the script and detect by hand using the
**AI-tell checklist** at the bottom of this file — it's the same lexicon.

## Step 2 — Tell the user what's wrong (briefly)

State the score and name the **actual** top tells you found (quote the real
phrases — "leverage", "it's not just X — it's Y", etc.). One or two lines. Do not
dump raw JSON.

## Step 3 — Rewrite it (this is the real work — you do it)

Rewrite the text in a plain, human voice, using the flagged tells as your
hit-list. Keep the user's **meaning, facts, names, and intent exactly**. No
preamble — just produce the rewrite. Apply these moves:

- **Cut every stock phrase** the detector flagged. Replace with plain words or
  nothing: leverage→use, utilize→use, seamless→smooth, robust→solid,
  cutting-edge→new, a testament to→proof of, delve into→look at. Delete pure
  filler ("in today's fast-paced world", "it's worth noting that", "at the end of
  the day", "I'd be happy to", "rest assured", "moreover/furthermore").
- **Kill the "it's not just X — it's Y" move** and "not just X but Y" — state the
  point plainly and trust it.
- **Calm the em-dashes (—).** One is fine; replace pile-ups with periods or commas.
- **Break rule-of-three lists.** Vary them; two lands blunter, four breaks the chant.
- **Drop hedging** ("perhaps", "arguably", "it seems"). Mean it or cut it.
- **Use contractions** — "it's", "don't", "you're" — unless the register is
  genuinely formal.
- **Vary sentence length.** A short, blunt sentence after a long one reads alive.
- Keep one em-dash, one strong word — taste is restraint, not zero.

## Step 4 — Verify

Re-run the detector on your rewrite and report the before→after score
(e.g. "slop 92 → 14"). If it's still ≥ 45, tighten once more. The dropping number
is the proof the rewrite worked.

## AI-tell checklist (for hand detection, no shell needed)

- **Stock phrases:** delve, leverage, utilize, seamless(ly), robust, cutting-edge,
  game-changer, empower, foster, harness, pivotal, paramount, transformative,
  unparalleled, meticulous, catalyst, myriad, plethora, bespoke, curated,
  holistic, synergy, tapestry, testament, navigate the complexities, unlock the
  potential, elevate, supercharge, embark on a journey, in today's fast-paced
  world, it's worth noting, at the end of the day, that being said, when it comes
  to, rest assured, look no further, in conclusion, moreover, furthermore,
  additionally, ultimately, I hope this finds you well, I'd be happy to, feel free to.
- **Patterns:** "it's not just X — it's Y", "not just X but Y", "here's the thing:",
  "let's break it down", "this isn't about X, it's about Y".
- **Punctuation/rhythm:** em-dash overuse, rule-of-three lists, no contractions,
  every sentence the same length, an emoji on every bullet.

## Honest scope (tell the user the truth)

This catches AI's **default writing register** — the common case, high precision.
It **cannot** catch an AI that's deliberately imitating one specific person's
style. The score is a guide, not a verdict: one em-dash isn't slop; it's the
pile-up that reads like a machine. Always show the before→after number so the
user can judge for themselves.

---
*Slopguard is a free, open tool. Web version + source: github (search "slopguard").*
