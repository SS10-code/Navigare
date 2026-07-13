"""
seo_engine.py
────────────────────────────────────────────────────────────────
Week 7 — SEO Foundations, Text Normalization & Sliding-Window N-Grams

This module is purely rule-based (no ML, no live Google scraping).
It operates on text the store owner pastes in directly.

Pipeline:
  Step 1  →  Text Normalization     (lowercase, strip punctuation, tokenize, purge stop-words)
  Step 2  →  Sliding-Window N-Gram  (find multi-word phrases with O(n) window scan)
  Step 3  →  Density Scoring        (piecewise function: floor / sweet-spot / penalty cliff)
  Step 4  →  Keyword Report         (per-keyword result + severity flag)

Scoring Zones (from session notes):
  Under-Optimized  density < 1.0%     → score = 50       (crawler can't associate page with keyword)
  Sweet Spot       1.0% ≤ d ≤ 3.5%   → score = 100      (human-authored, trusted)
  Over-Stuffed     density > 3.5%     → score = max(0, int(100 − (excess × 15)))

7.5% stress test:
  excess = 7.5 − 3.5 = 4.0
  penalty = 4.0 × 15 = 60
  score = 100 − 60 = 40  ← triggers high-severity warning

Hard floor: max(0, ...) prevents negative scores at extreme stuffing.
"""

import re
import os
import json
from typing import Union

# ─────────────────────────────────────────────────────────────
# STOP WORDS  (O(1) lookup via set — not a list)
# ─────────────────────────────────────────────────────────────
# Stop words are words so common they carry no SEO signal.
# Storing as a set means membership check is O(1) hash lookup
# instead of O(n) scan through a list.

STOP_WORDS: set = {
    "a","an","the","and","or","but","in","on","at","to","for",
    "of","with","by","from","up","about","into","through","during",
    "is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might",
    "shall","can","need","dare","ought","used","this","that","these",
    "those","i","you","he","she","it","we","they","what","which",
    "who","when","where","why","how","all","each","every","both",
    "few","more","most","other","some","such","no","not","only",
    "own","same","so","than","too","very","just","because","as",
    "until","while","although","though","if","then","else","our",
    "your","their","my","his","her","its","we","us","me","him",
}

# ─────────────────────────────────────────────────────────────
# STEP 1 — TEXT NORMALIZATION PIPELINE
# ─────────────────────────────────────────────────────────────

def normalize(raw_text: str, remove_stopwords: bool = False) -> list[str]:
    """
    Converts raw human-formatted text into a clean token list.

    Pipeline:
      1. Lowercase             — 'Bakery' and 'bakery' must match
      2. Strip punctuation     — regex removes everything except letters/digits/spaces
      3. Tokenize on whitespace — split into individual words
      4. Purge stop-words      — optional, O(1) per word via set membership

    Args:
        raw_text:          The string the store owner pasted in
        remove_stopwords:  If True, removes common English stop-words before
                           density calculation. Recommended for keyword matching.

    Returns:
        List of clean token strings.
    """
    if not raw_text or not raw_text.strip():
        return []

    # Step 1: lowercase
    lowered = raw_text.lower()

    # Step 2: strip punctuation & special characters
    # Regex: keep only [a-z 0-9] — removes commas, periods, apostrophes, etc.
    stripped = re.sub(r"[^a-z0-9\s]", " ", lowered)

    # Step 3: tokenize on whitespace (handles multiple spaces, tabs, newlines)
    tokens = stripped.split()

    # Step 4: purge stop-words (O(1) per token — set lookup, not list scan)
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOP_WORDS]

    return tokens


def normalize_phrase(phrase: str) -> list[str]:
    """Normalize a keyword phrase the same way we normalize the body text."""
    return normalize(phrase, remove_stopwords=False)


# ─────────────────────────────────────────────────────────────
# STEP 2 — SLIDING WINDOW N-GRAM MATCHER
# ─────────────────────────────────────────────────────────────

