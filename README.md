# College Data Tools

This repository contains tools for extracting and visualizing IPEDS college admissions data.

## Components

### 1. Data Extraction: `collegestats.py`

Reads selected tables from an NCES IPEDS Access database and outputs time-series CSV data.

**Features:**
- Extracts admissions, test scores, and enrollment data from IPEDS databases
- Supports multi-year time series with `--start-year` argument
- Handles missing fields gracefully (e.g., Carnegie 2021 classification fields for pre-2021 data)
- Outputs to `ipeds_{year}_{start_year}.csv`

**Usage:**
```powershell
# Set environment variables
$env:IPEDS_DB = 'C:\path\to\data-hub'
$env:COLLEGE_IDS = 'C:\path\to\select_college_IDs.xlsx'

# Run for single year
python collegestats.py --year 2023 --folder-tag "Provisional"

# Run for time series (2014-2023)
python collegestats.py --year 2023 --start-year 2014 --folder-tag "Provisional"
```

### 2. Web Dashboard: `college_app.py`

Interactive Dash web application for comparing colleges and building school lists.

**Features:**
- **Compare Schools Page** (`/`): Compare up to 4 schools with summary tables and trend charts
  - SAT/ACT score toggle with 25th-75th percentile ranges
  - Gender-based admission metrics (App M%, Adm+ M, App W%, Adm+ W)
  - Historical trends for admission rates, test submission rates, and scores
  
- **Build School Lists Page** (`/lists`): Create personalized Reach/Middle/Likely school lists
  - Profile management (save, load, delete)
  - Color-coded summary table by category
  - Persistent storage in `user_profiles.json`

**Usage:**
```bash
python college_app.py
```
Then open http://127.0.0.1:8050 in your browser. Network access available at http://<your-ip>:8050.

## Data Sources

**IPEDS Access Database:**
- Download from: https://nces.ed.gov/ipeds/use-the-data/download-access-database
- Generally recommend using latest "Provisional" release
- Do NOT commit the Access DB (excluded via .gitignore)

**How the script finds the Access DB:**
1. Command-line argument: `--db` or `-d` with path to ROOT directory
2. Environment variable: `IPEDS_DB`
3. Repo-relative locations: `./IPEDS_{START}-{END}_Provisional/IPEDS{START}{END}.accdb`

## Deployment

For cloud deployment (Render, Heroku, etc.):
- `Procfile`: Gunicorn configuration
- `runtime.txt`: Python version specification
- `requirements.txt`: Python dependencies

## Files

| File | Description |
|------|-------------|
| `collegestats.py` | IPEDS data extraction script |
| `college_app.py` | Dash web application |
| `ipeds_2023_2014.csv` | Time series data (2014-2023) |
| `user_profiles.json` | Saved user school lists |
| `requirements.txt` | Python dependencies |
| `Procfile` | Deployment configuration |
| `runtime.txt` | Python version for deployment |

## Requirements

See `requirements.txt` for dependencies. Key packages:
- `dash` - Web framework
- `plotly` - Charting
- `pandas` - Data manipulation
- `pyodbc` - Access database connectivity (Windows only, for data extraction)


