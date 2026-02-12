# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 18:41:54 2022

Read in key elements from the NCES IPEDS data.
NCES = National Center for Education Statistics 
IPEDS = Integrated Postsecondary Education Data System
https://nces.ed.gov/ipeds/use-the-data/download-access-database

Supports both single-year and multi-year (time series) data extraction.
- Single year: outputs raw.csv for current year
- Multi-year: outputs raw.csv (current year) + raw_timeseries.csv (all years with 'year' column)

sample command line calls:
$env:DB = 'C:\\Users\\gcubb\\OneDrive\\Python\\data-hub'
$env:IDS = 'C:\\Users\\gcubb\\OneDrive\\Python\\college-data\\select_college_IDs.xlsx'

# Single year (current/provisional):
python collegestats.py --year 2023 --db $env:DB --ids $env:IDS --folder-tag "Provisional"

# Multi-year time series (2014-2023, with 2023 as provisional):
python collegestats.py --year 2023 --db $env:DB --ids $env:IDS --folder-tag "Provisional" --start-year 2014

~If want to add more schools to select_college_IDs.xlsx, go into one of the access DBs and look at the HDyyyy table.

@author: gcubb
"""
import pyodbc
import pandas as pd
import os
import argparse
from pathlib import Path
# try to load a local .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def make_ipeds_names(start_year, folder_tag='Provisional'):
    """Return (folder_name, file_name) for a given start_year (e.g., "2023").

    Example:
    - start_year='2023', folder_tag='Final' -> ('IPEDS_2023-24_Final', 'IPEDS202324.accdb')
    """
    try:
        end_year = int(start_year) + 1
    except Exception:
        end_year = int(str(start_year)[-2:]) + 1
    end_short = str(end_year)[-2:]
    folder_name = f'IPEDS_{start_year}-{end_short}_{folder_tag}'
    file_name = f'IPEDS{start_year}{end_short}.accdb'
    return folder_name, file_name


def _resolve_db_path(start_year, folder_tag, cli_db_root=None):
    """Resolve the path to the IPEDS .accdb file for a given start_year.

    Resolution order:
    1. Command-line argument --db / -d
    2. Environment variable IPEDS_DB
    3. A few repo-relative candidate locations (useful when the DB lives next to the repo)
    If none found, raise FileNotFoundError with actionable instructions.

    start_year: full year string like '2023'. This will be used to construct
    folder and filename like 'IPEDS_2023-24_Provisional/IPEDS202324.accdb'.
    """
    folder_name, file_name = make_ipeds_names(start_year, folder_tag)
    # 1) CLI argument passed in programmatically
    if cli_db_root:
        cli_db = os.path.join(cli_db_root, folder_name, file_name)
        p = Path(cli_db).expanduser()
        if p.exists():
            return str(p)

    # 2) environment variable
    env_path_root = os.environ.get('IPEDS_DB')
    if env_path_root:
        env_path = os.path.join(env_path_root, folder_name, file_name)
        p = Path(env_path).expanduser()
        if p.exists():
            return str(p)

    # 3) repo-relative candidates (build folder/filename from start_year)
    repo_root = Path(__file__).resolve().parent
    candidates = [
        repo_root / folder_name / file_name,
        repo_root / '..' / folder_name / file_name,
        repo_root / 'data' / file_name,
    ]
    for c in candidates:
        if c.exists():
            return str(c)

    # not found
    raise FileNotFoundError(
        f"Could not find {file_name}. Provide the path with --db, set the IPEDS_DB environment variable, "
        f"or place the file at ./{folder_name}/{file_name} relative to this script."
    )


def _resolve_ids_path(cli_ids=None):
    """Resolve path to the select_college_IDs.xlsx file.

    Resolution order:
    1. CLI argument passed in (cli_ids)
    2. Environment variable COLLEGE_IDS
    3. Repo-relative candidates: ./select_college_IDs.xlsx, ../select_college_IDs.xlsx, ./data/select_college_IDs.xlsx
    """
    # 1) CLI argument
    if cli_ids:
        p = Path(cli_ids).expanduser()
        if p.exists():
            return str(p)

    # 2) environment variable
    env_path = os.environ.get('COLLEGE_IDS')
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists():
            return str(p)

    # 3) repo-relative
    repo_root = Path(__file__).resolve().parent
    candidates = [
        repo_root / 'select_college_IDs.xlsx',
        repo_root / '..' / 'select_college_IDs.xlsx',
        repo_root / 'data' / 'select_college_IDs.xlsx',
    ]
    for c in candidates:
        if c.exists():
            return str(c)

    raise FileNotFoundError(
        'Could not find select_college_IDs.xlsx. Provide the path with --ids, set the COLLEGE_IDS environment variable, '
        'or place the file at ./select_college_IDs.xlsx relative to this script.'
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read IPEDS Access DB and extract tables')
    parser.add_argument('--db', '-d', help='Path to IPEDS .accdb file', default='C:\\Users\\gcubb\\OneDrive\\Python\\data-hub')
    parser.add_argument('--ids', help='Path to college_IDs_backup.xlsx', default='C:\\Users\\gcubb\\OneDrive\\Python\\college-data\\select_college_IDs.xlsx')
    parser.add_argument('--year', '-y', help='Current/end year (e.g. 2023)', default='2023')
    parser.add_argument('--folder-tag', help='Folder tag for current year (e.g. Provisional, Final)', default='Provisional')
    parser.add_argument('--start-year', help='Start year for time series (e.g. 2014). If omitted, only current year is processed.', default=None)
    args = parser.parse_args(argv)
    
    current_year = int(args.year)
    current_folder_tag = args.folder_tag
    db_root = args.db
    ids_path = _resolve_ids_path(cli_ids=args.ids)
    
    # Determine which years to process
    if args.start_year:
        start_year = int(args.start_year)
        years_to_process = list(range(start_year, current_year + 1))
    else:
        years_to_process = [current_year]
    
    all_years_data = []
    
    for year in years_to_process:
        # For current year, use the provided folder_tag (Provisional or Final)
        # For all previous years, use Final
        if year == current_year:
            folder_tag = current_folder_tag
        else:
            folder_tag = 'Final'
        
        print(f"Processing year {year} ({folder_tag})...")
        
        year_str = str(year)
        db_path = _resolve_db_path(year_str, folder_tag, cli_db_root=db_root)
        conn = pyodbc.connect(fr'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};')
        cursor = conn.cursor()

        # construct table names dynamically from the chosen start year
        year_short = year_str[-2:]
        adm_table = f'ADM{year_str}'
        drvadm_table = f'DRVADM{year_str}'
        hd_table = f'HD{year_str}'
        valuesets_table = f'Valuesets{year_short}'
        admvar_table = f'vartable{year_short}'  # varName, varTitle

        # pull all fields from 3 key tables
        res = cursor.execute(f'select * from {adm_table}')
        columnList = [tuple[0] for tuple in res.description]
        dd = cursor.fetchall()
        adm = (
            pd.DataFrame((tuple(t) for t in dd), columns=columnList)
            .set_index('UNITID')
        )
        res = cursor.execute(f'select * from {drvadm_table}')
        columnList = [tuple[0] for tuple in res.description]
        dd = cursor.fetchall()
        drvadm = (
            pd.DataFrame((tuple(t) for t in dd), columns=columnList)
            .set_index('UNITID')
            .rename(columns={
                'DVADM01': 'percAdm',
                'DVADM02': 'percAdmMen',
                'DVADM03': 'percAdmWom',
            })
        )
        res = cursor.execute(f'select * from {hd_table}')
        columnList = [tuple[0] for tuple in res.description]
        dd = cursor.fetchall()
        desc = (
            pd.DataFrame((tuple(t) for t in dd), columns=columnList)
            .set_index('UNITID')
        )

        # Choose subset of fields of interest and merge 3 key tables
        descflds = [
            'INSTNM',
            'LOCALE',
            'ADDR',
            'CITY',
            'STABBR',
            'ZIP',
            'GROFFER',
            'HDEGOFR1',
            'CARNEGIE',
            'CCBASIC',
            'C15BASIC',
            'C18BASIC',
            'C21IPUG',
            'C21IPGRD',
            'C21UGPRF',
            'C21ENPRF',
            'C21SZSET',
            'C21BASIC',
            'INSTSIZE',
        ]
        # Filter to only fields that exist in this year's data (e.g., C21* fields only exist from 2021+)
        descflds_available = [f for f in descflds if f in desc.columns]
        dall = (
            pd.merge(adm, drvadm[['percAdm', 'percAdmMen', 'percAdmWom']], left_index=True, right_index=True)
            .merge(desc[descflds_available], left_index=True, right_index=True)
        )

        # Read in a set of college IDs of interest and filter to those
        dsub = (
            pd.read_excel(ids_path, sheet_name='list')
            .iloc[:, 0]
            .dropna()
            .reset_index()
            .rename(columns={'ncesid': 'UNITID'})
            .set_index('UNITID')
            .merge(dall, left_index=True, right_index=True)
            .drop(['index'], axis=1)
            .sort_index()
        )

        # map code-valued fields to their labels in-place
        res = cursor.execute(f'select * from {valuesets_table}')
        columnList = [tuple[0] for tuple in res.description]
        dd = cursor.fetchall()
        vsets = pd.DataFrame((tuple(t) for t in dd), columns=columnList)
        value_desc_map = vsets[['varName', 'Codevalue', 'valueLabel']].copy()
        replcodeflds = [
            'LOCALE',
            'GROFFER',
            'HDEGOFR1',
            'CARNEGIE',
            'CCBASIC',
            'C15BASIC',
            'C18BASIC',
            'C21IPUG',
            'C21IPGRD',
            'C21UGPRF',
            'C21ENPRF',
            'C21SZSET',
            'C21BASIC',
            'INSTSIZE',
            'ADMCON1',
            'ADMCON2',
            'ADMCON3',
            'ADMCON4',
            'ADMCON5',
            'ADMCON6',
            'ADMCON7',
            'ADMCON8',
            'ADMCON9',
            'ADMCON10',
            'ADMCON11',
            'ADMCON12',
        ]
        dsub_names = dsub.copy()
        for fld in replcodeflds:
            if fld not in dsub_names.columns:
                continue
            # build string-keyed mapping
            vseries = value_desc_map[value_desc_map.varName == fld].set_index('Codevalue')['valueLabel']
            str_map = vseries.to_dict()
            # build numeric-keyed mapping where possible
            num_map = {}
            for k, v in str_map.items():
                try:
                    # try integer first
                    ik = int(k)
                    num_map[ik] = v
                except Exception:
                    try:
                        fk = float(k)
                        num_map[fk] = v
                    except Exception:
                        # leave non-numeric keys only in str_map
                        pass
            orig = dsub_names[fld]
            # attempt numeric mapping (works when orig is numeric dtype), else string mapping
            mapped_num = orig.map(num_map) if num_map else pd.Series(index=orig.index)
            mapped_str = orig.astype(str).map(str_map)
            result = mapped_num.where(mapped_num.notna(), mapped_str)
            result = result.where(result.notna(), orig)
            dsub_names[fld] = result  # overwrite the original

        # change dsub column names using adm_col_descname
        res = cursor.execute(f'select * from {admvar_table}')
        columnList = [tuple[0] for tuple in res.description]
        dd = cursor.fetchall()
        vsets = pd.DataFrame((tuple(t) for t in dd), columns=columnList)
        adm_col_descname = (
            vsets[vsets['varName'].astype(str).str.startswith('ADMC', na=False)]
            [['varName', 'varTitle']]
            .set_index('varName')
        )
        dsub_names.rename(columns=adm_col_descname['varTitle'].to_dict(), inplace=True)
        
        # Add year column for time series tracking
        dsub_names['year'] = year
        
        # Store this year's data
        all_years_data.append(dsub_names.reset_index())

        cursor.close()
        conn.close()
    
    # Concatenate all years' data
    combined_df = pd.concat(all_years_data, ignore_index=True)
    
    # Output raw.csv for current year only (without year column for backward compatibility)
    current_year_df = combined_df[combined_df['year'] == current_year].drop(columns=['year']).set_index('UNITID')
    current_year_df.to_csv('raw.csv')
    print(f"Saved current year ({current_year}) data to raw.csv")
    
    # If multiple years, output time series CSV with year column
    if len(years_to_process) > 1:
        # Fill in college name field with most recent name (some have changed over time)
        idyrmax = combined_df.groupby('UNITID')['year'].max().rename('maxyr')
        combined_df = pd.merge(combined_df, idyrmax, how='inner', left_on='UNITID', right_index=True)
        currnm = combined_df[combined_df['year'] == combined_df['maxyr']][['UNITID', 'INSTNM']].drop_duplicates().set_index('UNITID')
        combined_df = combined_df.drop(columns=['INSTNM'])
        combined_df = pd.merge(combined_df, currnm, how='inner', left_on='UNITID', right_index=True)
        combined_df = combined_df.drop(columns=['maxyr'])
        
        # Reorder columns to put year and INSTNM first
        cols = combined_df.columns.tolist()
        cols.remove('year')
        cols.remove('UNITID')
        cols.remove('INSTNM')
        combined_df = combined_df[['UNITID', 'year', 'INSTNM'] + cols]
        combined_df = combined_df.sort_values(['UNITID', 'year'])
        
        # Generate filename from year range: ipeds_{end_year}_{start_year}.csv
        ts_filename = f'ipeds_{max(years_to_process)}_{min(years_to_process)}.csv'
        combined_df.to_csv(ts_filename, index=False)
        print(f"Saved time series data ({min(years_to_process)}-{max(years_to_process)}) to {ts_filename}")


if __name__ == '__main__':
    main()