def sliding_window_match(tokens: list[str], keyword_phrase: str) -> dict:
    """
    Finds all occurrences of a keyword phrase in a token list using
    a sliding window of size = number of words in the phrase (N-gram).

    Visual metaphor (from session notes):
      Imagine words printed on a strip of paper.
      A cardboard cutout with a window of width N slides across.
      At each position, check if the words in the window match the phrase.

    For 1-gram  (single word):   window = 1, simple membership check
    For 2-gram  ("san jose"):    window = 2, check pairs
    For 3-gram  ("best sourdough bread"): window = 3, check triples

    Falling-cliff guard:
      Loop runs range(len(tokens) - window_size + 1)
      Without the "+1" we'd miss the last valid position.
      Without the "- window_size" we'd try to read past the end of the list.

    Time complexity: O(n × w) where n=token count, w=phrase word count.
    For typical web copy (500 words) and short phrases (≤4 words), this is fast.

    Returns:
        dict with keys: phrase, window_size, match_count, match_positions,
                        tokens_searched, density_pct
    """
    phrase_tokens = normalize_phrase(keyword_phrase)
    window_size   = len(phrase_tokens)

    if window_size == 0:
        return {"error": "Empty keyword phrase"}
    if len(tokens) == 0:
        return {"error": "Empty text body"}
    if window_size > len(tokens):
        return {
            "phrase":         keyword_phrase,
            "window_size":    window_size,
            "match_count":    0,
            "match_positions":[],
            "tokens_searched":len(tokens),
            "density_pct":    0.0,
        }

    match_positions = []

    # THE SLIDING WINDOW LOOP
    # i moves from 0 to (total_tokens - window_size) inclusive
    # At each position, compare the slice tokens[i : i+window_size] to phrase_tokens
    for i in range(len(tokens) - window_size + 1):
        window = tokens[i : i + window_size]
        if window == phrase_tokens:
            match_positions.append(i)

    match_count  = len(match_positions)
    # Density anchored to ORIGINAL token count (not stop-word-filtered count)
    # This matches the session note: "8 words → San Jose appeared 1 → 1/8 × 100 = 12.5%"
    density_pct  = (match_count / len(tokens)) * 100 if len(tokens) > 0 else 0.0

    return {
        "phrase":          keyword_phrase,
        "normalized_phrase": " ".join(phrase_tokens),
        "window_size":     window_size,
        "match_count":     match_count,
        "match_positions": match_positions,
        "tokens_searched": len(tokens),
        "density_pct":     round(density_pct, 4),
    }


# ─────────────────────────────────────────────────────────────
# STEP 3 — PIECEWISE DENSITY SCORING FUNCTION
# ─────────────────────────────────────────────────────────────

# Scoring zones (non-linear — inverted-U curve):
#
#  density < 1.0%          → score = 50   (under-optimized / ghosting)
#  1.0% ≤ density ≤ 3.5%  → score = 100  (sweet spot)
#  density > 3.5%          → score = max(0, int(100 − (excess × 15)))
#
# Why non-linear?
#   Linear logic would reward copy-pasting keywords indefinitely.
#   The inverted-U penalises over-stuffing, matching how real search
#   crawler algorithms flag keyword manipulation.
#
# Penalty factor = 15:
#   Chosen so the score tanks meaningfully before text becomes unreadable.
#   At density = 3.5 + (100/15) ≈ 10.2%, score hits the hard floor of 0.

UNDER_OPTIMIZED_THRESHOLD = 1.0    # % — below this = ghosting
SWEET_SPOT_UPPER          = 3.5    # % — above this = stuffing penalty
FLOOR_SCORE               = 50     # score for under-optimized
CEILING_SCORE             = 100    # score for sweet spot
PENALTY_MULTIPLIER        = 15     # excess density × this = points deducted


