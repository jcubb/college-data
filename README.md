collegestats.py

This repository reads selected tables from a NCES IPEDS Access database.
Generally recommend using latest data found here, which will likely be a "Provisional" release:
https://nces.ed.gov/ipeds/use-the-data/download-access-database

How the script finds the Access DB
- Command-line argument: pass --db or -d with the path to the ROOT directory where the file folder is
- Environment variable: set IPEDS_DB to the path to the ROOT directory
- Repo-relative locations: the script will look for common candidate paths such as ./IPEDS_{START}-{END}_Provisional/IPEDS{START}{END}.accdb
	(where {START} is the 4-digit start year and {END} is the last two digits of start_year+1, e.g. start=2023 -> folder `IPEDS_2023-24_Provisional` and file `IPEDS202324.accdb`)

Do NOT commit the Access DB
The Access file is a local data artifact and should not be checked into git. This repo includes a .gitignore which excludes *.accdb and *.laccdb files, and a .env.example you can copy to .env for local configuration.

Quick PowerShell examples (Windows PowerShell v5.x)
# Run once for the current PowerShell session
$env:IPEDS_DB = 'C:\path\to'
python collegestats.py

# Make it persistent for the user (uses setx, requires reopening shells)
setx IPEDS_DB 'C:\path\to'

# Or run with an explicit path
python collegestats.py --db 'C:\path\to'

If you need to track the binary DB in git, consider using Git LFS (Large File Storage) instead of checking the raw .accdb into the repo.

Optional: use a .env file
- Copy .env.example to .env and fill in the real path
- The script already reads IPEDS_DB from the environment; if you want automatic loading of .env files, consider adding the python-dotenv package and loading it at runtime (small change)

Notes
- The script will raise FileNotFoundError with instructions if it cannot find the DB via any of the lookup methods.


