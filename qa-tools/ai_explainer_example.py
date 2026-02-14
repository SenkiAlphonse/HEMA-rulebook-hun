"""
Example: How to use hierarchy metadata for AI-assisted explanations

This module demonstrates how the new parent_id, child_ids, lineage, depth, 
is_leaf, and sibling_ids fields enable rich contextual explanations.
"""

import json
from typing import Optional, Dict, Any


class AIExplainer:
    """AI explanation assistant using hierarchy metadata"""
    
    def __init__(self, index_path: str):
        with open(index_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.rules = {r['rule_id']: r for r in self.data['rules']}
    
    def explain_rule(self, rule_id: str) -> Dict[str, Any]:
        """Generate a contextual explanation of a rule with hierarchical context"""
        rule = self.rules.get(rule_id)
        if not rule:
            return {"error": f"Rule {rule_id} not found"}
        
        # Build explanation with hierarchy context
        explanation = {
            "rule_id": rule_id,
            "text": rule['text'][:200] + "...",  # First 200 chars
            "hierarchy": {
                "depth": rule['depth'],
                "is_leaf": rule['is_leaf'],
            }
        }
        
        # Add parent context if exists
        if rule['parent_id']:
            parent = self.rules.get(rule['parent_id'])
            if parent:
                explanation["parent"] = {
                    "id": rule['parent_id'],
                    "section": parent['section'],
                    "subsection": parent['subsection'],
                }
        
        # Add siblings if not a root rule
        if rule['sibling_ids']:
            explanation["related_rules"] = {
                "siblings": rule['sibling_ids'][:5],  # First 5 siblings
                "count": len(rule['sibling_ids'])
            }
        
        # Add children if this is a parent rule
        if rule['child_ids']:
            explanation["has_children"] = {
                "count": len(rule['child_ids']),
                "examples": rule['child_ids'][:3]  # First 3 children
            }
        
        # Build hierarchical path for breadcrumb
        lineage_path = " → ".join(rule['lineage'] + [rule_id])
        explanation["breadcrumb"] = lineage_path
        
        return explanation
    
    def generate_contextual_answer(self, rule_id: str) -> str:
        """Generate a human-readable contextual explanation"""
        rule = self.rules.get(rule_id)
        if not rule:
            return f"Rule {rule_id} not found"
        
        lines = []
        lines.append(f"Rule: {rule_id}")
        lines.append(f"Section: {rule['section']}")
        
        # Show hierarchy context
        if rule['parent_id']:
            parent = self.rules.get(rule['parent_id'])
            if parent:
                lines.append(f"Part of: {rule['parent_id']} ({parent['section']})")
        
        # Show path in hierarchy
        if rule['lineage']:
            lines.append(f"Hierarchy Path: {' > '.join(rule['lineage'])}")
        
        # Show if this rule has sub-rules
        if not rule['is_leaf']:
            lines.append(f"This rule has {len(rule['child_ids'])} sub-rules")
        
        # Show siblings
        if rule['sibling_ids']:
            lines.append(f"Related rules at same level: {', '.join(rule['sibling_ids'][:3])}")
        
        lines.append(f"\n{rule['text'][:400]}...")
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    explainer = AIExplainer("rules_index.json")
    
    print("=" * 80)
    print("AI EXPLANATION EXAMPLES")
    print("=" * 80)
    
    # Example 1: Explain a deep nested rule
    print("\n" + "=" * 40)
    print("Example 1: Explain GEN-3.2.1.1 (Deep nested)")
    print("=" * 40)
    result = explainer.explain_rule("GEN-3.2.1.1")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Example 2: Generate contextual answer
    print("\n" + "=" * 40)
    print("Example 2: Contextual explanation")
    print("=" * 40)
    print(explainer.generate_contextual_answer("GEN-3.2.1.1"))
    
    # Example 3: Show parent rule context
    print("\n" + "=" * 40)
    print("Example 3: Parent rule context")
    print("=" * 40)
    result = explainer.explain_rule("GEN-3.2.1")
    print(json.dumps(result, indent=2, ensure_ascii=False))
