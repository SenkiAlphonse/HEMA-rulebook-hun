"""
HEMA Rulebook Parser
Extracts structured rule data from markdown files
"""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.config import get_project_root, get_rules_index_path
from app.utils.markdown_utils import strip_markdown


@dataclass
class Rule:
    """Represents a single rule in the rulebook"""

    rule_id: str  # e.g., "GEN-1.1.1"
    text: str  # Full rule text (markdown-formatted)
    section: str  # Parent section heading
    subsection: str  # Parent subsection heading
    document: str  # Source document name
    anchor_id: str  # HTML anchor ID for cross-referencing
    line_number: int  # Starting line in source file
    text_plain: str = ""  # Plain text for search (no formatting)
    weapon_type: str = ""  # e.g., "longsword", "rapier", or "general"
    variant: str = ""  # e.g., "VOR", "COMBAT", "AFTERBLOW"
    references_to: list[str] = None  # Rule IDs referenced BY this rule
    references_from: list[str] = None  # Rule IDs that reference THIS rule
    # Hierarchy metadata (computed at parse time)
    parent_id: str = ""  # Direct parent rule ID (e.g., "GEN-3.2.1" for "GEN-3.2.1.1")
    child_ids: list[str] = None  # All direct child rule IDs
    lineage: list[str] = None  # Path from root to parent (e.g., ["GEN", "GEN-3", "GEN-3.2"])
    depth: int = 0  # Nesting level (1=top, 5=deepest)
    is_leaf: bool = True  # True if no children
    sibling_ids: list[str] = None  # Direct siblings (same parent)
    language: str = "hun"  # Index language code (hun/eng)

    def __post_init__(self):
        if self.references_to is None:
            self.references_to = []
        if self.references_from is None:
            self.references_from = []
        if self.child_ids is None:
            self.child_ids = []
        if self.lineage is None:
            self.lineage = []
        if self.sibling_ids is None:
            self.sibling_ids = []


@dataclass
class Section:
    """Represents a section in the rulebook"""

    title: str
    anchor_id: str
    level: int  # 1 for #, 2 for ##, etc.
    rules: list[Rule]


