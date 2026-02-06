# Deploy to Render.com - Step by Step

## Prerequisites
- GitHub account (already have one)
- Render.com account (free)
- This repository pushed to GitHub

## Steps

### 1. Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Sign up"
3. Use GitHub account to sign up (easiest option)
4. Authorize Render to access your GitHub repositories

### 2. Connect Your Repository
1. In Render dashboard, click "New +" button
2. Select "Web Service"
3. Under "GitHub" section, click "Connect GitHub"
4. Select your HEMA-rulebook-hun repository
5. Click "Connect"

### 3. Configure the Service
The form will appear with these settings:

| Setting | Value |
|---------|-------|
| **Name** | `hema-rulebook-search` |
| **Runtime** | Python 3.11 |
| **Build Command** | (leave empty, Render auto-detects) |
| **Start Command** | `python app.py` |
| **Region** | Choose closest to your location |
| **Plan** | Free |

### 4. Deploy
1. Click "Create Web Service"
2. Render will start building
3. Wait for the build to complete (2-3 minutes)
4. You'll see a green checkmark when done
5. Your site URL: `https://hema-rulebook-search.onrender.com`

### 5. Test It Works
1. Visit your URL
2. Try searching: "longsword", "right of way", "target"
3. Test the filters

## What Happens Automatically

✅ Render detects `render.yaml` configuration  
✅ Installs Python 3.11  
✅ Installs dependencies from `requirements.txt`  
✅ Runs `python app.py`  
✅ Serves the app on a public URL  
✅ Auto-redeploys when you push to GitHub  

## Updating Your Rulebook

To update rules and re-deploy:

1. **Update markdown files** (e.g., `05-hosszukard.md`)
2. **Re-index locally** (optional):
   ```bash
   cd qa-tools
   python parser.py
   python add_aliases.py
   ```
3. **Commit and push to GitHub**:
   ```bash
   git add .
   git commit -m "Update rulebook"
   git push
   ```
4. **Render auto-deploys** your changes (usually within 2 minutes)

## Troubleshooting

### Build Failed
- Check Render logs for error messages
- Ensure `render.yaml` is valid YAML
- Verify all files exist in repository

### App not responding
- Check if instance is running (green status in Render)
- Render free tier may sleep - refresh page
- Check logs for Python errors

### Search not working
- Verify `rules_index.json` exists in `qa-tools/`
- Check `aliases.json` is present
- Run `python setup_check.py` locally to test

## Render Free Tier Limits

| Feature | Limit |
|---------|-------|
| Concurrent Users | ~10-20 before slowdown |
| Requests/month | Unlimited |
| Uptime SLA | None (best effort) |
| Sleep timeout | 15 min inactive → 30s cold start |
| Disk space | 1 GB |
| RAM | 512 MB |

**Tip**: For production with 100+ daily users, upgrade to Starter Plan ($7/month)

## Custom Domain (Optional)

1. In Render dashboard → Settings
2. Add custom domain (e.g., `hema-search.yoursite.com`)
3. Update DNS records with values Render provides
4. Takes 5-30 minutes to activate

## Next Steps

- 📱 Share the URL with your fencing club
- 📖 Update aliases in `qa-tools/aliases.json` for better searches
- 🎨 Customize colors in `templates/index.html`
- 🌐 Add custom domain for a more professional appearance
- 💾 Consider paid plan if getting heavy usage

## Questions?

- Check Render logs: Dashboard → Web Service → Logs
- Test locally: `python app.py` then visit `http://localhost:5000`
- Read DEPLOYMENT.md for more details

---

Good luck! Your HEMA rulebook is about to be accessible to everyone. ⚔️