def score_density(density_pct: float) -> dict:
    """
    Piecewise scoring function. Maps keyword density % → SEO score 0–100.

    Zone logic matches session spec exactly:
      < 1.0%          → 50
      1.0% to 3.5%    → 100
      > 3.5%          → max(0, int(100 − (excess × 15)))

    Returns a dict including score, zone name, severity flag, and explanation.
    """
    d = density_pct

    if d < UNDER_OPTIMIZED_THRESHOLD:
        score    = FLOOR_SCORE
        zone     = "Under-Optimized"
        severity = "low"
        explain  = (
            f"Density {d:.2f}% is below the 1% threshold. "
            "The page is being indexed but the crawler can't strongly associate "
            "it with this keyword (weak relevance signal). "
            "Add more natural mentions."
        )

    elif d <= SWEET_SPOT_UPPER:
        score    = CEILING_SCORE
        zone     = "Sweet Spot"
        severity = "none"
        explain  = (
            f"Density {d:.2f}% is in the optimal 1–3.5% range. "
            "Content appears human-authored. Crawler maps page to keyword intent. "
            "No changes needed."
        )

    else:
        # Over-stuffing penalty: max(0, int(100 − (excess × 15)))
        excess_density  = d - SWEET_SPOT_UPPER
        penalty         = excess_density * PENALTY_MULTIPLIER
        score           = max(0, int(CEILING_SCORE - penalty))

        if score >= 70:
            zone     = "Mildly Over-Stuffed"
            severity = "medium"
        elif score >= 40:
            zone     = "Over-Stuffed"
            severity = "high"
        else:
            zone     = "Keyword Spam"
            severity = "critical"

        explain = (
            f"Density {d:.2f}% exceeds the 3.5% ceiling. "
            f"Excess: {excess_density:.2f}% × 15 = {penalty:.1f} points deducted. "
            f"Score: 100 − {penalty:.1f} = {score}. "
            "Reduce keyword repetition to avoid crawler down-ranking."
        )

    return {
        "density_pct":   round(d, 4),
        "score":         score,
        "zone":          zone,
        "severity":      severity,   # none / low / medium / high / critical
        "explanation":   explain,
    }


# ─────────────────────────────────────────────────────────────
# STEP 4 — FULL KEYWORD REPORT
# ─────────────────────────────────────────────────────────────

def analyse_text(body_text: str, keywords: list[str],
                 remove_stopwords: bool = False) -> dict:
    """
    Full pipeline: normalize → match all keywords → score each one.

    Args:
        body_text:        Raw text the store owner pasted (web copy, review, etc.)
        keywords:         List of keyword phrases to check (1-gram or multi-word)
        remove_stopwords: Whether to remove stop-words before token count

    Returns:
        dict with overall stats and per-keyword results
    """
    if not body_text or not body_text.strip():
        return {"error": "No text provided"}
    if not keywords:
        return {"error": "No keywords provided"}

    # Normalize the body text once
    tokens = normalize(body_text, remove_stopwords=remove_stopwords)

    if len(tokens) == 0:
        return {"error": "Text contains no meaningful words after normalization"}

    results = []
    for kw in keywords:
        if not kw or not kw.strip():
            continue

        match_data  = sliding_window_match(tokens, kw)
        if "error" in match_data:
            results.append({"keyword": kw, "error": match_data["error"]})
            continue

        score_data  = score_density(match_data["density_pct"])

        results.append({
            "keyword":           kw,
            "normalized_phrase": match_data["normalized_phrase"],
            "n_gram_size":       match_data["window_size"],
            "match_count":       match_data["match_count"],
            "density_pct":       match_data["density_pct"],
            "score":             score_data["score"],
            "zone":              score_data["zone"],
            "severity":          score_data["severity"],
            "explanation":       score_data["explanation"],
        })

    # Overall page health = average score (weighted equally)
    scores    = [r["score"] for r in results if "score" in r]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "original_length_chars": len(body_text),
        "token_count":           len(tokens),
        "keyword_count":         len(results),
        "page_health_score":     avg_score,
        "results":               results,
    }


