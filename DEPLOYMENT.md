# HEMA Rulebook Web Search

A Flask web application for searching the Hungarian Historical European Martial Arts (HEMA) rulebook. This allows fencers and judges to quickly find relevant rules using natural language queries.

## Features

- 🔍 **Smart Search**: Search across 359+ rules with intelligent ranking
- 🏷️ **Aliasing**: Find rules using alternative names (e.g., "right of way" → VOR)
- 🎯 **Filtering**: Filter by competition variant (VOR, COMBAT, AFTERBLOW) or weapon
- 📱 **Mobile Responsive**: Works great on phones and tablets
- ⚡ **Fast**: Real-time search results
- 🌍 **Accessible**: Deployed publicly for all fencers

## Quick Start - Render Deployment

### 1. Connect Your GitHub Repository
- Go to [render.com](https://render.com)
- Sign up or log in
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Select the branch (usually `main`)

### 2. Configure the Service
- **Name**: `hema-rulebook-search`
- **Runtime**: Python 3.11+
- **Build / Start Command**: leave blank if using `render.yaml`
- **Region**: Choose closest to your users

### 3. Deploy
- Click "Create Web Service"
- Render will automatically detect `render.yaml`, run tests, rebuild `dist/rulebook.html`, and start Gunicorn
- Your site will be live at `https://hema-rulebook-hun.onrender.com`

## Local Development

### Requirements
- Python 3.11+
- Flask 3.0+

### Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd HEMA-rulebook-hun

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt

# Run the app
python app.py
```

Visit `http://localhost:5000` in your browser.

## Project Structure

```
HEMA-rulebook-hun/
├── app.py                 # Flask application
├── templates/
│   └── index.html        # Web interface
├── qa-tools/
│   ├── parser.py         # Rule parser
│   ├── search_aliases.py # Smart search engine
│   ├── rules_index.json  # 359+ indexed rules
│   └── aliases.json      # Search aliases
├── requirements.txt      # Python dependencies
├── render.yaml          # Render.com config
├── Procfile             # Optional generic process file
└── README.md           # This file
```

## How It Works

### Rule Indexing (Backend)
1. **Parser** (`parser.py`) extracts rules from markdown files
2. Rules are identified by format: `**PREFIX-NUMBER.NUMBER.NUMBER**`
3. Metadata captured: weapon type, variant (VOR/COMBAT/AFTERBLOW), section, etc.
4. All rules indexed in JSON for fast lookup

### Smart Search
1. **Keyword Matching**: Find rules containing search terms
2. **Alias Expansion**: Convert "right of way" → "VOR", etc.
3. **Relevance Ranking**: Score results by:
   - Rule ID match (+100)
   - Exact phrase match (+50)
   - Format alias match (+40)
   - Term frequency (+10 per occurrence)
4. **Hierarchy Support**: General rules apply to all weapons/variants

### Web Interface (Frontend)
- Clean, responsive design
- Real-time search with filters
- Statistics dashboard
- Mobile-friendly

## API Endpoints

### GET `/`
Returns the web interface (HTML)

### POST `/api/search`
Search for rules
```json
{
  "query": "right of way target",
  "max_results": 10,
  "variant_filter": "VOR",
  "weapon_filter": "longsword"
}
```

### GET `/api/stats`
Get rulebook statistics (total rules, by variant, etc.)

### GET `/api/rule/<rule_id>`
Get a specific rule by ID (e.g., `LS-VOR-1.1.1`)

## Search Tips

- **Format aliases**: "right of way", "priority", "row" → VOR rules
- **Weapon aliases**: "sword", "long sword", "ls" → Longsword rules
- **Natural language**: "Can I strike the knee?" will find relevant rules
- **Specific rules**: Use rule ID directly: "LS-VOR-1.1.1"

## Customization

### Add New Aliases
Edit `qa-tools/aliases.json`:
```json
{
  "variants": {
    "VOR": ["right of way", "row", "priority", ...]
  },
  "weapons": {
    "longsword": ["sword", "ls", ...]
  }
}
```

Then re-run:
```bash
cd qa-tools
python parser.py        # Re-index rules
python add_aliases.py   # Add aliases to index
```

### Update Rules
1. Edit markdown files in root directory
2. Run parser to update index:
```bash
cd qa-tools
python parser.py
python add_aliases.py
```
3. Commit and push to GitHub - Render will auto-deploy

## Troubleshooting

### Render Deploy Fails
- Check `render.yaml` syntax
- Ensure Python 3.11+ is specified
- Check GitHub is connected and accessible
- View Render logs for details

### Search Not Working
- Verify `rules_index.json` exists and is valid JSON
- Check `aliases.json` is in `qa-tools/`
- Restart the app: `python app.py`

### Slow Search
- Normal: First search takes ~1 second
- Subsequent searches should be instant
- Render free tier may have startup delays

## Performance

- **Index size**: ~500KB JSON
- **Search time**: <100ms typical
- **Memory usage**: ~50MB
- **Concurrent users**: Render free tier supports dozens

## Limitations (Free Tier)

- Renders to sleep after 15 minutes of inactivity (cold start ~30s)
- Limited to 1 GB RAM
- No custom domain (included: `*.onrender.com`)

## Scaling Up

For production use, consider:
- Paid Render plan (no sleep, custom domain)
- Caching layer (Redis)
- Database (PostgreSQL) for translations
- CDN for static assets

## Future Features

- 🌐 Multi-language translations (English, German, French)
- 📚 Cross-references between rules
- 📊 Statistics and analytics
- 💾 Favorite rules/bookmarks
- 🔔 Rules notifications
- 📖 Offline support (PWA)

## Contributing

To improve the rulebook search:
1. Update markdown files with better structured rules
2. Add more aliases in `qa-tools/aliases.json`
3. Improve parser logic in `qa-tools/parser.py`
4. Enhance UI in `templates/index.html`

## License

Same license as the rulebook source files

## Support

- Report issues on GitHub
- Ask questions in HEMA community
- Contribute improvements via pull requests

---

**Made for fencers, by fencers** ⚔️
