"""
app/utils/text_utils.py
────────────────────────
Shared text processing helpers used across the pipeline.
"""

from __future__ import annotations

import re
import unicodedata


# ── Whitespace normalisation ──────────────────────────────────────────────────

def normalise_whitespace(text: str) -> str:
    """Collapse multiple spaces / tabs into one; strip leading/trailing."""
    text = unicodedata.normalize("NFKC", text)   # normalise unicode
    text = re.sub(r"[ \t]+", " ", text)           # collapse horizontal space
    text = re.sub(r"\n{3,}", "\n\n", text)        # max two consecutive newlines
    return text.strip()


# ── Sentence splitting ────────────────────────────────────────────────────────

_SENT_BOUNDARY = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z])"      # punctuation followed by capital
    r"|(?<=[.!?])\s*$"             # punctuation at end of string
)


def split_into_sentences(text: str) -> list[str]:
    """
    Naive but fast sentence splitter.
    Falls back gracefully for texts without clear boundaries.
    """
    # Split on sentence-ending punctuation followed by a space and capital
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"\'])", text)
    # Filter empty strings
    return [p.strip() for p in parts if p.strip()]


# ── Word-level diff ───────────────────────────────────────────────────────────

def build_word_diffs(
    original: str,
    corrected: str,
    diff_type: str,
) -> list[dict]:
    """
    Simple LCS-based word-level diff.
    Returns a list of {original, corrected, type, position} dicts.
    """
    ow = original.split()
    cw = corrected.split()

    # LCS DP table
    m, n = len(ow), len(cw)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            if ow[i].lower() == cw[j].lower():
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])

    diffs: list[dict] = []
    i, j, pos = 0, 0, 0

    while i < m or j < n:
        if i < m and j < n and ow[i].lower() == cw[j].lower():
            i += 1; j += 1; pos += 1
        elif j < n and (i >= m or dp[i + 1][j] <= dp[i][j + 1]):
            # Insertion in corrected
            # Pair with previous deletion if it exists and merge into a substitution
            if diffs and diffs[-1]["position"] == pos - 1 and diffs[-1]["corrected"] == "":
                diffs[-1]["corrected"] = cw[j]
            else:
                diffs.append({
                    "original": "",
                    "corrected": cw[j],
                    "type": diff_type,
                    "position": pos,
                })
            j += 1
        else:
            diffs.append({
                "original": ow[i],
                "corrected": "",
                "type": diff_type,
                "position": pos,
            })
            i += 1; pos += 1

    return diffs


def count_word_diffs(a: str, b: str) -> int:
    """Count the number of differing word positions between two strings."""
    wa, wb = a.split(), b.split()
    count = abs(len(wa) - len(wb))
    for x, y in zip(wa, wb):
        if x.lower() != y.lower():
            count += 1
    return count
