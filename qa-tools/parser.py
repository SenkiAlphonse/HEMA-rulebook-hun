"""
HEMA Rulebook Parser
Extracts structured rule data from markdown files
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class Rule:
    """Represents a single rule in the rulebook"""
    rule_id: str  # e.g., "GEN-1.1.1"
    text: str  # Full rule text
    section: str  # Parent section heading
    subsection: str  # Parent subsection heading
    document: str  # Source document name
    anchor_id: str  # HTML anchor ID for cross-referencing
    line_number: int  # Starting line in source file
    weapon_type: str = ""  # e.g., "longsword", "rapier", or "general"
    formatum: str = ""  # e.g., "VOR", "COMBAT", "AFTERBLOW"
    references_to: List[str] = None  # Rule IDs referenced BY this rule
    references_from: List[str] = None  # Rule IDs that reference THIS rule
    
    def __post_init__(self):
        if self.references_to is None:
            self.references_to = []
        if self.references_from is None:
            self.references_from = []


@dataclass
class Section:
    """Represents a section in the rulebook"""
    title: str
    anchor_id: str
    level: int  # 1 for #, 2 for ##, etc.
    rules: List[Rule]


class RulebookParser:
    """Parse HEMA rulebook markdown files"""
    
    def __init__(self, rulebook_dir: str):
        self.rulebook_dir = Path(rulebook_dir)
        self.rules: List[Rule] = []
        self.sections: List[Section] = []
        
        # Patterns
        self.rule_id_pattern = re.compile(r'\*\*([A-Z]+(?:-[A-Z]+)*-[\d.]+)\*\*')
        self.anchor_pattern = re.compile(r'<span id="([^"]+)"></span>')
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        self.comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
        # Pattern to find rule references in text (e.g., [GEN-6.2.4], [DIS-3.3.9])
        # Matches: [PREFIX-NUM] or [PREFIX-NUM.NUM] or [PREFIX-NUM.NUM.NUM], etc.
        self.reference_pattern = re.compile(r'\[([A-Z]+(?:-[A-Z]+)*(?:-\d+(?:\.\d+)*)?)\]')
        
        
    def parse_all(self) -> Dict[str, Any]:
        """Parse all markdown files in the rulebook directory"""
        md_files = list(self.rulebook_dir.glob("*.md"))
        md_files.extend(list(self.rulebook_dir.glob("fuggelek/*.md")))
        
        # Skip README and architecture docs
        md_files = [f for f in md_files if f.name not in ["README.md", "qa-architecture.md"]]
        
        for md_file in md_files:
            print(f"Parsing {md_file.name}...")
            self.parse_file(md_file)
        
        # Build cross-reference index
        print("Building cross-reference index...")
        self._build_cross_references()
        
        return {
            "rules": [asdict(rule) for rule in self.rules],
            "total_rules": len(self.rules),
            "documents": list(set(rule.document for rule in self.rules))
        }
    
    def parse_file(self, filepath: Path):
        """Parse a single markdown file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract weapon type and formatum from filename
        weapon_type, formatum = self._extract_weapon_info(filepath.name)

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
                        current_rule_id, rule_text_lines, current_section,
                        current_subsection, filepath.name, current_anchor,
                        rule_start_line, weapon_type, formatum
                    )
                    current_rule_id = ""
                    rule_text_lines = []
                
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                if level == 1:
                    current_section = title
                    current_subsection = ""
                elif level == 2:
                    current_subsection = title
                elif level == 3:
                    current_subsection = title
                
                continue
            
            # Check for anchor ID
            anchor_match = self.anchor_pattern.search(line)
            if anchor_match:
                current_anchor = anchor_match.group(1)
                continue
            
            # Check for rule ID (only at start of line after stripping)
            stripped_line = line.strip()
            rule_id_match = self.rule_id_pattern.match(stripped_line)  # Use match() to require start of string
            if rule_id_match:
                # Save previous rule if exists
                if current_rule_id and rule_text_lines:
                    self._save_rule(
                        current_rule_id, rule_text_lines, current_section,
                        current_subsection, filepath.name, current_anchor,
                        rule_start_line, weapon_type, formatum
                    )

                # Start new rule
                current_rule_id = rule_id_match.group(1)
                rule_text_lines = []
                rule_start_line = i
                continue
            
            # Accumulate rule text
            if current_rule_id:
                stripped = line.strip()
                if stripped and not stripped.startswith('---'):
                    # Remove HTML comments
                    cleaned = self.comment_pattern.sub('', stripped).strip()
                    if cleaned:  # Only add if there's content after removing comments
                        rule_text_lines.append(cleaned)
        
        # Save last rule if exists
        if current_rule_id and rule_text_lines:
            self._save_rule(
                current_rule_id, rule_text_lines, current_section,
                current_subsection, filepath.name, current_anchor,
                rule_start_line, weapon_type, formatum
            )
    
    def _save_rule(self, rule_id: str, text_lines: List[str], section: str,
                   subsection: str, document: str, anchor: str, line_num: int,
                   weapon_type: str, formatum: str):
        """Save a parsed rule, detecting variant from text if present"""
        text = " ".join(text_lines).strip()
        if text:
            # Extract formatum from rule text if it starts with **Vor**:, **Combat**:, **Afterblow**:
            detected_formatum = self._detect_formatum_in_rule_text(text)
            if detected_formatum:
                formatum = detected_formatum
            
            rule = Rule(
                rule_id=rule_id,
                text=text,
                section=section,
                subsection=subsection,
                document=document,
                anchor_id=anchor,
                line_number=line_num,
                weapon_type=weapon_type,
                formatum=formatum
            )
            self.rules.append(rule)
    
    def _detect_formatum_in_rule_text(self, text: str) -> str:
        """
        Detect formatum (VOR, COMBAT, AFTERBLOW) from rule text.
        Checks if text starts with **Vor**:, **Combat**:, **Afterblow**:
        Note: The colon can be inside or outside the asterisks.
        """
        text_strip = text.strip()
        
        # Pattern: **Word**: at the start (handles both **Word**: and **Word:**)
        variant_start_pattern = re.compile(r'^\*\*(Vor|Combat|Afterblow)\*\*:?', re.IGNORECASE)
        match = variant_start_pattern.match(text_strip)
        
        if match:
            variant_name = match.group(1).upper()
            # Normalize variant names
            if variant_name == 'VOR':
                return 'VOR'
            elif variant_name == 'COMBAT':
                return 'COMBAT'
            elif variant_name == 'AFTERBLOW':
                return 'AFTERBLOW'
        
        return ''
    
    def _detect_formatum_in_rule_text(self, text: str) -> str:
        """
        Detect formatum (VOR, COMBAT, AFTERBLOW) from rule text.
        Checks if text starts with **Vor**: or **Combat**: or **Afterblow**:
        (with colon OUTSIDE the bold markers)
        """
        text_strip = text.strip()
        
        # Pattern: **Word**: with colon outside the asterisks
        variant_start_pattern = re.compile(r'^\*\*(vor|combat|afterblow)\*\*:', re.IGNORECASE)
        match = variant_start_pattern.match(text_strip)
        
        if match:
            variant_name = match.group(1).upper()
            # Normalize variant names
            if variant_name == 'VOR':
                return 'VOR'
            elif variant_name == 'COMBAT':
                return 'COMBAT'
            elif variant_name == 'AFTERBLOW':
                return 'AFTERBLOW'
        
        return ''
    
    def _extract_variant_subrules(self, parent_rule_id: str, text: str, section: str,
                                   subsection: str, document: str, anchor: str, line_num: int,
                                   weapon_type: str) -> List[Rule]:
        """
        Extract variant-specific sub-rules from text containing Vor/Combat/Afterblow sections.
        Returns a list of extracted sub-rules, or empty list if no variants found.
        """
        # Pattern to detect variant headers: **Vor**:, **Combat:**:, **Afterblow**:
        variant_pattern = re.compile(r'\*\*(Vor|Combat|Afterblow)\*\*:?\s*(.+?)(?=\*\*(?:Vor|Combat|Afterblow)\*\*|$)', 
                                    re.IGNORECASE | re.DOTALL)
        
        matches = list(variant_pattern.finditer(text))
        
        # Only proceed if we find multiple variants (indicating variant-split content)
        if len(matches) < 2:
            return []
        
        extracted_rules = []
        
        for match in matches:
            variant_name = match.group(1).upper()
            variant_text = match.group(2).strip()
            
            if not variant_text:
                continue
            
            # Create a sub-rule ID for this variant (e.g., GEN-6.10.4.1 for Vor)
            variant_subrule_id = f"{parent_rule_id}.{self._variant_to_subrule_index(variant_name)}"
            
            rule = Rule(
                rule_id=variant_subrule_id,
                text=f"**{variant_name}**: {variant_text}",
                section=section,
                subsection=subsection,
                document=document,
                anchor_id=anchor,
                line_number=line_num,
                weapon_type=weapon_type,
                formatum=variant_name
            )
            extracted_rules.append(rule)
        
        return extracted_rules
    
    def _variant_to_subrule_index(self, variant: str) -> str:
        """Map variant name to subrule index (1=Vor, 2=Combat, 3=Afterblow)"""
        mapping = {
            "VOR": "1",
            "COMBAT": "2", 
            "AFTERBLOW": "3"
        }
        return mapping.get(variant.upper(), "0")
    
    def _extract_weapon_info(self, filename: str) -> tuple:
        """Extract weapon type and formatum from filename"""
        weapon_type = "general"
        formatum = ""

        if "hosszukard" in filename.lower():
            weapon_type = "longsword"
            if "VOR" in filename:
                formatum = "VOR"
            elif "COMBAT" in filename:
                formatum = "COMBAT"
            elif "AFTERBLOW" in filename:
                formatum = "AFTERBLOW"
        elif "rapir" in filename.lower():
            weapon_type = "rapier"
        elif "parnazott" in filename.lower():
            weapon_type = "padded_weapons"

        return weapon_type, formatum

    def _build_cross_references(self):
        """Build cross-reference index by scanning rule text for references"""
        # First pass: extract all references each rule makes
        for rule in self.rules:
            # Find all rule IDs in bold (**GEN-...**) mentioned in this rule's text
            matches = self.reference_pattern.findall(rule.text)
            # Remove duplicates and self-references
            references = set(m for m in matches if m != rule.rule_id)
            rule.references_to = sorted(list(references))
        
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
            rule.references_from = sorted(list(set(rule.references_from)))
    
    def save_index(self, output_path: Path):
        """Save parsed rules to JSON index"""
        index_data = self.parse_all()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nIndex saved to {output_path}")
        print(f"Total rules indexed: {index_data['total_rules']}")
        print(f"Documents processed: {len(index_data['documents'])}")



def main():
    """Main entry point"""
    # Get the rulebook directory (parent of qa-tools)
    current_dir = Path(__file__).parent.parent
    
    parser = RulebookParser(current_dir)
    parser.save_index(current_dir / "qa-tools" / "rules_index.json")


if __name__ == "__main__":
    main()
