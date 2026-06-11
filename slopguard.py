#!/usr/bin/env python3
"""Slopguard — catch AI-slop before it ships.

A dependency-free linter for the *default register* of AI-generated prose: the
stock phrases ("delve", "leverage", "seamless", "I hope this finds you well"),
the "it's not just X — it's Y" escalation, em-dash drama, the rule-of-three, and
flawless parallel structure. It scores how slopped a piece of text is, names the
exact tells, and can do a rough deterministic de-slop.

Honest scope: high precision on the COMMON case (text written in AI's default
voice). It does NOT try to catch an AI deliberately imitating a specific person's
style — that's a different, much harder problem. The score is a guide, not a
verdict: one em-dash is fine; it's the pile-up that reads like a machine.

Usage:
    python slopguard.py "your text here"
    python slopguard.py --file draft.txt
    python slopguard.py --file draft.txt --fix        # also print a de-slopped draft
    echo "text" | python slopguard.py                 # read from stdin
    python slopguard.py --file draft.txt --json        # machine-readable output

No dependencies. Python 3.8+. MIT licensed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# --- the AI-tell lexicon (documented, public LLM-prose fingerprints) ---
STOCK = [
    r"i hope (this (email|message) finds you well|you('re| are) doing well)",
    r"i('d| would) be (happy|delighted|glad|more than happy) to",
    r"(please )?(feel free|don't hesitate) to (reach out|ask|contact)",
    r"in (today's|this) (fast-?paced|ever-?(changing|evolving)|digital|modern) (world|landscape|age)",
    r"at the end of the day", r"it('s| is) (worth|important) (noting|to note|mentioning)",
    r"that (being said|said,)", r"when it comes to", r"in the (realm|world) of",
    r"navigat(e|ing) the (complexit(?:y|ies)|landscape|challenges?)", r"a testament to",
    r"(rich|vibrant) tapestry", r"delv(e|ing) into", r"underscor(e|es|ing|ed)",
    r"look no further", r"rest assured", r"we('ve| have) got you covered",
    r"game-?changer", r"unlock (the |your )?(power|potential|secrets)",
    r"take (it|your \w+) to the next level", r"elevate your", r"embark on (a|your) journey",
    r"ever-?(evolving|changing|growing)", r"\bseamless(ly)?\b", r"\brobust\b",
    r"\bcutting-?edge\b", r"\bleverag(e|ing|ed)\b", r"\bsynerg(?:y|ies)\b", r"\bholistic\b",
    r"\bcurat(e|ed|ing)\b", r"\bbespoke\b", r"\bmyriad\b", r"\bplethora\b",
    r"\bstreamlin(e|ed|ing)\b", r"\bempower(s|ing|ed)?\b", r"\bfoster(s|ing|ed)?\b",
    r"\bharness(ing| the)?\b", r"\bpivotal\b", r"\bparamount\b", r"\btransformative\b",
    r"\bsupercharge\b", r"\bunparalleled\b", r"\bmeticulous(ly)?\b", r"\bcatalyst\b",
    r"the (beauty|magic|power) of", r"in conclusion", r"to sum (up|it up)",
    r"\bmoreover\b", r"\bfurthermore\b", r"\bnevertheless\b", r"\badditionally,",
    r"\bnotably,", r"\bcrucially,", r"\bimportantly,", r"\bultimately,", r"\bdive (deep|in)\b",
]
CONSTRUCTIONS = [
    (r"it'?s not (just|only|merely|about) [^.,;—]{2,40}[—,] it'?s", "‘it’s not just X — it’s Y’"),
    (r"not (just|only|merely) [^.,;—]{2,40} but (also )?", "‘not just X but Y’"),
    (r"this (isn'?t|is not) (just )?about [^.]{2,40}\. it'?s about", "‘this isn’t about X. it’s about Y’"),
    (r"here'?s the (thing|kicker|deal|catch|secret|truth)[:.]", "‘here’s the thing:’ bait"),
    (r"(but )?let'?s (break it down|dive in|unpack|explore)", "‘let’s break it down’ filler"),
    (r"the (best|wild|crazy|kicker) part\??[:.]?", "‘the best part’ bait"),
]
HEDGES = [r"\bperhaps\b", r"\barguably\b", r"\bit (seems|appears) (that|like)\b",
          r"\bone (might|could) (argue|say)\b", r"\bto some (extent|degree)\b"]


def analyze(text: str) -> dict:
    low = text.lower()
    n_words = max(1, len(re.findall(r"\w+", text)))
    tells = []  # (category, matched_text)
    stock_n = constr_n = hedge_n = 0
    for pat in STOCK:
        for m in re.finditer(pat, low):
            stock_n += 1
            tells.append(("phrase", text[m.start():m.end()]))
    for pat, label in CONSTRUCTIONS:
        if re.search(pat, low):
            constr_n += 1
            tells.append(("pattern", label))
    for pat in HEDGES:
        hedge_n += len(re.findall(pat, low))
    emdash = (text.count("—") + text.count(" - ")) / max(1, len(text) / 100)
    tric = len(re.findall(r"[\w][^,.;:]{1,30},\s[^,.;:]{1,30},\s(?:and|or)\s[^,.;:]{1,30}", low))
    sents = [s for s in re.split(r"[.!?。！？\n]+", text) if s.strip()]
    uni = 0.0
    if len(sents) >= 4:
        lens = [len(s) for s in sents]
        mean = sum(lens) / len(lens)
        sd = (sum((x - mean) ** 2 for x in lens) / len(lens)) ** 0.5
        uni = max(0.0, 1 - sd / (mean + 1e-9))
    has_contr = bool(re.search(r"\b\w+['’](s|t|re|ve|ll|d|m)\b", low))

    # PRIMARY = high-precision lexical/pattern tells. SECONDARY = weak structural
    # signals that ONLY amplify when primary tells exist — so clean human writing
    # can't be flagged on structure alone. em-dash counts only above ~1/100c.
    stock_rate = stock_n / (n_words / 60)
    heavy_em = max(0.0, emdash - 1.0)
    primary = 2.4 * stock_rate + 3.0 * constr_n + 1.4 * min(heavy_em, 3) + 1.4 * tric + 0.9 * hedge_n / (n_words / 80)
    secondary = 1.6 * uni + (1.2 if (not has_contr and n_words > 25) else 0)
    raw = primary + secondary * min(1.0, primary / 1.5)
    score = max(0, min(100, round(100 * (1 - 2 ** (-raw / 3)))))
    verdict = ("clean — reads human" if score < 20 else
               "some AI tells — tighten it" if score < 45 else
               "slopped — reads AI" if score < 70 else
               "heavy AI-slop — rewrite in your voice")

    signals = []
    if stock_n: signals.append(("AI filler words", f"{stock_n} found"))
    if constr_n: signals.append(("AI sentence patterns", f"{constr_n} found"))
    if emdash > 1.2: signals.append(("Dramatic dashes (—)", "overused"))
    if tric: signals.append(("Lists of three", str(tric)))
    if hedge_n: signals.append(("Hedge words", str(hedge_n)))
    if not has_contr and n_words > 25: signals.append(("No contractions", "stiff"))
    if uni > 0.7 and signals: signals.append(("Sentences same length", "yes"))

    # de-duplicate tells, keep order
    seen, uniq_tells = set(), []
    for cat, t in tells:
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq_tells.append((cat, t))
    return {"score": score, "verdict": verdict, "signals": signals,
            "tells": uniq_tells, "words": n_words}


def deslop(text: str) -> str:
    """Rough deterministic de-slop: a tighter starting draft, not a full rewrite.
    Strips removable filler, swaps inflated vocab (grammar-safe), restores
    contractions, calms em-dashes. Structural tells (rule-of-three, sentence
    rhythm) need a real rewrite — use an LLM for that."""
    t = text
    kill = [r"\bin today's [^,.]{0,30}?(world|landscape|age|era)[,]?\s*",
            r"\bit('s| is) (worth|important) (noting|to note|mentioning) that\s*",
            r"\bat the end of the day[,]?\s*", r"\bthat (being said|said),?\s*",
            r"\b(moreover|furthermore|additionally|notably|crucially|importantly|ultimately),\s*",
            r"\b(rest assured|look no further)[,.]?\s*", r"\b(in conclusion|to sum (up|it up))[,:]?\s*",
            r"\bneedless to say,?\s*", r"\bit goes without saying that\s*"]
    for pat in kill:
        t = re.sub(pat, "", t, flags=re.I)
    t = re.sub(r"\bi('d| would) be (happy|delighted|glad|more than happy) to\b", "I can", t, flags=re.I)
    t = re.sub(r"it'?s not (just|only|merely|about) [^.,;—]{2,60}[—,]\s*(it'?s\s*)", "it's ", t, flags=re.I)
    t = re.sub(r"\bnot (just|only|merely) [^.,;—]{2,60} but (also )?", "", t, flags=re.I)
    swap = [(r"\bleveraging\b", "using"), (r"\bleverages\b", "uses"), (r"\bleveraged\b", "used"),
            (r"\bleverage\b", "use"), (r"\butilizing\b", "using"), (r"\butilizes\b", "uses"),
            (r"\butilize\b", "use"), (r"\bseamless(ly)?\b", "smooth"), (r"\brobust\b", "solid"),
            (r"\bcutting-?edge\b", "new"), (r"\bplethora of\b", "lots of"), (r"\bmyriad of\b", "many"),
            (r"\bgame-?changer\b", "big deal"), (r"\bunparalleled\b", "unmatched"),
            (r"\bsynerg(?:y|ies)\b", "teamwork"),
            (r"\bparamount\b", "key"), (r"\bnumerous\b", "many"), (r"\bsubsequently\b", "then"),
            (r"\bin order to\b", "to"), (r"\ba testament to\b", "proof of"),
            (r"\bdelving into\b", "looking at"), (r"\bdelve into\b", "look at")]
    for pat, w in swap:
        t = re.sub(pat, w, t, flags=re.I)
    contr = [(r"\bit is\b", "it's"), (r"\bthat is\b", "that's"), (r"\byou are\b", "you're"),
             (r"\bwe are\b", "we're"), (r"\bdo not\b", "don't"), (r"\bdoes not\b", "doesn't"),
             (r"\bdid not\b", "didn't"), (r"\bcannot\b", "can't"), (r"\bwill not\b", "won't"),
             (r"\bis not\b", "isn't"), (r"\bare not\b", "aren't"), (r"\byou will\b", "you'll")]
    for pat, w in contr:
        t = re.sub(pat, lambda mm, w=w: (w[0].upper() + w[1:]) if mm.group(0)[0].isupper() else w, t, flags=re.I)
    t = re.sub(r"\s*—\s*", ", ", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r",\s*,", ",", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    t = re.sub(r"^\s*[,;]\s*", "", t)
    t = re.sub(r"(^|[.!?]\s+)([a-z])", lambda mm: mm.group(1) + mm.group(2).upper(), t)
    return t


def _bar(score: int) -> str:
    filled = score // 5
    return "█" * filled + "·" * (20 - filled)


def report(text: str, fix: bool) -> str:
    r = analyze(text)
    out = [f"\nSLOP {r['score']:>3}/100  [{_bar(r['score'])}]  {r['verdict']}"]
    if r["signals"]:
        out.append("\nWhat makes it read like AI:")
        for lbl, val in r["signals"]:
            out.append(f"  • {lbl:<26} {val}")
    if r["tells"]:
        out.append("\nThe exact giveaways:")
        for cat, t in r["tells"][:20]:
            out.append(f"  [{cat:<7}] {t}")
    if not r["signals"] and not r["tells"]:
        out.append("\n  No AI tells found — reads human.")
    if fix:
        cleaned = deslop(text)
        after = analyze(cleaned)["score"]
        out.append(f"\nDe-slopped (slop {r['score']} → {after}):\n  {cleaned}")
        if after >= 45:
            out.append("\n  (structural tells remain — for a full rewrite, ask an LLM to "
                       "\"rewrite this in a plain human voice, cut every AI tell\".)")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Catch AI-slop before it ships.")
    ap.add_argument("text", nargs="*", help="text to check (or use --file / stdin)")
    ap.add_argument("--file", help="read text from a file")
    ap.add_argument("--fix", action="store_true", help="also print a rough de-slopped draft")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            text = f.read()
    elif a.text:
        text = " ".join(a.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        ap.print_help()
        return 1
    if not text.strip():
        print("no text given")
        return 1
    if a.json:
        result = analyze(text)
        if a.fix:
            result["deslopped"] = deslop(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(report(text, a.fix))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
