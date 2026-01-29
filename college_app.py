# -*- coding: utf-8 -*-
"""
College Data Comparison App
Compare statistics and trends across schools using IPEDS data.

Features:
- Page 1: Compare 4 schools with tables and charts
- Page 2: Build and save Reach/Middle/Likely school lists by user profile

To run locally:
    python college_app.py

Then open http://127.0.0.1:8050 in your browser.
"""

import pandas as pd
import numpy as np
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table, ctx
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json

# Database configuration - uses PostgreSQL if DATABASE_URL is set, otherwise local JSON
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import psycopg2
    from psycopg2.extras import Json


# City coordinates for schools in the dataset (lat, lon)
CITY_COORDS = {
    ('Berkeley', 'CA'): (37.8716, -122.2727), ('Davis', 'CA'): (38.5449, -121.7405),
    ('Irvine', 'CA'): (33.6846, -117.8265), ('Los Angeles', 'CA'): (34.0522, -118.2437),
    ('La Jolla', 'CA'): (32.8328, -117.2713), ('Santa Barbara', 'CA'): (34.4208, -119.6982),
    ('Claremont', 'CA'): (34.0967, -117.7198), ('Stanford', 'CA'): (37.4275, -122.1697),
    ('New London', 'CT'): (41.3557, -72.0995), ('Hartford', 'CT'): (41.7658, -72.6734),
    ('Middletown', 'CT'): (41.5623, -72.6506), ('New Haven', 'CT'): (41.3083, -72.9279),
    ('Washington', 'DC'): (38.9072, -77.0369), ('Coral Gables', 'FL'): (25.7215, -80.2684),
    ('Atlanta', 'GA'): (33.7490, -84.3880), ('Chicago', 'IL'): (41.8781, -87.6298),
    ('Champaign', 'IL'): (40.1164, -88.2434), ('Evanston', 'IL'): (42.0451, -87.6877),
    ('South Bend', 'IN'): (41.6764, -86.2520), ('Bloomington', 'IN'): (39.1653, -86.5264),
    ('Notre Dame', 'IN'): (41.7003, -86.2390), ('Grinnell', 'IA'): (41.7431, -92.7224),
    ('New Orleans', 'LA'): (29.9511, -90.0715), ('Lewiston', 'ME'): (44.1004, -70.2148),
    ('Brunswick', 'ME'): (43.9145, -69.9653), ('Waterville', 'ME'): (44.5520, -69.6317),
    ('Amherst', 'MA'): (42.3732, -72.5199), ('Chestnut Hill', 'MA'): (42.3188, -71.1637),
    ('Boston', 'MA'): (42.3601, -71.0589), ('Waltham', 'MA'): (42.3765, -71.2356),
    ('Worcester', 'MA'): (42.2626, -71.8023), ('Cambridge', 'MA'): (42.3736, -71.1097),
    ('Northampton', 'MA'): (42.3251, -72.6412), ('Medford', 'MA'): (42.4184, -71.1062),
    ('Wellesley', 'MA'): (42.2968, -71.2924), ('Williamstown', 'MA'): (42.7120, -73.2037),
    ('Ann Arbor', 'MI'): (42.2808, -83.7430), ('Northfield', 'MN'): (44.4583, -93.1616),
    ('Saint Paul', 'MN'): (44.9537, -93.0900), ('Minneapolis', 'MN'): (44.9778, -93.2650),
    ('Saint Louis', 'MO'): (38.6270, -90.1994), ('Hanover', 'NH'): (43.7022, -72.2896),
    ('Princeton', 'NJ'): (40.3573, -74.6672), ('Annandale-On-Hudson', 'NY'): (42.0229, -73.9096),
    ('New York', 'NY'): (40.7128, -74.0060), ('Hamilton', 'NY'): (42.8270, -75.5446),
    ('Ithaca', 'NY'): (42.4440, -76.5019), ('Clinton', 'NY'): (43.0484, -75.3785),
    ('Troy', 'NY'): (42.7284, -73.6918), ('Rochester', 'NY'): (43.1566, -77.6088),
    ('Bronxville', 'NY'): (40.9401, -73.8318), ('Saratoga Springs', 'NY'): (43.0831, -73.7846),
    ('Albany', 'NY'): (42.6526, -73.7562), ('Vestal', 'NY'): (42.0848, -76.0540),
    ('Syracuse', 'NY'): (43.0481, -76.1474), ('Poughkeepsie', 'NY'): (41.7004, -73.9210),
    ('Davidson', 'NC'): (35.4993, -80.8487), ('Durham', 'NC'): (35.9940, -78.8986),
    ('Chapel Hill', 'NC'): (35.9132, -79.0558), ('Winston-Salem', 'NC'): (36.0999, -80.2442),
    ('Cleveland', 'OH'): (41.4993, -81.6944), ('Granville', 'OH'): (40.0681, -82.5196),
    ('Gambier', 'OH'): (40.3759, -82.3974), ('Oberlin', 'OH'): (41.2940, -82.2171),
    ('Portland', 'OR'): (45.5152, -122.6784), ('Lewisburg', 'PA'): (40.9645, -76.8844),
    ('Pittsburgh', 'PA'): (40.4406, -79.9959), ('Carlisle', 'PA'): (40.2015, -77.1989),
    ('Lancaster', 'PA'): (40.0379, -76.3055), ('Haverford', 'PA'): (40.0104, -75.3066),
    ('Easton', 'PA'): (40.6910, -75.2207), ('Bethlehem', 'PA'): (40.6259, -75.3705),
    ('Philadelphia', 'PA'): (39.9526, -75.1652), ('Swarthmore', 'PA'): (39.9020, -75.3499),
    ('Villanova', 'PA'): (40.0388, -75.3458), ('Providence', 'RI'): (41.8240, -71.4128),
    ('Nashville', 'TN'): (36.1627, -86.7816), ('Houston', 'TX'): (29.7604, -95.3698),
    ('Dallas', 'TX'): (32.7767, -96.7970), ('Austin', 'TX'): (30.2672, -97.7431),
    ('Middlebury', 'VT'): (44.0153, -73.1673), ('Burlington', 'VT'): (44.4759, -73.2121),
    ('Williamsburg', 'VA'): (37.2707, -76.7075), ('University of Richmond', 'VA'): (37.5741, -77.5400),
    ('Blacksburg', 'VA'): (37.2296, -80.4139), ('Charlottesville', 'VA'): (38.0293, -78.4767),
    ('Madison', 'WI'): (43.0731, -89.4012),
}


