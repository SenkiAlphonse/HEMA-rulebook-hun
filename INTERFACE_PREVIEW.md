# Web Interface Preview

## What Fencers See

### Home Page
```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║                  ⚔️ HEMA Rulebook Search                   ║
║     Hungarian Historical European Martial Arts             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

┌─ Search ────────────────────────────────────────────────────┐
│                                                              │
│  Search Query          │ Format │ Weapon  │ [Search]        │
│  [e.g., 'longsword']   │ [All ▼]│[All ▼] │                 │
│                        │        │         │                 │
└──────────────────────────────────────────────────────────────┘

┌─ Statistics ────────────────────────────────────────────────┐
│                                                              │
│  359 Rules    33 VOR   8 Combat   22 Afterblow   81 LS      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Search Results
```
═════════════════════════════════════════════════════════════
Found 3 results

[🔗 LS-VOR-1.1.1] [Score: 40.0]    ← Clickable! Opens full rulebook
                                       and jumps to this rule
[longsword] [VOR]
---
**Minden szabályosan végrehajtott támadást** védeni kell...

Document: 05.a-hosszukard-VOR.md
Section: A találatok érvényessége vagy elsőbbsége
───────────────────────────────────────────────────────────

[🔗 LS-VOR-1.1.2] [Score: 40.0]    ← Clickable! Opens full rulebook
[longsword] [VOR]
---
A támadások helyességének elbírálásakor a következőket...

Document: 05.a-hosszukard-VOR.md
Section: A találatok érvényessége vagy elsőbbsége
───────────────────────────────────────────────────────────

[🔗 LS-VOR-1.1.3] [Score: 40.0]    ← Clickable! Opens full rulebook
[longsword] [VOR]
---
Az egyszerű támadás, akár közvetlen, akár közvetett...

Document: 05.a-hosszukard-VOR.md
Section: A találatok érvényessége vagy elsőbbsége
═════════════════════════════════════════════════════════════
```

## Sample Searches

### "right of way target"
Finds: 5 VOR rules about valid targets
Uses aliases: "right of way" → VOR format

### "longsword strike"
Finds: 3 longsword rules about strikes
Applies to: General + weapon-general + all formats

### Search with Filter: "target" (Format: VOR)
Finds: Rules about targets in VOR format
Hierarchy: General rules + VOR-specific rules

### "free fencing penalty"
Finds: COMBAT format rules about penalties
Uses aliases: "free fencing" → COMBAT format

## Mobile Experience

```
┌─────────────────────┐
│ ⚔️ HEMA Search      │
├─────────────────────┤
│ [Search box.......] │
│ [Format ▼]          │
│ [Weapon ▼]          │
│ [Search]            │
├─────────────────────┤
│ 359 | 33 | 8 | 22   │
├─────────────────────┤
│ Rule: LS-1.1.1      │
│ Score: 40          │
│ longsword | VOR     │
│                     │
│ Rule text here...   │
│                     │
│ Doc: 05-hossz...    │
├─────────────────────┤
│ More results...     │
└─────────────────────┘
```

## Real Search Examples Your Fencers Will Try

### A Referee
- Query: "attacking without control"
- Expected: Find rules about control requirements
- Result: Gets 5 relevant rules with scores

### A Fencer Learning Rules
- Query: "where can I hit with longsword"
- Expected: Valid target areas
- Result: Gets general rules + longsword-specific rules

### Tournament Organizer
- Query: "right of way"
- Filter: Format = VOR
- Expected: All VOR-specific rules
- Result: 33 VOR rules ranked by relevance

### New Judge
- Query: "penalty illegal move"
- Expected: Penalty rules for illegal actions
- Result: 10+ rules with clear explanations

## What Makes It Work

✅ **Seamless Navigation**
- Rule IDs in search results are clickable links
- Click → Opens full rulebook at the referenced rule
- "Vissza / Back" button → Returns to previous scroll position
- Works across search-to-rulebook workflow

✅ **Smart Aliasing**
- "right of way" = VOR
- "free fencing" = COMBAT  
- "sword" = longsword
- "finding" = valid target

✅ **Hierarchy**
- General rules apply everywhere
- Weapon-general rules apply to all formats of that weapon
- Format-specific rules for VOR/COMBAT/AFTERBLOW

✅ **Fast Search**
- 359 rules searched instantly
- Relevance ranking by 8 scoring factors
- Results in <100ms

✅ **Mobile First**
- Works on phones, tablets, desktops
- Responsive design
- Touch-friendly buttons

✅ **Zero Learning Curve**
- Type what you're looking for
- Optional filters if needed
- Results in natural language

## Accessibility

✅ No login required
✅ No installation needed
✅ Works on any device with browser
✅ Accessible to all club members
✅ Can be shared via simple URL
✅ Works on slow internet

## Real Use Cases

### During Training
Fencer: "Can I attack to the back of the head?"
Coach: "Let me search..."
System: Shows LS-2.3.1 about valid target areas

### During Competition
Judge: "Was that a valid attack?"
Organizer: Searches "priority control"
System: Shows relevant VOR rules instantly

### For Learning
Beginner: "What are the basic rules?"
Friend: "Here's the search link"
Beginner: Explores rules at own pace

### For Rule Updates
Admin: Edits rulebook markdown
Admin: Pushes to GitHub
Result: Website auto-updates in 2 minutes

---

That's what your fencers get! Simple, fast, accessible. ⚔️
