# Consulting Experienced Hire Job Tracker

A tool that scrapes experienced hire job listings from major consulting firms and displays them on a static dashboard hosted via GitHub Pages.

**Live dashboard:** [baxterharrisbrown.github.io/consulting-experienced-hire](https://baxterharrisbrown.github.io/consulting-experienced-hire)

## Firms Tracked

| Firm | ATS |
|---|---|
| McKinsey & Company | Workday |
| Bain & Company | Workday |
| BCG | Eightfold AI |
| Deloitte | Workday |
| EY (incl. EY-Parthenon) | Workday |
| PwC | Workday |
| KPMG | Workday |
| FTI Consulting | Workday |
| LEK Consulting | Greenhouse |
| Simon Kucher | Greenhouse |
| Altman Solon | Greenhouse |

## How It Works

1. A Python scraper fetches job listings from each firm's ATS API
2. Jobs are filtered by seniority keywords (Consultant, Manager, Director, etc.) and exclusion keywords (Intern, Campus, etc.)
3. Results are saved to `data/snapshot.json`
4. A GitHub Actions workflow runs the scraper twice daily and commits the updated snapshot
5. The static dashboard at `docs/index.html` reads the snapshot and renders it client-side

## Local Setup

```bash
git clone https://github.com/baxterharrisbrown/consulting-experienced-hire.git
cd consulting-experienced-hire
pip install -r requirements.txt
python main.py --dry-run
```

### CLI Options

| Flag | Description |
|---|---|
| `--dry-run` | Run scrape and diff without writing snapshot |
| `--firms "McKinsey & Company" "BCG"` | Scrape only specific firms |
| `--verbose` | Enable DEBUG logging |

## Adding a New Firm

1. Add an entry to `config/firms.yaml` under `firms:`
2. Set `ats` to `workday`, `greenhouse`, or `eightfold`
3. Provide the required fields for that ATS type:
   - **Workday:** `tenant`, `wd_server`, `site`
   - **Greenhouse:** `slug` (and optional `slug_alt`)
   - **Eightfold:** `base_url`, `domain`
4. Run `python main.py --firms "New Firm" --dry-run` to test

## Updating Keyword Filters

Edit the `filters` section in `config/firms.yaml`:
- `seniority_keywords` — job titles must contain at least one of these (Tier 1)
- `exclusion_keywords` — job titles containing any of these are excluded (Tier 2)

## Enabling GitHub Pages

1. Go to your repo **Settings > Pages**
2. Under **Source**, select **Deploy from a branch**
3. Set branch to `main` and folder to `/docs`
4. Click **Save**
5. The dashboard will be live at `https://baxterharrisbrown.github.io/consulting-experienced-hire`

## Phase 2 Roadmap

- Email notifications for new job postings
