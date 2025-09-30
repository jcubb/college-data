# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 18:41:54 2022

Read in key elements from the NCES IPEDS 2023-24 Provisional data.
NCES = National Center for Education Statistics 
IPEDS = Integrated Postsecondary Education Data System

sample command line call:
$env:DB = 'C:\\Users\\gcubb\\OneDrive\\Python\\data-hub\\IPEDS_2023-24_Provisional\\IPEDS202324.accdb'
$env:IDS = 'C:\\Users\\gcubb\\OneDrive\\Python\\college-data\\select_college_IDs.xlsx'
python collegestats.py --year 2023 --db $env:DB --ids $env:IDS

~for time series data on these statistics, see collegestats_ts.py

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


def make_ipeds_names(start_year):
    """Return (folder_name, file_name) for a given start_year (e.g., "2023").

    Example:
    - start_year='2023' -> ('IPEDS_2023-24_Provisional', 'IPEDS202324.accdb')
    """
    try:
        end_year = int(start_year) + 1
    except Exception:
        end_year = int(str(start_year)[-2:]) + 1
    end_short = str(end_year)[-2:]
    folder_name = f'IPEDS_{start_year}-{end_short}_Provisional'
    file_name = f'IPEDS{start_year}{end_short}.accdb'
    return folder_name, file_name


def _resolve_db_path(start_year, cli_db=None):
    """Resolve the path to the IPEDS .accdb file for a given start_year.

    Resolution order:
    1. Command-line argument --db / -d
    2. Environment variable IPEDS_DB
    3. A few repo-relative candidate locations (useful when the DB lives next to the repo)
    If none found, raise FileNotFoundError with actionable instructions.

    start_year: full year string like '2023'. This will be used to construct
    folder and filename like 'IPEDS_2023-24_Provisional/IPEDS202324.accdb'.
    """
    # 1) CLI argument passed in programmatically
    if cli_db:
        p = Path(cli_db).expanduser()
        if p.exists():
            return str(p)

    # 2) environment variable
    env_path = os.environ.get('IPEDS_DB')
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists():
            return str(p)

    # 3) repo-relative candidates (build folder/filename from start_year)
    repo_root = Path(__file__).resolve().parent
    folder_name, file_name = make_ipeds_names(start_year)
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
    parser.add_argument('--db', '-d', help='Path to IPEDS .accdb file', default='C:\\Users\\gcubb\\OneDrive\\Python\\data-hub\\IPEDS_2023-24_Provisional\\IPEDS202324.accdb')
    parser.add_argument('--ids', help='Path to college_IDs_backup.xlsx', default='C:\\Users\\gcubb\\OneDrive\\Python\\college-data\\select_college_IDs.xlsx')
    parser.add_argument('--year', '-y', help='Start year (e.g. 2023)', default='2023')
    args = parser.parse_args(argv)

    year = args.year
    db_path = _resolve_db_path(year, cli_db=args.db)
    conn = pyodbc.connect(fr'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};')
    cursor = conn.cursor()

    # construct table names dynamically from the chosen start year
    year_short = year[-2:]
    adm_table = f'ADM{year}'
    drvadm_table = f'DRVADM{year}'
    hd_table = f'HD{year}'
    valuesets_table = f'Valuesets{year_short}'
    admvar_table = f'vartable{year_short}' #varName, varTitle

    # pull all fields from 3 key tables
    res = cursor.execute(f'select * from {adm_table}')
    columnList = [tuple[0] for tuple in res.description]
    dd = cursor.fetchall()
    adm = (
        pd.DataFrame((tuple(t) for t in dd), columns = columnList)
        .set_index('UNITID')
    )
    res = cursor.execute(f'select * from {drvadm_table}')
    columnList = [tuple[0] for tuple in res.description]
    dd = cursor.fetchall()
    drvadm = (
        pd.DataFrame((tuple(t) for t in dd), columns=columnList)
        .set_index('UNITID')
        .rename(columns={
            'DVADM01':'percAdm'
            ,'DVADM02':'percAdmMen'
            ,'DVADM03':'percAdmWom'
            }
        )
    )
    res = cursor.execute(f'select * from {hd_table}')
    columnList = [tuple[0] for tuple in res.description]
    dd = cursor.fetchall()
    desc = (
        pd.DataFrame((tuple(t) for t in dd), columns = columnList)
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
    dall = (
        pd.merge(adm,drvadm[['percAdm','percAdmMen','percAdmWom']],left_index=True,right_index=True)
        .merge(desc[descflds],left_index=True,right_index=True)
    )

    # Read in a set of college IDs of interest and filter to those
    ids_path = _resolve_ids_path(cli_ids=args.ids)
    dsub = (
        pd.read_excel(ids_path, sheet_name='list')
        .iloc[:,0]
        .dropna()
        .reset_index()
        .rename(columns={'ncesid':'UNITID'})
        .set_index('UNITID')
        .merge(dall,left_index=True,right_index=True)
        .drop(['index'],axis=1)
        .sort_index()
    )

    # map code-valued fields to their labels in-place
    res = cursor.execute(f'select * from {valuesets_table}')
    columnList = [tuple[0] for tuple in res.description]
    dd = cursor.fetchall()
    vsets = pd.DataFrame((tuple(t) for t in dd), columns = columnList)
    value_desc_map = vsets[['varName','Codevalue','valueLabel']].copy()
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
        dsub_names[fld] = result # overwrite the original

    # change dsub column names using adm_col_descname
    res = cursor.execute(f'select * from {admvar_table}')
    columnList = [tuple[0] for tuple in res.description]
    dd = cursor.fetchall()
    vsets = pd.DataFrame((tuple(t) for t in dd), columns = columnList)
    adm_col_descname = (
        vsets[vsets['varName'].astype(str).str.startswith('ADMC', na=False)]
        [['varName', 'varTitle']]
        .set_index('varName')
    )
    dsub_names.rename(columns=adm_col_descname['varTitle'].to_dict(), inplace=True)
    dsub_names.to_csv('raw.csv')

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
    