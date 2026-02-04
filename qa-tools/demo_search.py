"""
Quick demo of the HEMA rulebook search
Usage: python qa-tools\demo_search.py "your query here"
"""

import sys
from pathlib import Path
from search import RulebookSearch, format_result

def main():
    if len(sys.argv) < 2:
        print("Usage: python demo_search.py 'your query'")
        print("\nExample queries:")
        print("  python demo_search.py 'találati felület'")
        print("  python demo_search.py 'valid target areas'")
        print("  python demo_search.py 'GEN-1.1.1'")
        return
    
    query = " ".join(sys.argv[1:])
    
    # Initialize search
    index_path = Path(__file__).parent / "rules_index.json"
    search_engine = RulebookSearch(str(index_path))
    
    # Search
    print(f"\nSearching for: '{query}'\n")
    results = search_engine.search(query, max_results=3)
    
    if not results:
        print("No results found. Try different keywords.")
        return
    
    print(f"Found {len(results)} results:\n")
    
    for result in results:
        print(format_result(result))

if __name__ == "__main__":
    main()
