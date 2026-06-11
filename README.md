# Slopguard

Find out if a piece of text sounds like it was written by AI — and get a quick first-pass cleanup on the spot.

Everyone uses AI to write now, and AI has a "voice" — the stock phrases like *leverage* and *seamless*, the "it's not just X, it's Y" move, the dramatic dashes. Slopguard catches that voice and points at the exact words giving it away, then rewrites them in plain language.

It runs entirely in your browser. Nothing you paste ever leaves the page — there's no server and no tracking.

**[→ Try it live](https://allenwu-blip.github.io/slopguard/)**

## Three ways to use it

**1. The web tool.** Open [the page](https://allenwu-blip.github.io/slopguard/), paste your text, read the verdict, copy the cleaner version. That's it.

**2. The command line.** One file, no dependencies, Python 3.8+:

```bash
python slopguard.py "your text here"
python slopguard.py --file draft.txt --fix      # also print a de-slopped draft
echo "some text" | python slopguard.py --json    # machine-readable
```

**3. A Claude Code skill.** This is where it gets good. Copy `skill/slopguard/` into your `~/.claude/skills/` folder. After that, any time you ask Claude "make this sound less like AI" or "去AI化", it runs the detector to find the exact tells, rewrites the text itself, and re-checks the score so you can see it drop. The detector gives Claude precise targets; Claude does the actual rewriting.

```bash
cp -r skill/slopguard ~/.claude/skills/
```

## How it scores

The score (0–100) comes from a fixed list of AI's writing tells: stock phrases, canned sentence patterns, em-dash density, rule-of-three lists, hedging, missing contractions. Weak structural signals (like uniform sentence length) only count when real lexical tells are already present, so plain human writing won't get flagged on rhythm alone.

A few numbers from testing: pure AI-slop scores 100. Marketing copy scores 100. A Paul Graham essay scores 0, and so does a casual email.

## What it can't do

It catches AI's **default** voice — the common case, and it's accurate there. It does **not** catch an AI that's deliberately imitating one specific person's style; that's a much harder problem and this tool doesn't pretend to solve it.

The one-click "cleaner version" in the browser is a rough fix: it strips filler and swaps inflated words for plain ones. It can't rewrite sentence structure, though. For a real rewrite, copy the ready-made prompt and run it in ChatGPT or Claude — or use the Claude Code skill, which does the rewrite for you.

The score is a guide, not a verdict. One em-dash isn't slop. It's the pile-up that reads like a machine.

(One more honest note: run Slopguard on this very README and it scores moderately, not zero — because the text keeps *naming* the exact phrases it looks for, like "leverage" and "seamless". The detector flags words; it can't tell a mention from real use. Now you know one of its limits.)

## License

MIT. Use it, fork it, ship it.
