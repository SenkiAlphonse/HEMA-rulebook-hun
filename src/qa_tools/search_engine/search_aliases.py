"""
Enhanced HEMA Rulebook Search Engine with Alias Support
"""

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qa_tools.search_engine import search_config
from qa_tools.search_engine.search_utils import get_children_rules, get_rule_depth, get_rule_lineage

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result"""

    rule_id: str
    text: str
    section: str
    subsection: str
    document: str
    weapon_type: str
    variant: str
    score: float


class AliasAwareSearch:
    """Search engine with alias support for HEMA rulebook"""

    def __init__(self, index_path: str, aliases_path: str | None = None):
        self.index_path = Path(index_path)
        self.rules = []
        self.aliases = {}
        self.alias_to_key = {}  # Reverse lookup: alias -> (category, key)

        if aliases_path is None:
            aliases_path = self.index_path.parent / "aliases.json"

        self.load_aliases(aliases_path)
        self.load_index()
        self._build_alias_lookup()

    def load_aliases(self, aliases_path: str) -> None:
        """Load aliases from JSON file.

        Args:
            aliases_path: Path to the aliases JSON file

        Raises:
            Logs warning if file not found, logs error if JSON is invalid
        """
        try:
            with open(aliases_path, encoding="utf-8") as f:
                self.aliases = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Aliases file not found at {aliases_path}, using empty aliases")
            self.aliases = {"variants": {}, "weapons": {}, "concepts": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse aliases JSON: {e}")
            self.aliases = {"variants": {}, "weapons": {}, "concepts": {}}

    def _build_alias_lookup(self):
        """Build reverse lookup from alias to its category and key"""
        # Map variant aliases
        for key, aliases in self.aliases.get("variants", {}).items():
            for alias in aliases:
                self.alias_to_key[alias.lower()] = ("variant", key)

        # Map weapon aliases
        for key, aliases in self.aliases.get("weapons", {}).items():
            for alias in aliases:
                self.alias_to_key[alias.lower()] = ("weapon", key)

        # Map concept aliases - store all aliases in concept group
        for concept_key, aliases in self.aliases.get("concepts", {}).items():
            for alias in aliases:
                self.alias_to_key[alias.lower()] = ("concept", concept_key)

    def load_index(self) -> None:
        """Load the rules index"""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index not found: {self.index_path}")

        try:
            with open(self.index_path, encoding="utf-8") as f:
                data = json.load(f)
                loaded_rules = data["rules"]
                self.rules = self._deduplicate_rules_by_id(loaded_rules)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse index JSON: {e}")
            raise RuntimeError(f"Index file corrupted: {e}") from e

        logger.info(f"Loaded {len(self.rules)} rules with alias support")

    def _deduplicate_rules_by_id(self, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return rules with unique rule IDs, preserving first occurrence order."""
        deduplicated = []
        seen_rule_ids = set()

        for rule in rules:
            rule_id = rule.get("rule_id")
            if not rule_id or rule_id in seen_rule_ids:
                continue
            seen_rule_ids.add(rule_id)
            deduplicated.append(rule)

        duplicate_count = len(rules) - len(deduplicated)
        if duplicate_count > 0:
            logger.warning(
                "Removed %d duplicate rules by rule_id while loading %s",
                duplicate_count,
                self.index_path,
            )

        return deduplicated

    def _deduplicate_results_by_rule_id(self, results: list[SearchResult]) -> list[SearchResult]:
        """Return results with unique rule IDs, preserving ranking order."""
        deduplicated = []
        seen_rule_ids = set()

        for result in results:
            if result.rule_id in seen_rule_ids:
                continue
            seen_rule_ids.add(result.rule_id)
            deduplicated.append(result)

        return deduplicated

    def _expand_query(self, query: str) -> tuple[str, str | None, str | None, list[str], str]:
        """Expand query based on aliases, extracting filters and concept terms.

        Analyzes query words to detect variant/weapon filters and concept expansions.

        Args:
            query: Original search query

        Returns:
            Tuple of (expanded_query, variant_filter, weapon_filter, concept_terms, base_query)
            - expanded_query: Query with concept terms added
            - variant_filter: Detected variant (VOR/COMBAT/AFTERBLOW) or None
            - weapon_filter: Detected weapon type or None
            - concept_terms: List of concept alias terms
            - base_query: Original query without aliases
        """
        query_lower = query.lower()
        variant_filter = None
        weapon_filter = None
        concept_terms = []
        remaining_terms = []

        # Split query into words
        words = re.findall(r"\w+", query_lower)

        for word in words:
            if word in self.alias_to_key:
                category, key = self.alias_to_key[word]

                if category == "variant":
                    variant_filter = key
                elif category == "weapon":
                    weapon_filter = key
                elif category == "concept":
                    # Add all aliases from this concept to search terms
                    concept_terms.extend(self.aliases["concepts"][key])
            else:
                remaining_terms.append(word)

        # Build expanded query
        base_query = " ".join(remaining_terms)
        expanded_query = base_query
        if concept_terms:
            # Add concept terms to search
            expanded_query = expanded_query + " " + " ".join(concept_terms)

        return (
            expanded_query.strip(),
            variant_filter,
            weapon_filter,
            concept_terms,
            base_query.strip(),
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching by removing accents and converting to lowercase.

        Args:
            text: Text to normalize

        Returns:
            Normalized text without diacritics, in lowercase
        """
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()

    def search(
        self,
        query: str,
        max_results: int | None = None,
        variant_filter: str | None = None,
        weapon_filter: str | None = None,
    ) -> list[SearchResult]:
        """
        Search with alias awareness and query expansion

        Args:
            query: Search query
            max_results: Max results to return (defaults to config)
            variant_filter: Filter by variant (VOR, COMBAT, AFTERBLOW) - can be overridden by query
            weapon_filter: Filter by weapon (longsword, rapier, etc.) - can be overridden by query
        """
        # Expand query based on aliases
        expanded_query, detected_variant, detected_weapon, concept_terms, base_query = (
            self._expand_query(query)
        )

        # Use detected filters if not explicitly provided
        if not variant_filter and detected_variant:
            variant_filter = detected_variant
        if not weapon_filter and detected_weapon:
            weapon_filter = detected_weapon

        query_lower = expanded_query.lower() if expanded_query else query.lower()
        query_norm = self._normalize_text(query_lower)
        query_terms = self._extract_terms(query_norm)
        required_terms = self._extract_terms(self._normalize_text(base_query)) if base_query else []

        results = []

        for rule in self.rules:
            # Apply filters with hierarchy:
            # - General rules (weapon_type='general') apply to everything
            # - Weapon-general rules (no variant) apply to all variants of that weapon
            # - Format-specific rules apply only to that variant

            rule_weapon = rule.get("weapon_type", "general")
            rule_variant = rule.get("variant", "")

            # If weapon filter is specified
            if weapon_filter and rule_weapon != "general" and rule_weapon != weapon_filter:
                continue

            # If variant filter is specified
            if variant_filter and rule_weapon != "general" and rule_variant and rule_variant != variant_filter:
                continue

            # Require all base query terms to appear somewhere
            if required_terms:
                combined_text = " ".join(
                    [
                        rule.get("text_plain", rule.get("text", "")),
                        rule.get("section", ""),
                        rule.get("subsection", ""),
                    ]
                )
                combined_norm = self._normalize_text(combined_text)
                if any(term not in combined_norm for term in required_terms):
                    continue

            # Calculate score including aliases
            score = self._calculate_score_with_aliases(
                rule, query_lower, query_norm, query_terms, concept_terms
            )

            if score > 0:
                results.append(
                    SearchResult(
                        rule_id=rule["rule_id"],
                        text=rule["text"],
                        section=rule.get("section", ""),
                        subsection=rule.get("subsection", ""),
                        document=rule.get("document", ""),
                        weapon_type=rule.get("weapon_type", ""),
                        variant=rule.get("variant", ""),
                        score=score,
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)
        results = self._deduplicate_results_by_rule_id(results)

        # Use default max results if not provided
        if max_results is None:
            max_results = search_config.DEFAULT_MAX_RESULTS
        # Group results and return
        return self._group_and_return_results(results, max_results)

    def _group_and_return_results(
        self, results: list[SearchResult], max_results: int
    ) -> list[SearchResult]:
        """Group level 4-5 results with their parents and children"""
        grouped_results = []
        seen_root_ids = set()
        grouping_multiplier = getattr(search_config, "GROUPING_MULTIPLIER", 3)

        for result in results[:max_results]:
            depth = self.get_rule_depth(result.rule_id)
            # For level 4-5 rules, include parents (up to level 3) and children
            if depth >= 4:
                lineage = self.get_rule_lineage(result.rule_id)
                # Determine the root of this group (the level 2 parent if it exists)
                root_id = (
                    lineage[1] if len(lineage) > 1 else lineage[0] if lineage else result.rule_id
                )
                # Skip if we've already processed this family
                if root_id in seen_root_ids:
                    continue
                seen_root_ids.add(root_id)

                # Collect ALL matched results with the same root (all siblings that matched)
                siblings = [
                    r
                    for r in results
                    if self.get_rule_lineage(r.rule_id)[1] == root_id
                    if len(self.get_rule_lineage(r.rule_id)) > 1
                ]

                # Collect the family: parents + all matched siblings + children
                family = []

                # Add parents (up to level 3)
                for parent_id in lineage:
                    parent_depth = self.get_rule_depth(parent_id)
                    if parent_depth <= 3:
                        parent_rule = self.get_rule_by_id(parent_id)
                        if parent_rule:
                            family.append(
                                SearchResult(
                                    rule_id=parent_rule["rule_id"],
                                    text=parent_rule["text"],
                                    section=parent_rule.get("section", ""),
                                    subsection=parent_rule.get("subsection", ""),
                                    document=parent_rule.get("document", ""),
                                    weapon_type=parent_rule.get("weapon_type", ""),
                                    variant=parent_rule.get("variant", ""),
                                    score=result.score,  # Inherit score from matched rule
                                )
                            )

                # Add all matched siblings (up to 5 deep)
                for sibling in siblings:
                    if sibling not in family:
                        family.append(sibling)

                # Sort family by depth and add to results
                family.sort(key=lambda x: self.get_rule_depth(x.rule_id))
                grouped_results.extend(family)
            else:
                # Level 1-3 rules: just add them directly
                grouped_results.append(result)
        grouped_results = self._deduplicate_results_by_rule_id(grouped_results)
        return grouped_results[: max_results * grouping_multiplier]

    def _build_rule_family(self, result: SearchResult, lineage: list[str]) -> list[SearchResult]:
        """Build a family of rules: parents + matched rule + children.

        For hierarchical display, gathers parent rules (up to level 3),
        the matched rule itself, and child rules (if at level 4).

        Args:
            result: The matched SearchResult
            lineage: List of parent rule IDs from get_rule_lineage

        Returns:
            List of SearchResult objects forming the rule family
        """
        family = []

        # Add parents (up to level 3)
        for parent_id in lineage:
            parent_depth = self.get_rule_depth(parent_id)
            if parent_depth <= 3:
                parent_rule = self.get_rule_by_id(parent_id)
                if parent_rule:
                    family.append(
                        SearchResult(
                            rule_id=parent_rule["rule_id"],
                            text=parent_rule["text"],
                            section=parent_rule.get("section", ""),
                            subsection=parent_rule.get("subsection", ""),
                            document=parent_rule.get("document", ""),
                            weapon_type=parent_rule.get("weapon_type", ""),
                            variant=parent_rule.get("variant", ""),
                            score=result.score,  # Inherit score from matched rule
                        )
                    )

        # Add the matched rule itself
        family.append(result)

        # Add children (level 5 if we're at level 4, nothing if we're at level 5)
        if self.get_rule_depth(result.rule_id) == 4:
            children = self.get_children_rules(result.rule_id)
            for child_id in children:
                child_rule = self.get_rule_by_id(child_id)
                if child_rule:
                    family.append(
                        SearchResult(
                            rule_id=child_rule["rule_id"],
                            text=child_rule["text"],
                            section=child_rule.get("section", ""),
                            subsection=child_rule.get("subsection", ""),
                            document=child_rule.get("document", ""),
                            weapon_type=child_rule.get("weapon_type", ""),
                            variant=child_rule.get("variant", ""),
                            score=result.score,  # Inherit score
                        )
                    )

        return family

    def _extract_terms(self, query: str) -> list[str]:
        """Extract meaningful search terms from query.

        Filters out Hungarian and English stop words and short terms.

        Args:
            query: Search query string

        Returns:
            List of extracted terms (> 2 chars, excluding stop words)
        """
        stop_words = {
            "a",
            "az",
            "és",
            "vagy",
            "de",
            "ha",
            "hogy",
            "mi",
            "van",
            "volt",
            "the",
            "an",
            "and",
            "or",
            "but",
            "if",
            "is",
        }
        terms = re.findall(r"\w+", query)
        return [t for t in terms if t not in stop_words and len(t) > 2]

    def _calculate_score_with_aliases(
        self,
        rule: dict[str, Any],
        query: str,
        query_norm: str,
        terms: list[str],
        concept_terms: list[str] | None = None,
    ) -> float:
        """Calculate score including alias matches"""
        score = 0.0

        # Use text_plain for scoring (markdown-stripped version) to enable substring matches
        # but keep original text for display
        text_plain = rule.get("text_plain", rule.get("text", ""))
        text_lower = text_plain.lower()
        section_lower = rule.get("section", "").lower()
        subsection_lower = rule.get("subsection", "").lower()
        rule_id_lower = rule["rule_id"].lower()

        text_norm = self._normalize_text(text_lower)
        section_norm = self._normalize_text(section_lower)
        subsection_norm = self._normalize_text(subsection_lower)

        # Direct rule ID match (highest priority)
        if rule_id_lower in query:
            score += search_config.SCORE_RULE_ID_MATCH

        # Exact phrase in text
        if query_norm and query_norm in text_norm:
            score += search_config.SCORE_EXACT_PHRASE_TEXT

        # Exact phrase in section
        if query_norm and (query_norm in section_norm or query_norm in subsection_norm):
            score += search_config.SCORE_EXACT_PHRASE_SECTION

        # Term frequency in text
        for term in terms:
            count_in_text = text_norm.count(term)
            score += count_in_text * search_config.SCORE_TERM_FREQUENCY

            if term in section_norm or term in subsection_norm:
                score += search_config.SCORE_TERM_SECTION

        # Check concept terms (from alias expansion)
        if concept_terms:
            for concept_term in concept_terms:
                if self._normalize_text(concept_term) in text_norm:
                    score += search_config.SCORE_CONCEPT_TERM

        # Check variant aliases (legacy scoring for non-expanded queries)
        if rule.get("variant"):
            for alias in rule.get("variant_aliases", []):
                if alias in query:
                    score += search_config.SCORE_VARIANT_ALIAS

        # Check weapon aliases (legacy scoring for non-expanded queries)
        for alias in rule.get("weapon_aliases", []):
            if alias in query:
                score += search_config.SCORE_WEAPON_ALIAS

        # Apply length penalty for very long rules (e.g., large tables)
        # Rules > threshold chars get progressively lower scores to push them down rankings
        text_length = len(rule["text"])
        if text_length > search_config.LENGTH_PENALTY_THRESHOLD:
            # Exponential penalty: threshold chars = 1.5x, etc.
            length_penalty = (
                text_length / float(search_config.LENGTH_PENALTY_THRESHOLD)
            ) ** search_config.LENGTH_PENALTY_EXP
            score = score / length_penalty

        return score

    def get_rule_depth(self, rule_id: str) -> int:
        """Get depth of rule from its ID.

        Examples:
            GEN-6.7.4.2 -> depth 4
            LS-AB-1.2.10.2 -> depth 4
        """
        return get_rule_depth(rule_id)

    def get_rule_lineage(self, rule_id: str) -> list[str]:
        """Get list of parent rule IDs for a given rule.

        Examples:
            GEN-6.7.4.2 -> ["GEN", "GEN-6", "GEN-6.7", "GEN-6.7.4"]
        """
        return get_rule_lineage(rule_id)

    def get_children_rules(self, rule_id: str) -> list[str]:
        """Get direct child rule IDs for a given rule."""
        return get_children_rules(rule_id, self.rules)

    def get_rule_by_id(self, rule_id: str) -> dict[str, Any] | None:
        """Get a rule by its ID (case-insensitive)."""
        for rule in self.rules:
            if rule.get("rule_id") == rule_id:
                return rule
        # Case-insensitive fallback
        rule_id_lower = rule_id.lower()
        for rule in self.rules:
            if rule.get("rule_id", "").lower() == rule_id_lower:
                return rule
        return None


def format_result(result: SearchResult) -> str:
    """Format a result for display"""
    output = []
    output.append(f"\n{'=' * 70}")
    output.append(f"Rule ID: {result.rule_id}")
    output.append(f"Document: {result.document}")

    if result.weapon_type and result.weapon_type != "general":
        output.append(f"Weapon: {result.weapon_type}")
        if result.variant:
            output.append(f"Format: {result.variant}")
    elif result.variant:
        output.append(f"Format: {result.variant}")

    output.append(f"\nSection: {result.section}")
    if result.subsection:
        output.append(f"Subsection: {result.subsection}")

    output.append(f"\n{result.text[:300]}...")
    output.append(f"\n[Score: {result.score:.1f}]")

    return "\n".join(output)


def main() -> None:
    """Interactive search CLI"""
    current_dir = Path(__file__).parent.parent / "data"
    index_path = current_dir / "rules_index_hun.json"
    aliases_path = current_dir / "aliases.json"

    if not index_path.exists():
        print("Error: Index not found. Run parser.py first.")
        return

    search = AliasAwareSearch(str(index_path), str(aliases_path))

    print("\n" + "=" * 70)
    print("HEMA Rulebook Search - Alias-Aware")
    print("=" * 70)
    print("\nExample queries:")
    print("  - 'right of way' (will find VOR rules)")
    print("  - 'longsword target area'")
    print("  - 'combat priority'")
    print("  - 'rapier equipment'")
    print("  - 'penalty illegal'")
    print("\nFilters:")
    print("  - search VOR <query>")
    print("  - search longsword <query>")
    print("  - quit to exit")
    print("-" * 70)

    while True:
        try:
            cmd = input("\nQuery: ").strip()

            if not cmd or cmd.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            parts = cmd.split(maxsplit=1)
            variant_filter = None
            weapon_filter = None
            query = cmd

            # Check for filters
            if parts[0].upper() in ["VOR", "COMBAT", "AFTERBLOW"]:
                variant_filter = parts[0].upper()
                query = parts[1] if len(parts) > 1 else ""
            elif parts[0].lower() in ["longsword", "rapier", "padded"]:
                weapon_filter = (
                    parts[0].lower() if parts[0].lower() != "padded" else "padded_weapons"
                )
                query = parts[1] if len(parts) > 1 else ""

            if not query:
                print("Please enter a query.")
                continue

            results = search.search(
                query, max_results=5, variant_filter=variant_filter, weapon_filter=weapon_filter
            )

            if not results:
                print("\nNo results found. Try different keywords or aliases.")
                continue

            print(f"\nFound {len(results)} results:")
            for result in results:
                print(format_result(result))

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