class RulebookParser:
    """Parse HEMA rulebook markdown files"""

    def __init__(self, rulebook_dir: str, rules_subdir: str = "rules", language: str = "hun"):
        self.rulebook_dir = Path(rulebook_dir)
        self.rules_subdir = rules_subdir
        self.language = language
        self.rules: list[Rule] = []
        self.rule_id_index: dict[str, Rule] = {}  # O(1) lookup by rule_id
        self.sections: list[Section] = []

        # Patterns
        self.rule_id_pattern = re.compile(r"\*\*([A-Z]+(?:-[A-Z]+)*-[\d.]+)\*\*")
        self.anchor_pattern = re.compile(r'<span id="([^"]+)"></span>')
        self.heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
        self.comment_pattern = re.compile(r"<!--.*?-->", re.DOTALL)
        # Pattern to find rule references in text (e.g., [GEN-6.2.4], [DIS-3.3.9])
        # Matches: [PREFIX-NUM] or [PREFIX-NUM.NUM] or [PREFIX-NUM.NUM.NUM], etc.
        self.reference_pattern = re.compile(r"\[([A-Z]+(?:-[A-Z]+)*(?:-\d+(?:\.\d+)*)?)\]")

    def parse_all(self) -> dict[str, Any]:
        """Parse all markdown files in the rules directory"""
        rules_dir = self.rulebook_dir / self.rules_subdir

        if not rules_dir.exists():
            raise FileNotFoundError(f"Rules directory not found: {rules_dir}")

        # Parse all markdown files in the rules directory (no filtering needed)
        md_files = sorted(rules_dir.glob("*.md"))
        md_files.extend(sorted(rules_dir.glob("*/*.md")))

        if not md_files:
            raise FileNotFoundError(f"No markdown files found in {rules_dir}")

        for md_file in md_files:
            print(f"Parsing {md_file.relative_to(self.rulebook_dir)}...")
            self.parse_file(md_file)

        # Build cross-reference index
        print("Building cross-reference index...")
        self._build_cross_references()

        # Build hierarchy metadata (parent-child relationships)
        print("Building hierarchy metadata...")
        self._build_hierarchy_metadata()

        return {
            "rules": [asdict(rule) for rule in self.rules],
            "total_rules": len(self.rules),
            "documents": list({rule.document for rule in self.rules}),
            "language": self.language,
        }

    def parse_file(self, filepath: Path):
        """Parse a single markdown file"""
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Strip multi-line HTML comment blocks before line processing so that
        # rule IDs inside <!-- ... --> blocks are never indexed.
        content = self.comment_pattern.sub("", content)
        lines = content.splitlines(keepends=True)

        # Extract weapon type and variant from filename
        weapon_type, variant = self._extract_weapon_info(filepath.name)

        current_section = ""
        current_subsection = ""
        current_anchor = ""
        current_rule_id = ""
        rule_text_lines = []
        rule_start_line = 0

        for i, line in enumerate(lines, start=1):
            # Check for heading
            heading_match = self.heading_pattern.match(line)
            if heading_match:
                # Save any pending rule
                if current_rule_id and rule_text_lines:
                    self._save_rule(
                        current_rule_id,
                        rule_text_lines,
                        current_section,
                        current_subsection,
                        filepath.name,
                        current_anchor,
                        rule_start_line,
                        weapon_type,
                        variant,
                    )
                    current_rule_id = ""
                    rule_text_lines = []

                level = len(heading_match.group(1))
                title = self.comment_pattern.sub("", heading_match.group(2)).strip()

                if level == 1:
                    current_section = title
                    current_subsection = ""
                elif level in (2, 3):
                    current_subsection = title

                continue

            # Check for anchor ID
            anchor_match = self.anchor_pattern.search(line)
            if anchor_match:
                current_anchor = anchor_match.group(1)
                continue

            # Check for rule ID (only at start of line after stripping)
            stripped_line = line.strip()
            rule_id_match = self.rule_id_pattern.match(
                stripped_line
            )  # Use match() to require start of string
            if rule_id_match:
                # Save previous rule if exists
                if current_rule_id and rule_text_lines:
                    self._save_rule(
                        current_rule_id,
                        rule_text_lines,
                        current_section,
                        current_subsection,
                        filepath.name,
                        current_anchor,
                        rule_start_line,
                        weapon_type,
                        variant,
                    )

                # Start new rule
                current_rule_id = rule_id_match.group(1)
                rule_text_lines = []
                rule_start_line = i
                continue

            # Accumulate rule text
            if current_rule_id:
                stripped = line.strip()
                if stripped and not stripped.startswith("---"):
                    # Preserve leading whitespace for indented list items so
                    # multilevel nested lists keep their nesting depth
                    if line.lstrip() != line:
                        cleaned = self.comment_pattern.sub("", line.rstrip())
                    else:
                        cleaned = self.comment_pattern.sub("", stripped).strip()
                    if cleaned.strip():  # Only add if there's content after removing comments
                        rule_text_lines.append(cleaned)

        # Save last rule if exists
        if current_rule_id and rule_text_lines:
            self._save_rule(
                current_rule_id,
                rule_text_lines,
                current_section,
                current_subsection,
                filepath.name,
                current_anchor,
                rule_start_line,
                weapon_type,
                variant,
            )

    def _save_rule(
        self,
        rule_id: str,
        text_lines: list[str],
        section: str,
        subsection: str,
        document: str,
        anchor: str,
        line_num: int,
        weapon_type: str,
        variant: str,
    ) -> None:
        """Save a parsed rule, detecting variant from text if present"""
        # Join text lines preserving structure:
        # - Lines starting with "- " (bullets) keep newlines
        # - Other lines are joined with newlines to preserve paragraph breaks
        formatted_lines = []
        for line in text_lines:
            # If line starts with "- ", mark it as a bullet point
            if line.startswith("- "):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        # Join with newlines to preserve all line breaks
        text = "\n".join(formatted_lines).strip()
        text_plain = strip_markdown(text)

        if text:
            # Extract variant from rule text if it starts with **Vor**:, **Combat**:, **Afterblow**:
            detected_variant = self._detect_variant_in_rule_text(text)
            if detected_variant:
                variant = detected_variant
            rule = Rule(
                rule_id=rule_id,
                text=text,
                text_plain=text_plain,
                section=section,
                subsection=subsection,
                document=document,
                anchor_id=anchor,
                line_number=line_num,
                weapon_type=weapon_type,
                variant=variant,
                language=self.language,
            )
            self.rules.append(rule)
            self.rule_id_index[rule_id] = rule  # Add to O(1) lookup index

    def _detect_variant_in_rule_text(self, text: str) -> str:
        """
        Detect variant (VOR, COMBAT, AFTERBLOW) from rule text.
        Checks if text starts with **Vor**:, **Combat**:, **Afterblow**:
        Note: The colon can be inside or outside the asterisks.
        """
        text_strip = text.strip()

        # Pattern: **Word**: at the start (handles both **Word**: and **Word:**)
        variant_start_pattern = re.compile(r"^\*\*(Vor|Combat|Afterblow)\*\*:?", re.IGNORECASE)
        match = variant_start_pattern.match(text_strip)

        if match:
            variant_name = match.group(1).upper()
            # Normalize variant names
            if variant_name in {"VOR", "COMBAT", "AFTERBLOW"}:
                return variant_name

        return ""

    def _extract_variant_subrules(
        self,
        parent_rule_id: str,
        text: str,
        section: str,
        subsection: str,
        document: str,
        anchor: str,
        line_num: int,
        weapon_type: str,
    ) -> list[Rule]:
        """
        Extract variant-specific sub-rules from text containing Vor/Combat/Afterblow sections.
        Returns a list of extracted sub-rules, or empty list if no variants found.
        """

    def _variant_to_subrule_index(self, variant: str) -> str:
        """Map variant name to subrule index (1=Vor, 2=Combat, 3=Afterblow)"""

    def _extract_weapon_info(self, filename: str) -> tuple:  # tuple[str, str]
        """Extract weapon type and variant from filename"""
        weapon_type = "general"
        variant = ""

        lower_name = filename.lower()

        if "hosszukard" in lower_name or "longsword" in lower_name:
            weapon_type = "longsword"
            if "VOR" in filename:
                variant = "VOR"
            elif "COMBAT" in filename:
                variant = "COMBAT"
            elif "AFTERBLOW" in filename:
                variant = "AFTERBLOW"
        elif "rapir" in lower_name or "rapier" in lower_name:
            weapon_type = "rapier"
        elif "parnazott" in lower_name or "padded" in lower_name:
            weapon_type = "padded_weapons"

        return weapon_type, variant

    def _build_cross_references(self) -> None:
        """Build cross-reference index by scanning rule text for references"""
        # First pass: extract all references each rule makes
        for rule in self.rules:
            # Find all rule IDs in bold (**GEN-...**) mentioned in this rule's text
            matches = self.reference_pattern.findall(rule.text)
            # Remove duplicates and self-references
            references = {m for m in matches if m != rule.rule_id}
            rule.references_to = sorted(references)

        # Second pass: build reverse references (references_from)
        rule_by_id = {rule.rule_id: rule for rule in self.rules}

        for rule in self.rules:
            rule.references_from = []

        for rule in self.rules:
            for referenced_id in rule.references_to:
                if referenced_id in rule_by_id:
                    rule_by_id[referenced_id].references_from.append(rule.rule_id)

        # Remove duplicates and sort
        for rule in self.rules:
            rule.references_from = sorted(set(rule.references_from))

    def _build_hierarchy_metadata(self) -> None:
        """Build parent-child hierarchy metadata for all rules"""
        # First pass: compute parent_id, depth, and lineage for each rule
        for rule in self.rules:
            rule.depth = self._get_rule_depth(rule.rule_id)
            rule.parent_id = self._get_parent_id(rule.rule_id)
            rule.lineage = self._get_rule_lineage(rule.rule_id)

        # Second pass: find direct children for each rule (using sets to avoid duplicates)
        parent_to_children = {}
        for rule in self.rules:
            if rule.parent_id:
                if rule.parent_id not in parent_to_children:
                    parent_to_children[rule.parent_id] = set()
                parent_to_children[rule.parent_id].add(rule.rule_id)

        # Assign child_ids and is_leaf to each rule (convert sets to sorted lists)
        for rule in self.rules:
            child_set = parent_to_children.get(rule.rule_id, set())
            rule.child_ids = sorted(child_set)
            rule.is_leaf = len(rule.child_ids) == 0

        # Third pass: find siblings for each rule (using sets to avoid duplicates)
        for rule in self.rules:
            if rule.parent_id:
                # Siblings are all children of parent except self (using set difference)
                sibling_set = parent_to_children.get(rule.parent_id, set()) - {rule.rule_id}
                rule.sibling_ids = sorted(sibling_set)
            else:
                rule.sibling_ids = []

    def _get_rule_depth(self, rule_id: str) -> int:
        """Calculate nesting depth from rule ID (delegates to shared utils)"""
        from qa_tools.search_engine.search_utils import get_rule_depth

        return get_rule_depth(rule_id)

    def _get_parent_id(self, rule_id: str) -> str:
        """Get direct parent rule ID from a given rule"""
        lineage = self._get_rule_lineage(rule_id)
        return lineage[-1] if lineage else ""

    def _get_rule_lineage(self, rule_id: str) -> list:
        """Get list of parent rule IDs (delegates to shared utils)"""
        from qa_tools.search_engine.search_utils import get_rule_lineage

        return get_rule_lineage(rule_id)

    def save_index(self, output_path: Path) -> None:
        """Save parsed rules to JSON index"""
        index_data = self.parse_all()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"\nIndex saved to {output_path}")
        print(f"Total rules indexed: {index_data['total_rules']}")
        print(f"Documents processed: {len(index_data['documents'])}")


def main() -> None:
    """Main entry point"""
    project_root = get_project_root()
    parser = RulebookParser(project_root, rules_subdir="rules", language="hun")
    output_path = get_rules_index_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parser.save_index(output_path)


if __name__ == "__main__":
    main()