def get_school_coordinates(row):
    """Get coordinates for a school based on city and state."""
    city_state = (row['CITY'], row['STABBR'])
    if city_state in CITY_COORDS:
        return CITY_COORDS[city_state]
    return (None, None)

# --- Load Data ---
DATA_FILE = os.path.join(os.path.dirname(__file__), 'ipeds_2023_2014.csv')
PROFILES_FILE = os.path.join(os.path.dirname(__file__), 'user_profiles.json')


def load_data():
    """Load and prepare the IPEDS time series data."""
    df = pd.read_csv(DATA_FILE)
    df['year'] = df['year'].astype(int)
    return df


def get_school_list(df):
    """Get list of unique school names sorted alphabetically."""
    max_year = df['year'].max()
    schools = df[df['year'] == max_year]['INSTNM'].dropna().unique()
    return sorted(schools)


def add_computed_fields(df):
    """Add computed fields to the dataframe."""
    df = df.copy()
    df['ENRLFTM'] = df['ENRLFTM'].fillna(0)
    df['ENRLFTW'] = df['ENRLFTW'].fillna(0)
    
    if 'percAdm' not in df.columns:
        df['percAdm'] = 100 * df['ADMSSN'] / df['APPLCN']
    if 'percAdmMen' not in df.columns:
        df['percAdmMen'] = 100 * df['ADMSSNM'] / df['APPLCNM']
    if 'percAdmWom' not in df.columns:
        df['percAdmWom'] = 100 * df['ADMSSNW'] / df['APPLCNW']
    
    df['approxUndergrad'] = 4 * (df['ENRLFTM'] + df['ENRLFTW'])
    df['approxPercWom'] = 100 * df['ENRLFTW'] / (df['ENRLFTM'] + df['ENRLFTW'])
    df['approxPercMen'] = 100 * df['ENRLFTM'] / (df['ENRLFTM'] + df['ENRLFTW'])
    df['citystate'] = df['CITY'].astype(str) + ', ' + df['STABBR'].astype(str)
    
    df['APP_M_pct'] = 100 * df['APPLCNM'] / df['APPLCN']
    df['APP_W_pct'] = 100 * df['APPLCNW'] / df['APPLCN']
    df['ADM_M_ratio'] = (df['ADMSSNM'] / df['ADMSSN']) / (df['APPLCNM'] / df['APPLCN'])
    df['ADM_W_ratio'] = (df['ADMSSNW'] / df['ADMSSN']) / (df['APPLCNW'] / df['APPLCN'])
    
    return df


# --- Profile Management (Dual Mode: PostgreSQL on Render, JSON locally) ---

def init_database():
    """Initialize the PostgreSQL database table if it doesn't exist."""
    if not DATABASE_URL:
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                data JSONB NOT NULL
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database init error: {e}")


def load_profiles():
    """Load user profiles from PostgreSQL or JSON file."""
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute('SELECT name, data FROM profiles')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return {row[0]: row[1] for row in rows}
        except Exception as e:
            print(f"Database load error: {e}")
            return {}
    else:
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}