# ─────────────────────────────────────────────────────────────
# DEMO / UNIT TEST
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍  SEO Engine — Week 7 Demo")
    print("=" * 55)

    # ── Test 1: Text normalization pipeline ───────────────────
    print("\n── Step 1: Text Normalization ──")
    sample = "Welcome to our Artisan Bakery! Fresh sourdough bread, the BEST croissants in San Jose."
    tokens = normalize(sample, remove_stopwords=False)
    tokens_clean = normalize(sample, remove_stopwords=True)
    print(f"  Input  : {sample}")
    print(f"  Tokens : {tokens}")
    print(f"  No stop: {tokens_clean}")
    print(f"  Length : {len(tokens)} → {len(tokens_clean)} after stop-word removal")

    # ── Test 2: Sliding window N-gram matching ─────────────────
    print("\n── Step 2: Sliding Window N-Gram ──")
    body = """
    Welcome to Sunrise Bakery, the best bakery in San Jose. 
    Our San Jose bakery offers fresh bread, pastries, and custom cakes.
    Visit our San Jose location today. Best bakery near me in San Jose.
    We are proud to be San Jose's favorite artisan bakery.
    """
    test_phrases = ["san jose", "bakery", "best bakery", "sourdough"]
    for phrase in test_phrases:
        result = sliding_window_match(normalize(body), phrase)
        print(f"  '{phrase}' → count={result['match_count']}  density={result['density_pct']:.2f}%")

    # ── Test 3: Density scoring — all three zones ──────────────
    print("\n── Step 3: Piecewise Scoring ──")
    test_densities = [
        (0.3,  "Under-optimized"),
        (1.5,  "Sweet spot"),
        (3.5,  "Upper boundary"),
        (7.5,  "Session stress test"),
        (10.2, "Extreme stuffing"),
    ]
    for density, label in test_densities:
        s = score_density(density)
        print(f"  {label:22s}  density={density:5.1f}%  score={s['score']:3d}  "
              f"zone='{s['zone']}'  severity={s['severity']}")

    # ── Test 4: Full pipeline on realistic bakery copy ─────────
    print("\n── Step 4: Full Keyword Report ──")
    bakery_copy = """
    Sunrise Bakery is the best bakery in San Jose. We bake fresh sourdough bread 
    every morning. Our San Jose bakery has served the community for over 10 years.
    Come visit the best bakery near you. Custom birthday cakes, fresh pastries, 
    and artisan bread available daily. San Jose bakery open 7 days a week.
    Order your custom cake online. Fresh bread baked daily. San Jose bakery.
    """
    keywords = [
        "san jose bakery",
        "fresh bread",
        "custom cake",
        "sourdough",
        "best bakery",
    ]
    report = analyse_text(bakery_copy, keywords)
    print(f"\n  Token count        : {report['token_count']}")
    print(f"  Page health score  : {report['page_health_score']}/100")
    print()
    for r in report["results"]:
        if "error" in r: continue
        bar = "█" * (r["score"] // 10)
        print(f"  [{r['score']:3d}/100] {bar:<10}  '{r['keyword']}'")
        print(f"          count={r['match_count']}  density={r['density_pct']:.2f}%  "
              f"zone={r['zone']}  severity={r['severity']}")

    # ── Session stress test (7.5%) ─────────────────────────────
    print("\n── Session Stress Test: 7.5% density ──")
    s75 = score_density(7.5)
    print(f"  Density  : 7.5%")
    print(f"  Excess   : 7.5 - 3.5 = 4.0%")
    print(f"  Penalty  : 4.0 × 15 = 60 points")
    print(f"  Score    : 100 - 60 = {s75['score']}")
    print(f"  Severity : {s75['severity'].upper()}")
    print(f"  Zone     : {s75['zone']}")

    print("\n  Hard floor test (10.2%): ", end="")
    s102 = score_density(10.2)
    print(f"score={s102['score']}  (max(0, ...) prevents negatives)")
    print("\n✅  SEO Engine ready.\n")
