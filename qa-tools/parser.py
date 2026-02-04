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
    variant: str = ""  # e.g., "VOR", "COMBAT", "AFTERBLOW"


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
        self.rule_id_pattern = re.compile(r'\*\*([A-Z]+-[\d.]+)\*\*')
        self.anchor_pattern = re.compile(r'<span id="([^"]+)"></span>')
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        
    def parse_all(self) -> Dict[str, Any]:
        """Parse all markdown files in the rulebook directory"""
        md_files = list(self.rulebook_dir.glob("*.md"))
        md_files.extend(list(self.rulebook_dir.glob("fuggelek/*.md")))
        
        # Skip README and architecture docs
        md_files = [f for f in md_files if f.name not in ["README.md", "qa-architecture.md"]]
        
        for md_file in md_files:
            print(f"Parsing {md_file.name}...")
            self.parse_file(md_file)
        
        return {
            "rules": [asdict(rule) for rule in self.rules],
            "total_rules": len(self.rules),
            "documents": list(set(rule.document for rule in self.rules))
        }
    
    def parse_file(self, filepath: Path):
        """Parse a single markdown file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
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
                        current_rule_id, rule_text_lines, current_section,
                        current_subsection, filepath.name, current_anchor,
                        rule_start_line, weapon_type, variant
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
            
            # Check for rule ID
            rule_id_match = self.rule_id_pattern.search(line)
            if rule_id_match:
                # Save previous rule if exists
                if current_rule_id and rule_text_lines:
                    self._save_rule(
                        current_rule_id, rule_text_lines, current_section,
                        current_subsection, filepath.name, current_anchor,
                        rule_start_line, weapon_type, variant
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
                    rule_text_lines.append(stripped)
        
        # Save last rule if exists
        if current_rule_id and rule_text_lines:
            self._save_rule(
                current_rule_id, rule_text_lines, current_section,
                current_subsection, filepath.name, current_anchor,
                rule_start_line, weapon_type, variant
            )
    
    def _save_rule(self, rule_id: str, text_lines: List[str], section: str,
                   subsection: str, document: str, anchor: str, line_num: int,
                   weapon_type: str, variant: str):
        """Save a parsed rule"""
        text = " ".join(text_lines).strip()
        if text:
            rule = Rule(
                rule_id=rule_id,
                text=text,
                section=section,
                subsection=subsection,
                document=document,
                anchor_id=anchor,
                line_number=line_num,
                weapon_type=weapon_type,
                variant=variant
            )
            self.rules.append(rule)
    
    def _extract_weapon_info(self, filename: str) -> tuple:
        """Extract weapon type and variant from filename"""
        weapon_type = "general"
        variant = ""
        
        if "hosszukard" in filename.lower():
            weapon_type = "longsword"
            if "VOR" in filename:
                variant = "VOR"
            elif "COMBAT" in filename:
                variant = "COMBAT"
            elif "AFTERBLOW" in filename:
                variant = "AFTERBLOW"
        elif "rapir" in filename.lower():
            weapon_type = "rapier"
        elif "parnazott" in filename.lower():
            weapon_type = "padded_weapons"
        
        return weapon_type, variant
    
    def save_index(self, output_path: str):
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
