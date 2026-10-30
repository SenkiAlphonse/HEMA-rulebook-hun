"""
Enhanced HEMA Rulebook Search Engine with Alias Support
"""

import json
import logging
import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from qa_tools.search_engine import search_config
from qa_tools.search_engine.search_scoring import normalize_text, score_rule, split_rule_ids
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


@dataclass
class SearchResultGroup:
    """Ranked matches with their shared hierarchy context.

    cited_by lists rules that cite a rule the query named by ID; they are not matches.
    """

    group_root: str
    context: list[SearchResult]
    matches: list[SearchResult]
    cited_by: list[SearchResult] = field(default_factory=list)


@dataclass
class ExpandedQuery:
    """Result of resolving a raw user query against the alias dictionary.

    Attributes:
        alias_groups: One list of interchangeable phrases per alias group the query named.
        base_query: Original query with the recognised alias phrases and rule IDs removed.
        rule_ids: Lowercase rule IDs the query named, such as "gen-6.2.1".
    """

    alias_groups: list[list[str]]
    base_query: str
    rule_ids: list[str]


class AliasAwareSearch:
    """Search engine with alias support for HEMA rulebook"""

    def __init__(self, index_path: str, aliases_path: str | None = None):
        self.index_path = Path(index_path)
        self.rules = []
        self.aliases = {}
        self.alias_groups = {}  # (category, key) -> interchangeable phrases
        self.alias_to_key = {}  # Reverse lookup: alias -> (category, key)
        self.alias_token_lookup = {}
        self.alias_token_lengths = []

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
        """Index every alias phrase under the group it belongs to."""
        for category in ("variants", "weapons", "concepts"):
            for key, aliases in self.aliases.get(category, {}).items():
                group_id = (category, key)
                self.alias_groups[group_id] = list(aliases)
                for alias in aliases:
                    self.alias_to_key[alias.lower()] = group_id

        for alias, value in self.alias_to_key.items():
            tokens = tuple(re.findall(r"\w+", alias))
            if tokens:
                self.alias_token_lookup[tokens] = value
        self.alias_token_lengths = sorted(
            {len(tokens) for tokens in self.alias_token_lookup}, reverse=True
        )

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

    def _expand_query(self, query: str) -> ExpandedQuery:
        """Split a query into rule IDs, the alias groups it names, and the remaining plain words.

        Args:
            query: Original search query

        Returns:
            ExpandedQuery with the rule IDs, matched alias groups and unrecognised words.
        """
        alias_groups: list[list[str]] = []
        seen_group_ids = set()
        remaining_terms: list[str] = []

        query_without_ids, rule_ids = split_rule_ids(query)
        words = re.findall(r"\w+", query_without_ids.lower())

        word_index = 0
        while word_index < len(words):
            group_id = None
            alias_length = 0
            for candidate_length in self.alias_token_lengths:
                candidate = tuple(words[word_index : word_index + candidate_length])
                if candidate in self.alias_token_lookup:
                    group_id = self.alias_token_lookup[candidate]
                    alias_length = candidate_length
                    break

            if group_id is None:
                remaining_terms.append(words[word_index])
                word_index += 1
                continue

            if group_id not in seen_group_ids:
                seen_group_ids.add(group_id)
                alias_groups.append(self.alias_groups[group_id])
            word_index += alias_length

        return ExpandedQuery(
            alias_groups=alias_groups,
            base_query=" ".join(remaining_terms),
            rule_ids=rule_ids,
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching by removing accents and converting to lowercase.

        Args:
            text: Text to normalize

        Returns:
            Normalized text without diacritics, in lowercase
        """
        return normalize_text(text)

    def search(
        self,
        query: str,
        max_results: int | None = None,
        variant_filter: str | None = None,
        weapon_filter: str | None = None,
    ) -> list[SearchResult]:
        """Search and return a flat, deduplicated compatibility view."""
        groups = self.search_grouped(
            query,
            max_results=max_results,
            variant_filter=variant_filter,
            weapon_filter=weapon_filter,
        )
        flattened = []
        seen_rule_ids = set()

        for group in groups:
            context_score = max((match.score for match in group.matches), default=0.0)
            for result in group.context:
                if result.rule_id in seen_rule_ids:
                    continue
                seen_rule_ids.add(result.rule_id)
                flattened.append(
                    SearchResult(
                        rule_id=result.rule_id,
                        text=result.text,
                        section=result.section,
                        subsection=result.subsection,
                        document=result.document,
                        weapon_type=result.weapon_type,
                        variant=result.variant,
                        score=context_score,
                    )
                )
            for result in group.matches:
                if result.rule_id in seen_rule_ids:
                    continue
                seen_rule_ids.add(result.rule_id)
                flattened.append(result)

        flattened.sort(key=lambda result: result.score, reverse=True)
        return flattened

    def search_grouped(
        self,
        query: str,
        max_results: int | None = None,
        variant_filter: str | None = None,
        weapon_filter: str | None = None,
    ) -> list[SearchResultGroup]:
        """
        Search and group ranked hits with their relevant rule ancestry.

        Args:
            query: Search query
            max_results: Max results to return (defaults to config)
            variant_filter: Only rules of this variant (VOR, COMBAT, AFTERBLOW) and general rules
            weapon_filter: Only rules of this weapon (longsword, rapier, etc.) and general rules
        """
        expanded = self._expand_query(query)

        # Alias phrases and rule IDs are matched on their own, so only the rest is a phrase query.
        phrase_query = expanded.base_query
        terms = self._extract_terms(self._normalize_text(phrase_query))

        results = []

        for rule in self.rules:
            if not self._passes_filters(rule, variant_filter, weapon_filter):
                continue

            score = score_rule(
                rule,
                query=query,
                phrase_query=phrase_query,
                terms=terms,
                alias_groups=expanded.alias_groups,
            )

            if score > 0:
                results.append(self._to_result(rule, score))

        results.sort(key=lambda x: x.score, reverse=True)
        results = self._deduplicate_results_by_rule_id(results)

        # Use default max results if not provided
        if max_results is None:
            max_results = search_config.DEFAULT_MAX_RESULTS
        groups = self._group_search_results(results, max_results)
        self._attach_citing_rules(groups, expanded.rule_ids, variant_filter, weapon_filter)
        return groups

    @staticmethod
    def _passes_filters(
        rule: dict[str, Any], variant_filter: str | None, weapon_filter: str | None
    ) -> bool:
        """Apply the explicit variant/weapon filters with their hierarchy.

        - General rules (weapon_type='general') apply to everything
        - Weapon-general rules (no variant) apply to all variants of that weapon
        - Format-specific rules apply only to that variant
        """
        rule_weapon = rule.get("weapon_type", "general")
        rule_variant = rule.get("variant", "")

        if weapon_filter and rule_weapon != "general" and rule_weapon != weapon_filter:
            return False
        return not (
            variant_filter
            and rule_weapon != "general"
            and rule_variant
            and rule_variant != variant_filter
        )

    @staticmethod
    def _to_result(rule: dict[str, Any], score: float) -> SearchResult:
        return SearchResult(
            rule_id=rule["rule_id"],
            text=rule.get("text", ""),
            section=rule.get("section", ""),
            subsection=rule.get("subsection", ""),
            document=rule.get("document", ""),
            weapon_type=rule.get("weapon_type", ""),
            variant=rule.get("variant", ""),
            score=score,
        )

    def _attach_citing_rules(
        self,
        groups: list[SearchResultGroup],
        queried_ids: list[str],
        variant_filter: str | None,
        weapon_filter: str | None,
    ) -> None:
        """Add the rules citing a rule the query named by ID to that rule's group."""
        if not queried_ids:
            return

        shown_ids = {r.rule_id for group in groups for r in (*group.context, *group.matches)}
        for group in groups:
            for match in group.matches:
                if match.rule_id.lower() not in queried_ids:
                    continue
                cited_rule = self.get_rule_by_id(match.rule_id) or {}
                for citing_id in cited_rule.get("references_from", []):
                    citing = self.get_rule_by_id(citing_id)
                    if (
                        citing
                        and citing_id not in shown_ids
                        and self._passes_filters(citing, variant_filter, weapon_filter)
                    ):
                        shown_ids.add(citing_id)
                        group.cited_by.append(self._to_result(citing, 0.0))

    def _group_search_results(
        self, results: list[SearchResult], max_results: int
    ) -> list[SearchResultGroup]:
        """Group selected matches by their nearest level-3 ancestor."""
        selected_matches = results[:max_results]
        groups_by_root: dict[str, SearchResultGroup] = {}

        for result in selected_matches:
            depth = self.get_rule_depth(result.rule_id)
            group_root = result.rule_id
            if depth >= 4:
                group_root = next(
                    (
                        ancestor_id
                        for ancestor_id in reversed(self.get_rule_lineage(result.rule_id))
                        if self.get_rule_depth(ancestor_id) == 3
                    ),
                    result.rule_id,
                )

            group = groups_by_root.setdefault(
                group_root,
                SearchResultGroup(group_root=group_root, context=[], matches=[]),
            )
            group.matches.append(result)

        selected_ids = {result.rule_id for result in selected_matches}
        for group in groups_by_root.values():
            context_ids = []
            seen_context_ids = set()
            for match in group.matches:
                if self.get_rule_depth(match.rule_id) < 4:
                    continue
                for ancestor_id in self.get_rule_lineage(match.rule_id):
                    if (
                        self.get_rule_depth(ancestor_id) in {3, 4}
                        and ancestor_id not in selected_ids
                        and ancestor_id not in seen_context_ids
                    ):
                        context_ids.append(ancestor_id)
                        seen_context_ids.add(ancestor_id)

            for context_id in context_ids:
                rule = self.get_rule_by_id(context_id)
                if rule:
                    group.context.append(self._to_result(rule, 0.0))

        return list(groups_by_root.values())

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

    def suggest(self, query: str, max_suggestions: int = 5) -> list[str]:
        """Return near-match suggestions for a query that produced zero results.

        Strategy:
        1. If the query looks like a rule ID, suggest similar rule IDs.
        2. Otherwise, tokenise and suggest closest known alias keys for each
           token using difflib's ratio.

        Args:
            query: The original (non-empty) user query.
            max_suggestions: Cap on returned suggestions.

        Returns:
            Ordered list of suggestion strings, best matches first. May be empty.
        """
        q = (query or "").strip()
        if not q:
            return []

        # Heuristic: looks like a rule ID (contains '-' and digits)
        if "-" in q and any(ch.isdigit() for ch in q):
            ids = [r.get("rule_id", "") for r in self.rules if r.get("rule_id")]
            return get_close_matches(q.upper(), ids, n=max_suggestions, cutoff=0.6)

        # Otherwise: per-token nearest alias key
        tokens = re.findall(r"\w+", q.lower())
        if not tokens:
            return []

        candidates = list(self.alias_to_key.keys())
        if not candidates:
            return []

        suggestions: list[str] = []
        seen: set[str] = set()
        for tok in tokens:
            if tok in self.alias_to_key:
                continue  # already a known term, no suggestion needed
            for match in get_close_matches(tok, candidates, n=2, cutoff=0.7):
                if match not in seen:
                    seen.add(match)
                    suggestions.append(match)
                    if len(suggestions) >= max_suggestions:
                        return suggestions
        return suggestions


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
    print("  - 'right of way' (also finds 'priority' and related terms)")
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
