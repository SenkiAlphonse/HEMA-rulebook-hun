from search_aliases import AliasAwareSearch

search = AliasAwareSearch('rules_index.json', 'aliases.json')

print('=== Test 1: Search "right of way target" ===')
results = search.search('right of way target', max_results=5)
for r in results:
    print(f'  {r.rule_id} (score={r.score}): {r.text[:80]}...')

print('\n=== Test 2: Search "longsword strike" ===')
results = search.search('longsword strike', max_results=5)
for r in results:
    print(f'  {r.rule_id} (score={r.score}, formatum={r.formatum or \"general\"}): {r.text[:60]}...')

print('\n=== Test 3: Search with VOR filter "target" ===')
results = search.search('target', max_results=5, formatum_filter='VOR')
print(f'Found {len(results)} results (should include general + weapon-general + VOR-specific)')
for r in results:
    weapon_label = r.weapon_type if r.weapon_type != 'general' else 'general'
    format_label = r.formatum if r.formatum else 'weapon-general'
    print(f'  {r.rule_id} [{weapon_label}/{format_label}] (score={r.score})')
