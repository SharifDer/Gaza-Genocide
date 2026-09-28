# 🚀 Gaza Genocide Documentation - Deployment Guide

## ✅ What This Project Is

A fully automated documentation system for the humanitarian crisis in Gaza:

- **Real data** from the [Tech for Palestine "Palestine Datasets" API](https://data.techforpalestine.org) (Gaza Ministry of Health daily reports, cross-referenced with UN OCHA)
- **Automated updates every day** via GitHub Actions
- **Live bilingual dashboard** (English + Arabic) at https://sharifder.github.io/Gaza-Genocide/ with interactive charts
- **Self-updating badges and statistics table** in the README
- **SEO/GEO ready** — static injected numbers, structured data, sitemap, `llms.txt`
- **Zero hosting costs** — runs entirely on GitHub

## 📋 Project Structure

```
Gaza-Genocide/
├── README.md                          # Main documentation with live badges
├── CONTRIBUTING.md                    # Contribution guidelines
├── PROJECT_STRUCTURE.md               # Technical documentation
├── DEPLOYMENT_GUIDE.md                # This guide
├── CITATION.cff                       # Citation metadata
├── requirements.txt                   # Python dependencies (requests only)
├── fetch_statistics.py                # Fetches real data from the TfP API
├── index.html / ar.html               # Generated dashboard pages (do not edit)
├── templates/                         # Dashboard templates (edit these)
├── robots.txt / sitemap.xml / llms.txt# SEO/GEO files
├── .nojekyll                          # Static GitHub Pages serving
├── .github/workflows/
│   └── update-stats.yml              # Automation daily
├── scripts/
│   └── update_badges.py              # Updates README + generates dashboard pages
└── data/
    ├── latest_stats.json             # Latest fetched statistics
    └── history.json                  # Full daily time series
```

## 🚀 Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Enable real-data statistics pipeline"
git push origin main
```

### 2. Enable GitHub Actions

1. Go to your GitHub repository
2. Navigate to the **Actions** tab
3. Enable workflows if prompted
4. The `Update Gaza Statistics` workflow runs every day automatically,
   or trigger it manually via **Actions → Update Gaza Statistics → Run workflow**

The workflow uses the default `GITHUB_TOKEN` with `contents: write`
permission — **no personal access token is required**.

### 3. Enable GitHub Pages (for the dashboard)

1. Go to **Settings → Pages**
2. Under **Build and deployment**, select **Deploy from a branch**
3. Choose branch **main**, folder **/ (root)**, click **Save**
4. Wait ~1 minute, then visit https://sharifder.github.io/Gaza-Genocide/

Optional but recommended for exposure:

- Set the repo **description** and **topics** (`gaza`, `palestine`,
  `gaza-casualties`, `humanitarian`, `data-visualization`, `github-pages`)
  via the ⚙️ icon on the repo's main page
- Submit the site to
  [Google Search Console](https://search.google.com/search-console) and
  upload `https://sharifder.github.io/Gaza-Genocide/sitemap.xml`

### 4. Verify It Works

- Check the **Actions** tab for a green run
- Look for a commit like `Update Gaza statistics - YYYY-MM-DD HH:MM UTC`
- Confirm the README badges and statistics table show fresh numbers
- Confirm the dashboard shows the same numbers as plain text
  (view-source of `index.html` — no `{{PLACEHOLDER}}` tokens)

## 🔧 How It Works

### Automation Flow

1. **Every day**, the GitHub Actions workflow triggers
2. `fetch_statistics.py` pulls the latest cumulative figures from
   `https://data.techforpalestine.org/api/v3/summary.json` and regenerates
   the full daily history (`data/history.json`)
3. The data is validated (sanity checks) and saved to `data/latest_stats.json`
4. `scripts/update_badges.py` rewrites the badges and live table in README.md
   and generates `index.html` / `ar.html` from `templates/`
5. Changes are committed and pushed automatically
6. GitHub Pages serves the updated dashboard

### Data Sources

| Figure | Source |
|--------|--------|
| Total deaths, children, women, injured | Gaza MoH daily reports via [TfP Datasets](https://data.techforpalestine.org) |
| Press / medical / civil defence killed | Gaza MoH daily reports via TfP Datasets |
| Massacres | Gaza MoH daily reports via TfP Datasets |
| Displaced, hospitals, food insecurity | Manually maintained from [UN OCHA flash updates](https://www.ochaopt.org/) |

### Failure Behavior

- **API unreachable** → the last good `data/latest_stats.json` is kept; the workflow does not push regressions
- **Unexpected API payload** → rejected by sanity checks; the last good data is kept
- **No changes** → no commit is created

## 🆘 Troubleshooting

### GitHub Actions not running

- Scheduled workflows only run on the **default branch**
- GitHub disables scheduled workflows after 60 days of repository inactivity;
  the regular commits from this workflow count as activity and keep it alive
- Check **Settings → Actions → General** that Actions are enabled

### Badges not updating

- Check the workflow logs for warnings from `update_badges.py`
  (`WARNING: badge ... not found` means the README badge markup was edited
  and no longer matches the expected format)
- Run locally to reproduce:
  ```bash
  pip install -r requirements.txt
  python fetch_statistics.py
  python scripts/update_badges.py
  ```

### Data looks stale

- The API itself is updated once daily by Tech for Palestine; the daily
  workflow picks up changes shortly after publication
- Check https://data.techforpalestine.org for the latest published report date
  (`last_update` field)

## 🌟 Maintenance

Very little is required:

- **Manual figures** (displaced, hospitals, food insecurity) live in
  `MANUAL_FIGURES` at the top of `fetch_statistics.py` — update them when
  UN OCHA publishes new figures
- **Dashboard changes**: edit `templates/index.html` / `templates/ar.html`
  (the root `index.html` / `ar.html` are generated — never edit them directly),
  then run `python scripts/update_badges.py` to regenerate
- Review the README narrative periodically; the badges and table update
  themselves, but prose does not

---

*"The world will not be destroyed by those who do evil, but by those who watch them without doing anything." - Albert Einstein*