def save_profile(name, data):
    """Save a single profile to PostgreSQL or JSON file."""
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO profiles (name, data) VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data
            ''', (name, Json(data)))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Database save error: {e}")
    else:
        profiles = load_profiles()
        profiles[name] = data
        with open(PROFILES_FILE, 'w') as f:
            json.dump(profiles, f, indent=2)


def delete_profile(name):
    """Delete a profile from PostgreSQL or JSON file."""
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute('DELETE FROM profiles WHERE name = %s', (name,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Database delete error: {e}")
    else:
        profiles = load_profiles()
        if name in profiles:
            del profiles[name]
            with open(PROFILES_FILE, 'w') as f:
                json.dump(profiles, f, indent=2)


def get_profile_names():
    """Get list of saved profile names."""
    profiles = load_profiles()
    return sorted(profiles.keys())


# Initialize database on startup if using PostgreSQL
if DATABASE_URL:
    init_database()
    print("Using PostgreSQL database for profiles")
else:
    print("Using local JSON file for profiles")


# Load data at startup
cdat = load_data()
cdat = add_computed_fields(cdat)
school_list = get_school_list(cdat)

# Default schools
DEFAULT_SCHOOLS = ['Stanford University', 'University of Chicago', 'Amherst College', 'Georgetown University']
DEFAULT_SCHOOLS = [s for s in DEFAULT_SCHOOLS if s in school_list][:4]
while len(DEFAULT_SCHOOLS) < 4:
    for s in school_list:
        if s not in DEFAULT_SCHOOLS:
            DEFAULT_SCHOOLS.append(s)
            break

# --- Initialize Dash App ---
app = Dash(__name__, title='College Data Comparison', suppress_callback_exceptions=True)
server = app.server

# --- Common Styles ---
SECTION_STYLE = {'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderRadius': '10px', 'marginBottom': '20px'}
HEADER_STYLE = {'color': '#34495e'}

# --- Navigation ---
def create_nav():
    link_style = {'marginRight': '25px', 'fontSize': '16px', 'color': 'white', 'textDecoration': 'none', 'fontWeight': 'bold'}
    return html.Div([
        html.Span('📊 ', style={'fontSize': '16px'}),
        dcc.Link('Compare Schools', href='/', style=link_style),
        html.Span('|', style={'color': 'rgba(255,255,255,0.5)', 'marginRight': '25px'}),
        html.Span('🔍 ', style={'fontSize': '16px'}),
        dcc.Link('Find Schools', href='/find', style=link_style),
        html.Span('|', style={'color': 'rgba(255,255,255,0.5)', 'marginRight': '25px'}),
        html.Span('📋 ', style={'fontSize': '16px'}),
        dcc.Link('Build School Lists', href='/lists', style={'fontSize': '16px', 'color': 'white', 'textDecoration': 'none', 'fontWeight': 'bold'}),
    ], style={'marginBottom': '20px', 'padding': '15px', 'backgroundColor': '#3498db', 'borderRadius': '5px', 'textAlign': 'center'})


# --- Page 1: Compare Schools ---
def create_compare_page():
    return html.Div([
        create_nav(),
        html.H1('College Data Comparison Dashboard', 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P('Compare admissions statistics and trends across 4 schools using IPEDS data (2014-2023)',
               style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'}),
        
        # School Selection Section
        html.Div([
            html.H3('Select Schools to Compare', style=HEADER_STYLE),
            html.Div([
                html.Div([
                    html.Label('School 1:', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='school1-dropdown', options=[{'label': s, 'value': s} for s in school_list],
                                value=DEFAULT_SCHOOLS[0], searchable=True, placeholder='Type to search...')
                ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                html.Div([
                    html.Label('School 2:', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='school2-dropdown', options=[{'label': s, 'value': s} for s in school_list],
                                value=DEFAULT_SCHOOLS[1], searchable=True, placeholder='Type to search...')
                ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                html.Div([
                    html.Label('School 3:', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='school3-dropdown', options=[{'label': s, 'value': s} for s in school_list],
                                value=DEFAULT_SCHOOLS[2], searchable=True, placeholder='Type to search...')
                ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                html.Div([
                    html.Label('School 4:', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='school4-dropdown', options=[{'label': s, 'value': s} for s in school_list],
                                value=DEFAULT_SCHOOLS[3], searchable=True, placeholder='Type to search...')
                ], style={'width': '24%', 'display': 'inline-block'}),
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Label('Test Type:', style={'fontWeight': 'bold', 'marginRight': '15px'}),
                dcc.RadioItems(id='test-type-toggle',
                    options=[{'label': ' SAT', 'value': 'SAT'}, {'label': ' ACT', 'value': 'ACT'}],
                    value='SAT', inline=True, style={'display': 'inline-block'},
                    inputStyle={'marginRight': '5px'}, labelStyle={'marginRight': '20px', 'fontSize': '16px'})
            ], style={'marginTop': '10px'}),
        ], style=SECTION_STYLE),
        
        html.Div([html.H3('Current Year Summary', style=HEADER_STYLE), html.Div(id='summary-table')], style={'marginBottom': '30px'}),
        html.Div([html.H3('Trends Over Time', style=HEADER_STYLE), dcc.Graph(id='trends-chart', style={'height': '800px'})]),
        
        html.Div([html.Hr(), html.P('Data Source: IPEDS (Integrated Postsecondary Education Data System)', 
                   style={'textAlign': 'center', 'color': '#95a5a6', 'fontSize': '12px'})])
    ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px', 'fontFamily': 'Arial, sans-serif'})


# --- Page 2: Build School Lists ---
def create_lists_page():
    profile_names = get_profile_names()
    return html.Div([
        create_nav(),
        html.H1('Build Your School Lists', 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P('Create and save personalized Reach, Middle, and Likely school lists',
               style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'}),
        
        # Profile Management Section
        html.Div([
            html.H3('Profile Management', style=HEADER_STYLE),
            html.Div([
                # Left column: Select Existing Profile + Load button
                html.Div([
                    html.Label('Select Existing Profile:', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='profile-dropdown', 
                                options=[{'label': p, 'value': p} for p in profile_names],
                                placeholder='Select a profile...', searchable=True),
                    html.Button('Load Profile', id='load-profile-btn', n_clicks=0,
                               style={'marginTop': '10px', 'padding': '10px 20px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}),
                ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '4%', 'verticalAlign': 'top'}),
                # Right column: Create New Profile + Save/Delete buttons
                html.Div([
                    html.Label('Or Create New Profile:', style={'fontWeight': 'bold'}),
                    dcc.Input(id='new-profile-input', type='text', placeholder='Enter new profile name...',
                             style={'width': '100%', 'padding': '8px'}),
                    html.Div([
                        html.Button('Save Profile', id='save-profile-btn', n_clicks=0,
                                   style={'marginTop': '10px', 'marginRight': '10px', 'padding': '10px 20px', 'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}),
                        html.Button('Delete Profile', id='delete-profile-btn', n_clicks=0,
                                   style={'marginTop': '10px', 'padding': '10px 20px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}),
                    ]),
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            ]),
            html.Div(id='profile-status', style={'marginTop': '10px', 'fontStyle': 'italic', 'color': '#27ae60'})
        ], style=SECTION_STYLE),
        
        # School Lists Section
        html.Div([
            html.H3('Build Your Lists', style=HEADER_STYLE),
            html.P('Select schools for each category. Use Ctrl+Click (Cmd+Click on Mac) to select multiple schools.',
                   style={'color': '#7f8c8d', 'fontSize': '14px'}),
            html.Div([
                # Reach Schools
                html.Div([
                    html.Label('🎯 Reach Schools:', style={'fontWeight': 'bold', 'fontSize': '16px', 'color': '#e74c3c'}),
                    html.P('Schools where admission is a stretch', style={'fontSize': '12px', 'color': '#7f8c8d', 'margin': '5px 0'}),
                    dcc.Dropdown(id='reach-schools', options=[{'label': s, 'value': s} for s in school_list],
                                multi=True, placeholder='Select reach schools...', searchable=True)
                ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '2%', 'verticalAlign': 'top'}),
                
                # Middle Schools
                html.Div([
                    html.Label('⚖️ Middle Schools:', style={'fontWeight': 'bold', 'fontSize': '16px', 'color': '#f39c12'}),
                    html.P('Schools where you have a reasonable chance', style={'fontSize': '12px', 'color': '#7f8c8d', 'margin': '5px 0'}),
                    dcc.Dropdown(id='middle-schools', options=[{'label': s, 'value': s} for s in school_list],
                                multi=True, placeholder='Select middle schools...', searchable=True)
                ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '2%', 'verticalAlign': 'top'}),
                
                # Likely Schools
                html.Div([
                    html.Label('✅ Likely Schools:', style={'fontWeight': 'bold', 'fontSize': '16px', 'color': '#27ae60'}),
                    html.P('Schools where admission is likely', style={'fontSize': '12px', 'color': '#7f8c8d', 'margin': '5px 0'}),
                    dcc.Dropdown(id='likely-schools', options=[{'label': s, 'value': s} for s in school_list],
                                multi=True, placeholder='Select likely schools...', searchable=True)
                ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            ]),
        ], style=SECTION_STYLE),
        
        # Test Type Toggle for Lists Page
        html.Div([
            html.Label('Test Type for Table:', style={'fontWeight': 'bold', 'marginRight': '15px'}),
            dcc.RadioItems(id='lists-test-type-toggle',
                options=[{'label': ' SAT', 'value': 'SAT'}, {'label': ' ACT', 'value': 'ACT'}],
                value='SAT', inline=True, style={'display': 'inline-block'},
                inputStyle={'marginRight': '5px'}, labelStyle={'marginRight': '20px', 'fontSize': '16px'})
        ], style={'marginBottom': '20px'}),
        
        # Summary Table Section
        html.Div([
            html.H3('Your School List Summary', style=HEADER_STYLE),
            html.Div(id='lists-summary-table')
        ], style={'marginBottom': '30px'}),
        
        # Map Section
        html.Div([
            html.H3('School Locations', style=HEADER_STYLE),
            dcc.Graph(id='lists-map', style={'height': '500px'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([html.Hr(), html.P('Data Source: IPEDS (Integrated Postsecondary Education Data System)', 
                   style={'textAlign': 'center', 'color': '#95a5a6', 'fontSize': '12px'})])
    ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px', 'fontFamily': 'Arial, sans-serif'})


# --- Page 3: Find Schools ---
def create_find_page():
    # Get unique LOCALE values from the most recent year
    max_year = cdat['year'].max()
    locale_values = sorted(cdat[cdat['year'] == max_year]['LOCALE'].dropna().unique())
    
    return html.Div([
        create_nav(),
        html.H1('Find Schools', 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P('Search for schools based on location type and admission rate',
               style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'}),
        
        # Search Criteria Section
        html.Div([
            html.H3('Search Criteria', style=HEADER_STYLE),
            html.Div([
                # LocType Filter
                html.Div([
                    html.Label('Location Type (select one or more):', style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                    dcc.Checklist(
                        id='loctype-checklist',
                        options=[{'label': f' {loc}', 'value': loc} for loc in locale_values],
                        value=[],
                        style={'columnCount': 3},
                        inputStyle={'marginRight': '5px'},
                        labelStyle={'marginBottom': '8px', 'display': 'block'}
                    )
                ], style={'width': '60%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                # Admit Rate Range
                html.Div([
                    html.Label('Admit Rate Range:', style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                    html.Div([
                        html.Span('From: ', style={'marginRight': '5px'}),
                        dcc.Input(id='admit-rate-min', type='number', min=0, max=100, step=1, value=0,
                                 style={'width': '80px', 'padding': '5px', 'marginRight': '15px'}),
                        html.Span('%', style={'marginRight': '20px'}),
                        html.Span('To: ', style={'marginRight': '5px'}),
                        dcc.Input(id='admit-rate-max', type='number', min=0, max=100, step=1, value=100,
                                 style={'width': '80px', 'padding': '5px', 'marginRight': '5px'}),
                        html.Span('%'),
                    ]),
                    html.P('(Lower bound is >=, upper bound is <=)', style={'fontSize': '12px', 'color': '#7f8c8d', 'marginTop': '5px'})
                ], style={'width': '35%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '5%'}),
            ]),
            html.Div([
                html.Button('Find Schools', id='find-schools-btn', n_clicks=0,
                           style={'marginTop': '20px', 'padding': '12px 30px', 'backgroundColor': '#27ae60', 'color': 'white', 
                                  'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '16px', 'fontWeight': 'bold'}),
            ])
        ], style=SECTION_STYLE),
        
        # Test Type Toggle
        html.Div([
            html.Label('Test Type for Table:', style={'fontWeight': 'bold', 'marginRight': '15px'}),
            dcc.RadioItems(id='find-test-type-toggle',
                options=[{'label': ' SAT', 'value': 'SAT'}, {'label': ' ACT', 'value': 'ACT'}],
                value='SAT', inline=True, style={'display': 'inline-block'},
                inputStyle={'marginRight': '5px'}, labelStyle={'marginRight': '20px', 'fontSize': '16px'})
        ], style={'marginBottom': '20px'}),
        
        # Results Section
        html.Div([
            html.H3('Search Results', style=HEADER_STYLE),
            html.Div(id='find-results-count', style={'marginBottom': '10px', 'fontStyle': 'italic', 'color': '#7f8c8d'}),
            html.Div(id='find-results-table')
        ], style={'marginBottom': '30px'}),
        
        # Map Section
        html.Div([
            html.H3('School Locations', style=HEADER_STYLE),
            dcc.Graph(id='find-results-map', style={'height': '500px'})
        ], style={'marginBottom': '30px'}),
        
        html.Div([html.Hr(), html.P('Data Source: IPEDS (Integrated Postsecondary Education Data System)', 
                   style={'textAlign': 'center', 'color': '#95a5a6', 'fontSize': '12px'})])
    ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px', 'fontFamily': 'Arial, sans-serif'})


# --- Main Layout with URL Routing ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


# --- URL Routing Callback ---
@callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/find':
        return create_find_page()
    if pathname == '/lists':
        return create_lists_page()
    return create_compare_page()


# --- Page 1 Callbacks ---
@callback(
    [Output('summary-table', 'children'), Output('trends-chart', 'figure')],
    [Input('school1-dropdown', 'value'), Input('school2-dropdown', 'value'),
     Input('school3-dropdown', 'value'), Input('school4-dropdown', 'value'),
     Input('test-type-toggle', 'value')]
)
def update_dashboard(school1, school2, school3, school4, test_type):
    """Update the dashboard when school selection or test type changes."""
    schools = [s for s in [school1, school2, school3, school4] if s]
    
    if not schools:
        return html.P('Please select at least one school.'), go.Figure()
    
    df_filtered = cdat[cdat['INSTNM'].isin(schools)].copy()
    max_year = df_filtered['year'].max()
    df_current = df_filtered[df_filtered['year'] == max_year].copy()
    
    table_with_footnote = create_school_table(df_current, test_type)
    fig = create_trends_chart(df_filtered, schools, test_type)
    
    return table_with_footnote, fig


# --- Helper function to create school table ---
def create_school_table(df_current, test_type, category_col=None):
    """Create a formatted school table."""
    def format_range(row, col25, col75):
        v25 = row.get(col25)
        v75 = row.get(col75)
        if pd.notna(v25) and pd.notna(v75):
            return f"{int(v25)}-{int(v75)}"
        return '-'
    
    if test_type == 'SAT':
        df_current = df_current.copy()
        df_current['SAT M 25-75'] = df_current.apply(lambda r: format_range(r, 'SATMT25', 'SATMT75'), axis=1)
        df_current['SAT V 25-75'] = df_current.apply(lambda r: format_range(r, 'SATVR25', 'SATVR75'), axis=1)
        
        table_cols = {
            'INSTNM': 'School Name', 'citystate': 'Location', 'LOCALE': 'LocType',
            'APPLCN': 'Applications', 'percAdm': 'Admit Rate', 'APP_M_pct': 'App M%',
            'ADM_M_ratio': 'Adm+ M', 'APP_W_pct': 'App W%', 'ADM_W_ratio': 'Adm+ W',
            'SAT M 25-75': 'SAT M 25-75', 'SAT V 25-75': 'SAT V 25-75',
            'SATPCT': 'SAT Sub%', 'approxUndergrad': 'Est. Ugrad',
        }
        pct_col = 'SAT Sub%'
    else:
        df_current = df_current.copy()
        df_current['ACT C 25-75'] = df_current.apply(lambda r: format_range(r, 'ACTCM25', 'ACTCM75'), axis=1)
        df_current['ACT M 25-75'] = df_current.apply(lambda r: format_range(r, 'ACTMT25', 'ACTMT75'), axis=1)
        
        table_cols = {
            'INSTNM': 'School Name', 'citystate': 'Location', 'LOCALE': 'LocType',
            'APPLCN': 'Applications', 'percAdm': 'Admit Rate', 'APP_M_pct': 'App M%',
            'ADM_M_ratio': 'Adm+ M', 'APP_W_pct': 'App W%', 'ADM_W_ratio': 'Adm+ W',
            'ACT C 25-75': 'ACT C 25-75', 'ACT M 25-75': 'ACT M 25-75',
            'ACTPCT': 'ACT Sub%', 'approxUndergrad': 'Est. Ugrad',
        }
        pct_col = 'ACT Sub%'
    
    if category_col:
        table_cols = {'Category': 'Category', **table_cols}
    
    df_table = df_current[[c for c in table_cols.keys() if c in df_current.columns]].copy()
    df_table = df_table.rename(columns=table_cols)
    
    for col in df_table.columns:
        if col in ['Applications', 'Admissions', 'Est. Ugrad']:
            df_table[col] = df_table[col].apply(lambda x: f'{x:,.0f}' if pd.notna(x) else '-')
        elif col in ['Admit Rate', 'App M%', 'App W%', pct_col]:
            df_table[col] = df_table[col].apply(lambda x: f'{x:.1f}%' if pd.notna(x) else '-')
        elif col in ['Adm+ M', 'Adm+ W']:
            df_table[col] = df_table[col].apply(lambda x: f'{x:.2f}' if pd.notna(x) else '-')
    
    # Style for category highlighting
    style_data_conditional = [{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}]
    if category_col:
        style_data_conditional = [
            {'if': {'filter_query': '{Category} = "🎯 Reach"'}, 'backgroundColor': '#fadbd8'},
            {'if': {'filter_query': '{Category} = "⚖️ Middle"'}, 'backgroundColor': '#fef9e7'},
            {'if': {'filter_query': '{Category} = "✅ Likely"'}, 'backgroundColor': '#d5f5e3'},
        ]
    
    table = dash_table.DataTable(
        data=df_table.to_dict('records'),
        columns=[{'name': c, 'id': c} for c in df_table.columns],
        style_cell={'textAlign': 'left', 'padding': '10px', 'fontSize': '14px'},
        style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': 'bold'},
        style_data_conditional=style_data_conditional
    )
    
    return html.Div([
        table,
        html.P([
            html.Strong('Adm+ M'), ': Admission advantage ratio for men (>1 means men are admitted at a higher rate than the school average). ',
            html.Strong('Adm+ W'), ': Admission advantage ratio for women (>1 means women are admitted at a higher rate than the school average).'
        ], style={'fontSize': '12px', 'color': '#7f8c8d', 'marginTop': '10px', 'fontStyle': 'italic'})
    ])


# --- Helper function to create trends chart ---
def create_trends_chart(df_filtered, schools, test_type):
    """Create the trends chart."""
    if test_type == 'SAT':
        subplot_titles = ('Admission Rate (%)', 'SAT Submission Rate (%)',
                         'SAT Math Score (25th Percentile)', 'SAT Verbal Score (25th Percentile)')
        submit_col, score1_col, score2_col = 'SATPCT', 'SATMT25', 'SATVR25'
    else:
        subplot_titles = ('Admission Rate (%)', 'ACT Submission Rate (%)',
                         'ACT Composite Score (25th Percentile)', 'ACT Math Score (25th Percentile)')
        submit_col, score1_col, score2_col = 'ACTPCT', 'ACTCM25', 'ACTMT25'
    
    fig = make_subplots(rows=2, cols=2, subplot_titles=subplot_titles, vertical_spacing=0.12, horizontal_spacing=0.08)
    colors = px.colors.qualitative.Set2[:len(schools)]
    
    for i, school in enumerate(schools):
        df_school = df_filtered[df_filtered['INSTNM'] == school].sort_values('year')
        color = colors[i % len(colors)]
        
        fig.add_trace(go.Scatter(x=df_school['year'], y=df_school['percAdm'], mode='lines+markers',
                                name=school, line=dict(color=color), legendgroup=school, showlegend=True), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_school['year'], y=df_school[submit_col], mode='lines+markers',
                                name=school, line=dict(color=color), legendgroup=school, showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=df_school['year'], y=df_school[score1_col], mode='lines+markers',
                                name=school, line=dict(color=color), legendgroup=school, showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_school['year'], y=df_school[score2_col], mode='lines+markers',
                                name=school, line=dict(color=color), legendgroup=school, showlegend=False), row=2, col=2)
    
    fig.update_layout(height=700, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5), margin=dict(t=100))
    fig.update_xaxes(title_text='Year', dtick=1)
    fig.update_yaxes(title_text='%', row=1, col=1)
    fig.update_yaxes(title_text='%', row=1, col=2)
    fig.update_yaxes(title_text='Score', row=2, col=1)
    fig.update_yaxes(title_text='Score', row=2, col=2)
    
    return fig


# --- Page 2 Callbacks ---
@callback(
    [Output('reach-schools', 'value'), Output('middle-schools', 'value'), Output('likely-schools', 'value'),
     Output('profile-status', 'children'), Output('profile-dropdown', 'options')],
    [Input('load-profile-btn', 'n_clicks'), Input('save-profile-btn', 'n_clicks'), Input('delete-profile-btn', 'n_clicks')],
    [State('profile-dropdown', 'value'), State('new-profile-input', 'value'),
     State('reach-schools', 'value'), State('middle-schools', 'value'), State('likely-schools', 'value')],
    prevent_initial_call=True
)
def manage_profiles(load_clicks, save_clicks, delete_clicks, selected_profile, new_profile_name, reach, middle, likely):
    """Handle profile load, save, and delete operations."""
    triggered = ctx.triggered_id
    profiles = load_profiles()
    status = ''
    
    # Determine profile name
    profile_name = new_profile_name.strip() if new_profile_name else selected_profile
    
    if triggered == 'load-profile-btn' and selected_profile:
        if selected_profile in profiles:
            data = profiles[selected_profile]
            reach = data.get('reach', [])
            middle = data.get('middle', [])
            likely = data.get('likely', [])
            status = f'✓ Loaded profile: {selected_profile}'
        else:
            status = f'✗ Profile not found: {selected_profile}'
    
    elif triggered == 'save-profile-btn' and profile_name:
        data = {
            'reach': reach or [],
            'middle': middle or [],
            'likely': likely or []
        }
        save_profile(profile_name, data)
        profiles[profile_name] = data  # Update local copy for dropdown
        status = f'✓ Saved profile: {profile_name}'
    
    elif triggered == 'delete-profile-btn' and selected_profile:
        if selected_profile in profiles:
            delete_profile(selected_profile)
            del profiles[selected_profile]  # Update local copy for dropdown
            reach, middle, likely = [], [], []
            status = f'✓ Deleted profile: {selected_profile}'
        else:
            status = f'✗ Profile not found: {selected_profile}'
    
    profile_options = [{'label': p, 'value': p} for p in sorted(profiles.keys())]
    return reach or [], middle or [], likely or [], status, profile_options


@callback(
    [Output('lists-summary-table', 'children'), Output('lists-map', 'figure')],
    [Input('reach-schools', 'value'), Input('middle-schools', 'value'), Input('likely-schools', 'value'),
     Input('lists-test-type-toggle', 'value')]
)
def update_lists_table(reach, middle, likely, test_type):
    """Update the summary table and map for school lists."""
    reach = reach or []
    middle = middle or []
    likely = likely or []
    
    all_schools = reach + middle + likely
    
    # Create the map
    fig = go.Figure()
    
    if not all_schools:
        # Empty map
        fig.update_geos(
            scope='usa',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            showsubunits=True,
            subunitcolor='rgb(200, 200, 200)',
            bgcolor='rgba(0,0,0,0)'
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            title=dict(text='Select schools to see their locations', x=0.5, xanchor='center'),
            paper_bgcolor='white'
        )
        return html.P('Select schools in the lists above to see their summary.', style={'color': '#7f8c8d', 'fontStyle': 'italic'}), fig
    
    max_year = cdat['year'].max()
    df_current = cdat[cdat['year'] == max_year].copy()
    df_filtered = df_current[df_current['INSTNM'].isin(all_schools)].copy()
    
    # Add category column
    def get_category(school):
        if school in reach:
            return '🎯 Reach'
        elif school in middle:
            return '⚖️ Middle'
        elif school in likely:
            return '✅ Likely'
        return ''
    
    df_filtered['Category'] = df_filtered['INSTNM'].apply(get_category)
    
    # Sort by category order
    category_order = {'🎯 Reach': 0, '⚖️ Middle': 1, '✅ Likely': 2}
    df_filtered['cat_order'] = df_filtered['Category'].map(category_order)
    df_filtered = df_filtered.sort_values(['cat_order', 'INSTNM']).drop(columns=['cat_order'])
    
    # Build the map with category-based colors
    df_map = df_filtered.copy()
    df_map['lat'] = df_map.apply(lambda r: get_school_coordinates(r)[0], axis=1)
    df_map['lon'] = df_map.apply(lambda r: get_school_coordinates(r)[1], axis=1)
    df_map = df_map.dropna(subset=['lat', 'lon'])
    
    # Color mapping for categories
    category_colors = {'🎯 Reach': '#e74c3c', '⚖️ Middle': '#f39c12', '✅ Likely': '#27ae60'}
    
    if len(df_map) > 0:
        for cat, color in category_colors.items():
            cat_data = df_map[df_map['Category'] == cat]
            if len(cat_data) > 0:
                cat_data = cat_data.copy()
                cat_data['hover_text'] = cat_data.apply(
                    lambda r: f"<b>{r['INSTNM']}</b><br>{r['CITY']}, {r['STABBR']}<br>Admit Rate: {r['percAdm']:.1f}%", 
                    axis=1
                )
                fig.add_trace(go.Scattergeo(
                    lon=cat_data['lon'],
                    lat=cat_data['lat'],
                    text=cat_data['hover_text'],
                    hoverinfo='text',
                    mode='markers',
                    marker=dict(size=14, color=color, line=dict(width=1, color='white')),
                    name=cat
                ))
    
    fig.update_geos(
        scope='usa',
        showland=True,
        landcolor='rgb(243, 243, 243)',
        showlakes=True,
        lakecolor='rgb(255, 255, 255)',
        showsubunits=True,
        subunitcolor='rgb(200, 200, 200)',
        showcountries=True,
        countrycolor='rgb(150, 150, 150)',
        bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(text=f'{len(all_schools)} School{"s" if len(all_schools) != 1 else ""} in Your List', x=0.5, xanchor='center'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        paper_bgcolor='white'
    )
    
    return create_school_table(df_filtered, test_type, category_col='Category'), fig


# --- Page 3 Callbacks: Find Schools ---
@callback(
    [Output('find-results-table', 'children'), Output('find-results-count', 'children'),
     Output('find-results-map', 'figure')],
    [Input('find-schools-btn', 'n_clicks')],
    [State('loctype-checklist', 'value'), State('admit-rate-min', 'value'),
     State('admit-rate-max', 'value'), State('find-test-type-toggle', 'value')],
    prevent_initial_call=True
)
def find_schools(n_clicks, loctypes, admit_min, admit_max, test_type):
    """Search for schools matching the criteria."""
    max_year = cdat['year'].max()
    df_current = cdat[cdat['year'] == max_year].copy()
    
    # Apply filters
    if loctypes:
        df_current = df_current[df_current['LOCALE'].isin(loctypes)]
    
    if admit_min is not None:
        df_current = df_current[df_current['percAdm'] >= admit_min]
    
    if admit_max is not None:
        df_current = df_current[df_current['percAdm'] <= admit_max]
    
    # Sort by admit rate
    df_current = df_current.sort_values('percAdm')
    
    count = len(df_current)
    
    # Create the map
    fig = go.Figure()
    
    if count > 0:
        # Add coordinates from city lookup
        df_map = df_current.copy()
        df_map['lat'] = df_map.apply(lambda r: get_school_coordinates(r)[0], axis=1)
        df_map['lon'] = df_map.apply(lambda r: get_school_coordinates(r)[1], axis=1)
        df_map = df_map.dropna(subset=['lat', 'lon'])
        
        if len(df_map) > 0:
            # Create hover text
            df_map['hover_text'] = df_map.apply(
                lambda r: f"<b>{r['INSTNM']}</b><br>{r['CITY']}, {r['STABBR']}<br>Admit Rate: {r['percAdm']:.1f}%", 
                axis=1
            )
            
            # Add school markers
            fig.add_trace(go.Scattergeo(
                lon=df_map['lon'],
                lat=df_map['lat'],
                text=df_map['hover_text'],
                hoverinfo='text',
                mode='markers',
                marker=dict(
                    size=12,
                    color=df_map['percAdm'],
                    colorscale='RdYlGn',
                    cmin=0,
                    cmax=100,
                    colorbar=dict(title='Admit Rate %', thickness=15),
                    line=dict(width=1, color='white')
                ),
                name='Schools'
            ))
    
    # Configure the map layout
    fig.update_geos(
        scope='usa',
        showland=True,
        landcolor='rgb(243, 243, 243)',
        showlakes=True,
        lakecolor='rgb(255, 255, 255)',
        showsubunits=True,
        subunitcolor='rgb(200, 200, 200)',
        showcountries=True,
        countrycolor='rgb(150, 150, 150)',
        bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(text=f'{count} School{"s" if count != 1 else ""} Found' if count > 0 else 'No Schools Found', 
                   x=0.5, xanchor='center'),
        geo=dict(bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='white'
    )
    
    if count == 0:
        return (html.P('No schools found matching your criteria.', style={'color': '#e74c3c', 'fontStyle': 'italic'}), 
                '', fig)
    
    count_text = f'Found {count} school{"s" if count != 1 else ""} matching your criteria.'
    return create_school_table(df_current, test_type), count_text, fig


# --- Run Server ---
if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n" + "="*60)
    print("College Data Comparison Dashboard")
    print("="*60)
    print(f"Data loaded: {len(cdat)} records, {len(school_list)} schools")
    print(f"Years: {cdat['year'].min()} - {cdat['year'].max()}")
    print(f"\nLocal access:   http://127.0.0.1:8050")
    print(f"Network access: http://{local_ip}:8050")
    print("\nPages:")
    print("  - Compare Schools: http://127.0.0.1:8050/")
    print("  - Find Schools:    http://127.0.0.1:8050/find")
    print("  - Build Lists:     http://127.0.0.1:8050/lists")
    print("\n(Use the network address to access from your phone)")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=8050)
