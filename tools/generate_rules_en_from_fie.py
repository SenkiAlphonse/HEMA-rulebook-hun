#!/usr/bin/env python3
"""Generate English HEMA rule files by reusing exact FIE English text where applicable.

Inputs:
- English FIE extracted text with article IDs (t.N): provided by user.
- Hungarian FIE text (t.N): extracted from the HU PDF.
- Hungarian HEMA markdown rules in ./rules

Outputs:
- English rule files in ./rules_en for:
  - 01-altalanos.md
  - 02-hosszukard.md
  - 02.a-hosszukard-VOR.md
  - 03-etikett_fegyelem.md
  - 04-szervezes.md

Principles:
- Do NOT freely translate Hungarian HEMA text.
- If a HEMA rule block maps cleanly to a FIE t.N article (by explicit reference and/or similarity),
  insert the exact English FIE article text.
- If no clean mapping exists, mark the HEMA rule as unmatched and include the original Hungarian
  block as a placeholder.

This script is intentionally conservative: it only inserts FIE English when the Hungarian texts are
sufficiently similar.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


RE_HEMA_RULE_ID_LINE = re.compile(r"^\*\*([A-Z]{2,10}-[0-9]+(?:\.[0-9]+)*)\*\*\s*$")
RE_FIE_ARTICLE_LINE = re.compile(r"^t\.(\d+)\s*$")
RE_T_REF_ANYWHERE = re.compile(r"\bt\.(\d+)\b")


@dataclass(frozen=True)
class MappingDecision:
    status: str  # 'mapped' | 'no_match' | 'not_applicable'
    fie_id: int | None = None
    score: float | None = None
    reason: str | None = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_hu(text: str) -> str:
    text = text.lower()
    # remove markdown/HTML-ish clutter
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\*\*[^*]+\*\*", " ", text)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    # keep letters (including accented), split on non-letters
    text = re.sub(r"[^a-záéíóöőúüű]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def token_set(text: str) -> set[str]:
    t = normalize_hu(text)
    if not t:
        return set()
    tokens = {w for w in t.split(" ") if len(w) >= 3}
    return tokens


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def seq_ratio(a: str, b: str) -> float:
    a_n = normalize_hu(a)
    b_n = normalize_hu(b)
    if not a_n or not b_n:
        return 0.0
    return SequenceMatcher(None, a_n, b_n).ratio()


def combined_similarity(hema_hu: str, fie_hu: str) -> float:
    a = token_set(hema_hu)
    b = token_set(fie_hu)
    jac = jaccard(a, b)
    sr = seq_ratio(hema_hu, fie_hu)
    # weight jaccard more; sequence ratio helps for short defs
    return 0.65 * jac + 0.35 * sr


def parse_fie_articles(raw: str) -> dict[int, str]:
    """Parse an extracted FIE text file into t.N -> article text.

    Keeps the longest occurrence for each t.N (to ignore TOC duplicates).
    """
    articles: dict[int, str] = {}
    current: int | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal current, buf
        if current is None:
            return
        content = "\n".join(buf).strip("\n ")
        if not content:
            return
        prev = articles.get(current, "")
        if len(content) > len(prev):
            articles[current] = content

    for line in raw.splitlines():
        m = RE_FIE_ARTICLE_LINE.match(line.strip())
        if m:
            flush()
            current = int(m.group(1))
            buf = []
            continue
        if current is not None:
            buf.append(line.rstrip())

    flush()
    return articles


def iter_hema_rule_blocks(lines: list[str]) -> Iterable[tuple[int, str, list[str]]]:
    """Yield (start_index, rule_id, block_lines_after_id)"""
    i = 0
    while i < len(lines):
        m = RE_HEMA_RULE_ID_LINE.match(lines[i].rstrip("\n"))
        if not m:
            i += 1
            continue
        rule_id = m.group(1)
        start = i
        i += 1
        block: list[str] = []
        while i < len(lines):
            if RE_HEMA_RULE_ID_LINE.match(lines[i].rstrip("\n")):
                break
            block.append(lines[i])
            i += 1
        yield (start, rule_id, block)


def choose_mapping(
    hema_rule_id: str,
    hema_block_hu: str,
    fie_hu_articles: dict[int, str],
    explicit_candidates: list[int],
) -> MappingDecision:
    # Hard exclusions: if HEMA is clearly weapon-specific HEMA (longsword/HEMA org), skip mapping.
    hu_norm = normalize_hu(hema_block_hu)
    if any(w in hu_norm for w in [
        "hosszúkard", "hosszukard", "birkó", "birkózás", "mhs", "hemaratings", "bandázs", "gambeson",
    ]):
        # Still allow mapping if there is an explicit candidate and similarity is very high.
        pass

    candidates: list[tuple[int, float, str]] = []

    # 1) Evaluate explicit FIE references first.
    for fie_id in explicit_candidates:
        fie_hu = fie_hu_articles.get(fie_id)
        if not fie_hu:
            continue
        score = combined_similarity(hema_block_hu, fie_hu)
        candidates.append((fie_id, score, "explicit"))

    # 2) If no explicit, or explicit weak, also try best global match.
    if not candidates or max(s for _, s, _ in candidates) < 0.45:
        # limit search using token overlap prefilter
        hema_tokens = token_set(hema_block_hu)
        if hema_tokens:
            best: tuple[int, float] | None = None
            for fie_id, fie_hu in fie_hu_articles.items():
                fie_tokens = token_set(fie_hu)
                if not fie_tokens:
                    continue
                # quick prefilter
                if len(hema_tokens & fie_tokens) < 6:
                    continue
                score = combined_similarity(hema_block_hu, fie_hu)
                if best is None or score > best[1]:
                    best = (fie_id, score)
            if best is not None:
                candidates.append((best[0], best[1], "similarity"))

    if not candidates:
        return MappingDecision(status="no_match", reason="no candidate")

    candidates.sort(key=lambda x: x[1], reverse=True)
    best_id, best_score, best_kind = candidates[0]

    # Conservative thresholds.
    # - If explicit reference exists: accept at >= 0.50
    # - If only similarity: accept at >= 0.62
    if explicit_candidates:
        if best_score >= 0.50:
            return MappingDecision(status="mapped", fie_id=best_id, score=best_score, reason=f"{best_kind}")
        return MappingDecision(status="not_applicable", fie_id=best_id, score=best_score, reason="explicit but low similarity")

    if best_score >= 0.62:
        return MappingDecision(status="mapped", fie_id=best_id, score=best_score, reason=f"{best_kind}")

    return MappingDecision(status="no_match", fie_id=best_id, score=best_score, reason="similarity below threshold")


def format_fie_en_article(fie_id: int, fie_en_articles: dict[int, str]) -> str | None:
    content = fie_en_articles.get(fie_id)
    if not content:
        return None
    # Light cleanup: remove repeated page headers and form feeds.
    content = content.replace("\f", "\n")
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def rewrite_hema_file(
    hema_path: Path,
    out_path: Path,
    fie_en_articles: dict[int, str],
    fie_hu_articles: dict[int, str],
) -> None:
    src_lines = hema_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    # Precompute rule blocks for replacement.
    replacements: dict[int, list[str]] = {}

    for start_idx, rule_id, block_lines in iter_hema_rule_blocks(src_lines):
        block_hu = "".join(block_lines).strip()
        explicit = [int(x) for x in RE_T_REF_ANYWHERE.findall(block_hu)]
        # de-dup while preserving order
        explicit_dedup: list[int] = []
        for x in explicit:
            if x not in explicit_dedup:
                explicit_dedup.append(x)

        decision = choose_mapping(rule_id, block_hu, fie_hu_articles, explicit_dedup)

        new_block: list[str] = []
        if decision.status == "mapped" and decision.fie_id is not None:
            fie_id = decision.fie_id
            fie_en = format_fie_en_article(fie_id, fie_en_articles)
            if fie_en:
                new_block.append(f"<!-- FIE: t.{fie_id} | score={decision.score:.3f} | {decision.reason} -->\n")
                new_block.append(fie_en + "\n")
                new_block.append("\n")
            else:
                new_block.append(f"[[FIE_EN_MISSING_FOR_t.{fie_id}]]\n")
                new_block.append("\n")
                new_block.append(block_hu + "\n\n")
        elif decision.status == "not_applicable" and decision.fie_id is not None:
            new_block.append(f"[[FIE_RULE_NOT_DIRECTLY_APPLICABLE t.{decision.fie_id} | score={decision.score:.3f}]]\n")
            new_block.append("\n")
            new_block.append(block_hu + "\n\n")
        else:
            new_block.append("[[NO_MATCHING_FIE_RULE]]\n\n")
            if decision.fie_id is not None and decision.score is not None:
                new_block.append(f"<!-- best_candidate: t.{decision.fie_id} | score={decision.score:.3f} | {decision.reason} -->\n\n")
            new_block.append(block_hu + "\n\n")

        # Replace the *content after* the rule ID line.
        replacements[start_idx] = new_block

    # Build output in a single correct pass.
    out_lines: list[str] = []
    i = 0
    while i < len(src_lines):
        m = RE_HEMA_RULE_ID_LINE.match(src_lines[i].rstrip("\n"))
        if not m:
            out_lines.append(src_lines[i])
            i += 1
            continue

        # Rule block start.
        start_idx = i
        out_lines.append(src_lines[i])
        i += 1

        # Skip original block lines until next rule-id line or EOF.
        while i < len(src_lines) and not RE_HEMA_RULE_ID_LINE.match(src_lines[i].rstrip("\n")):
            i += 1

        # Insert replacement (or empty if not parsed).
        out_lines.extend(replacements.get(start_idx, ["\n"]))

    out_path.write_text("".join(out_lines), encoding="utf-8")


def _build_arg_parser(repo_root: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate English HEMA rule files by reusing exact FIE English text where applicable. "
            "This tool is conservative; it only inserts FIE English where the Hungarian texts match closely."
        )
    )
    parser.add_argument(
        "--fie-en",
        type=Path,
        default=repo_root / "data" / "fie_extracted" / "FIE_ENG.txt",
        help=(
            "Path to extracted English FIE technical rules with 't.N' article IDs. "
            "Default: data/fie_extracted/FIE_ENG.txt (not committed by default)."
        ),
    )
    parser.add_argument(
        "--fie-hu",
        type=Path,
        default=repo_root / "data" / "fie_extracted" / "FIE_HUN.txt",
        help="Path to extracted Hungarian FIE technical rules with 't.N' article IDs.",
    )
    parser.add_argument(
        "--hema-dir",
        type=Path,
        default=repo_root / "rules",
        help="Directory containing Hungarian HEMA rules markdown.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=repo_root / "rules_en",
        help="Output directory for generated English markdown files.",
    )
    return parser


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    parser = _build_arg_parser(repo_root)
    args = parser.parse_args()

    fie_en_path: Path = args.fie_en
    fie_hu_path: Path = args.fie_hu
    hema_dir: Path = args.hema_dir
    out_dir: Path = args.out_dir

    if not fie_en_path.exists():
        raise SystemExit(
            "Missing FIE EN extracted file: "
            f"{fie_en_path}. Provide it via --fie-en (must contain 't.N' headings)."
        )
    if not fie_hu_path.exists():
        raise SystemExit(f"Missing FIE HU extracted file: {fie_hu_path}")

    fie_en_articles = parse_fie_articles(read_text(fie_en_path))
    fie_hu_articles = parse_fie_articles(read_text(fie_hu_path))

    out_dir.mkdir(exist_ok=True)

    hema_files = [
        hema_dir / "01-altalanos.md",
        hema_dir / "02-hosszukard.md",
        hema_dir / "02.a-hosszukard-VOR.md",
        hema_dir / "03-etikett_fegyelem.md",
        hema_dir / "04-szervezes.md",
    ]

    missing_hema = [p for p in hema_files if not p.exists()]
    if missing_hema:
        raise SystemExit("Missing HEMA source file(s):\n" + "\n".join(str(p) for p in missing_hema))

    for hema_path in hema_files:
        out_path = out_dir / (hema_path.stem + ".en.md")
        rewrite_hema_file(hema_path, out_path, fie_en_articles, fie_hu_articles)
        print(f"WROTE {out_path}")


if __name__ == "__main__":
    main()
