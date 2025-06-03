import os
import logging
import traceback
import requests
import atexit
from flask import Flask, request, render_template, jsonify
import pandas as pd
import numpy as np
from werkzeug.serving import run_simple
import re
from urllib.parse import quote_plus
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'distress_analysis.db'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def init_database():
    """Initialize the SQLite database for storing analysis results"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Create properties table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            distress_score INTEGER,
            risk_level TEXT,
            discount_potential TEXT,
            property_value REAL,
            confidence INTEGER,
            risk_factors TEXT,
            analysis_type TEXT,
            source_file TEXT,
            case_id TEXT,
            party_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            distress_explanation TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

def cleanup():
    """Cleanup function to be called on shutdown"""
    logger.info("Shutting down Flask application...")
    # Add any cleanup code here

atexit.register(cleanup)

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {str(error)}")
    logger.error(traceback.format_exc())
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

def clean_nan(obj):
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(x) for x in obj]
    elif isinstance(obj, float) and (pd.isna(obj) or np.isnan(obj)):
        return ''
    else:
        return obj

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/distress-dashboard')
def distress_dashboard():
    """New page showing all analyzed properties with filtering"""
    return render_template('distress_dashboard.html')

@app.route('/api/properties')
def get_properties():
    """API endpoint to get all properties with optional filtering"""
    source_file = request.args.get('source_file', None)
    analysis_type = request.args.get('analysis_type', None)
    
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Build query with filters
    query = '''
        SELECT 
            id, address, distress_score, risk_level, discount_potential, 
            property_value, confidence, risk_factors, analysis_type, 
            source_file, case_id, party_name, created_at, distress_explanation
        FROM properties
        WHERE 1=1
    '''
    params = []
    
    if source_file:
        query += ' AND source_file = ?'
        params.append(source_file)
    
    if analysis_type:
        query += ' AND analysis_type = ?'
        params.append(analysis_type)
    
    query += ' ORDER BY distress_score DESC, created_at DESC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    properties = []
    for row in rows:
        risk_factors = json.loads(row[7]) if row[7] else []
        properties.append({
            'id': row[0],
            'address': row[1],
            'distress_score': row[2],
            'risk_level': row[3],
            'discount_potential': row[4],
            'property_value': row[5],
            'confidence': row[6],
            'risk_factors': risk_factors,
            'analysis_type': row[8],
            'source_file': row[9],
            'case_id': row[10],
            'party_name': row[11],
            'created_at': row[12],
            'distress_explanation': row[13]
        })
    
    conn.close()
    return jsonify({'properties': properties})

@app.route('/api/source-files')
def get_source_files():
    """Get list of unique source files for filtering"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT source_file FROM properties WHERE source_file IS NOT NULL ORDER BY source_file')
    files = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'files': files})

@app.route('/api/save-analysis', methods=['POST'])
def save_analysis():
    """Save analysis results to database"""
    try:
        data = request.json
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # Generate distress explanation with property data
        risk_factors = data.get('risk_factors', [])
        distress_score = data.get('distress_score', 0)
        discount_potential = data.get('discount_potential', '0-0%')
        
        # Extract property data from the request
        property_data = {
            'current_value': data.get('property_value', 0),
            'days_on_market': data.get('days_on_market', 0),
            'tax_liens': data.get('tax_liens', 0),
            'year_built': data.get('year_built', 0),
            'court_deadline': data.get('court_deadline', 0),
            'case_duration_months': data.get('case_duration_months', 0)
        }
        
        explanation = generate_distress_explanation(distress_score, discount_potential, risk_factors, property_data)
        
        cursor.execute('''
            INSERT INTO properties 
            (address, distress_score, risk_level, discount_potential, property_value,
             confidence, risk_factors, analysis_type, source_file, case_id, 
             party_name, distress_explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('address'),
            data.get('distress_score'),
            data.get('risk_level'),
            data.get('discount_potential'),
            data.get('property_value'),
            data.get('confidence'),
            json.dumps(data.get('risk_factors', [])),
            data.get('analysis_type', 'divorce'),
            data.get('source_file'),
            data.get('case_id'),
            data.get('party_name'),
            explanation
        ))
        
        conn.commit()
        property_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'id': property_id})
        
    except Exception as e:
        logger.error(f"Error saving analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_distress_explanation(distress_score, discount_potential, risk_factors, property_data=None):
    """Generate concise explanation based on real property data and distress factors"""
    
    # Extract real metrics from property data if available
    factors = []
    
    # Add property-specific metrics from ATTOM API
    if property_data:
        value = property_data.get('current_value', 0)
        if value > 0:
            if value > 500000:
                factors.append(f"${value:,} high-value property")
            else:
                factors.append(f"${value:,} property")
        
        # Court deadline creates urgency
        court_deadline = property_data.get('court_deadline', 0)
        if court_deadline > 0 and court_deadline < 120:
            factors.append(f"{court_deadline}-day court deadline")
        
        # Case duration shows extended stress
        case_duration = property_data.get('case_duration_months', 0)
        if case_duration > 12:
            factors.append(f"{case_duration}-month case duration")
        
        # Days on market from ATTOM data
        days_on_market = property_data.get('days_on_market', 0)
        if days_on_market > 90:
            factors.append(f"{days_on_market} days on market")
        
        # Tax liens from ATTOM data
        tax_liens = property_data.get('tax_liens', 0)
        if tax_liens > 0:
            factors.append(f"${tax_liens:,} tax liens")
        
        # Property age risk
        year_built = property_data.get('year_built', 0)
        if year_built > 0 and (2024 - year_built) > 30:
            factors.append(f"{2024 - year_built}yr old property")
    
    # Add real case-specific factors from risk_factors (limit to most important)
    divorce_factors = []
    for factor in risk_factors:
        if "court-ordered sale" in factor.lower():
            divorce_factors.append("court-ordered sale")
        elif "dual mortgage" in factor.lower():
            divorce_factors.append("dual mortgage obligations")
        elif "legal fee" in factor.lower():
            divorce_factors.append("high legal costs")
        elif "child support" in factor.lower():
            divorce_factors.append("child support requirements")
        elif "contested" in factor.lower():
            divorce_factors.append("contested divorce")
    
    # Combine property and divorce factors (max 4 total)
    all_factors = factors + divorce_factors[:2]  # Prioritize property data
    
    # Build concise explanation with real factors only
    if all_factors:
        factor_list = ", ".join(all_factors[:4])  # Max 4 factors
        return f"{discount_potential} discount from {factor_list}."
    else:
        return f"{discount_potential} discount potential from divorce proceedings."

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.info('Received upload request')
    try:
        logging.info(f"Request files: {request.files}")
        if 'file' not in request.files:
            logging.error('No file part in request')
            return jsonify({'success': False, 'error': 'No file part'}), 400
        file = request.files['file']
        logging.info(f"Uploaded filename: {file.filename}")
        if file.filename == '':
            logging.error('No selected file')
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        filename = file.filename.replace(' ', '_')
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logging.info(f'Saving file to: {save_path}')
        file.save(save_path)
        logging.info('Attempting to read Excel file')
        df = pd.read_excel(save_path)
        logging.info(f'Successfully read Excel file. Shape: {df.shape}')
        data = df.to_dict(orient='records')
        cleaned_data = clean_nan(data)
        logging.info(f"Returning {len(cleaned_data)} records from upload.")
        return jsonify({'success': True, 'data': cleaned_data})
    except Exception as e:
        logging.error(f'Error processing file: {e}')
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

def clean_address1(address: str) -> str:
    """
    Clean and normalize US residential address1 for ATTOM API queries.
    Always preserve trailing LOT, UNIT, or APT suffixes and their values for ATTOM API queries.
    Only strip them for fallback/retry.
    """
    if not address:
        return ""
    address = address.strip().upper()
    address = re.sub(r"\s{2,}", " ", address)            # Remove double spaces
    address = re.sub(r"\.\s*$", "", address)             # Remove trailing periods
    # Normalize unit/apartment/lot spacing
    address = re.sub(r"\bAPT(\d+)", r"APT \1", address)
    address = re.sub(r"\bUNIT(\s?)([A-Z0-9]+)", r"UNIT \2", address)
    address = re.sub(r"\bLOT(\s?)(\d+)", r"LOT \2", address)
    # Remove extra commas or trailing punctuation
    address = address.replace(",,", ",").rstrip(",. ")
    # USPS suffix normalization
    usps_suffix_map = {
        r"\bDR\b": "DRIVE",
        r"\bRD\b": "ROAD",
        r"\bST\b": "STREET",
        r"\bCT\b": "COURT",
        r"\bLN\b": "LANE",
        r"\bAVE\b": "AVENUE",
        r"\bBLVD\b": "BOULEVARD",
        r"\bPL\b": "PLACE",
        r"\bPKWY\b": "PARKWAY",
        r"\bTER\b": "TERRACE",
        r"\bCIR\b": "CIRCLE",
    }
    for pattern, replacement in usps_suffix_map.items():
        address = re.sub(pattern, replacement, address)
    # DO NOT strip trailing LOT/UNIT/APT and value here (preserve for ATTOM)
    return address.strip()

def is_valid_florida_address(address2):
    # Ensures format is like: "PALM BEACH GARDENS, FL 33418"
    return bool(re.match(r'^([A-Z\s]+),\s?FL\s\d{5}$', address2.upper()))

def strip_unit_or_lot_suffix(address: str) -> str:
    """
    Remove unit or lot info from the end of an address string for retrying ATTOM lookups.
    """
    return re.sub(r'\b(UNIT|APT|LOT)\s*[A-Z0-9#\-]+$', '', address).strip().rstrip(',')

def query_attom_avm(address1, address2):
    """Query ATTOM AVM API and return the parsed JSON response."""
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
    params = {
        'address1': address1,
        'address2': address2
    }
    headers = {
        'accept': 'application/json',
        'apikey': 'ad91f2f30426f1ee54aec35791aaa044'
    }
    try:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error(f"query_attom_avm error: {e}")
        return {'status': {'code': 400, 'msg': 'Error'}, 'property': []}

# Helper: generate address variants for brute-force ATTOM AVM

def generate_address_variants(address):
    """
    Generate address variants: original, stripped unit/apt/lot, alternate suffixes.
    """
    variants = [address]
    # Strip unit/apt/lot
    stripped = strip_unit_or_lot_suffix(address)
    if stripped != address:
        variants.append(stripped)
    # Try alternate suffixes (e.g., DR <-> DRIVE, ST <-> STREET, etc.)
    usps_suffix_map = [
        (r"\bDRIVE\b", "DR"), (r"\bDR\b", "DRIVE"),
        (r"\bROAD\b", "RD"), (r"\bRD\b", "ROAD"),
        (r"\bSTREET\b", "ST"), (r"\bST\b", "STREET"),
        (r"\bCOURT\b", "CT"), (r"\bCT\b", "COURT"),
        (r"\bLANE\b", "LN"), (r"\bLN\b", "LANE"),
        (r"\bAVENUE\b", "AVE"), (r"\bAVE\b", "AVENUE"),
        (r"\bBOULEVARD\b", "BLVD"), (r"\bBLVD\b", "BOULEVARD"),
        (r"\bPLACE\b", "PL"), (r"\bPL\b", "PLACE"),
        (r"\bPARKWAY\b", "PKWY"), (r"\bPKWY\b", "PARKWAY"),
        (r"\bTERRACE\b", "TER"), (r"\bTER\b", "TERRACE"),
        (r"\bCIRCLE\b", "CIR"), (r"\bCIR\b", "CIRCLE"),
    ]
    for pattern, replacement in usps_suffix_map:
        alt = re.sub(pattern, replacement, address)
        if alt != address and alt not in variants:
            variants.append(alt)
        if stripped:
            alt2 = re.sub(pattern, replacement, stripped)
            if alt2 != stripped and alt2 not in variants:
                variants.append(alt2)
    return variants

# Add this helper for logging variants

def log_variant_attempt(variant, address2):
    print(f"  [TRY] {variant}, {address2}", flush=True)

def log_attom_response(resp):
    print(f"    [ATTOM STATUS] {getattr(resp, 'status_code', 'N/A')}", flush=True)
    try:
        print(f"    [ATTOM BODY] {resp.text[:200]}...", flush=True)
    except Exception:
        pass

def try_attom_variants(address1_variants, address2):
    """Try each address1 variant until a valuation is found, with detailed logging."""
    for variant in address1_variants:
        log_variant_attempt(variant, address2)
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
        params = {'address1': variant, 'address2': address2}
        headers = {'accept': 'application/json', 'apikey': 'ad91f2f30426f1ee54aec35791aaa044'}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            log_attom_response(resp)
            resp.raise_for_status()
            response = resp.json()
        except Exception as e:
            print(f"    [ATTOM ERROR] {e}", flush=True)
            continue
        if response and response.get('status', {}).get('code') == 0 and response.get('status', {}).get('msg') == 'SuccessWithResult':
            prop = response.get('property', [{}])[0]
            one_line = prop.get('address', {}).get('oneLine', f"{variant}, {address2}")
            value = prop.get('avm', {}).get('amount', {}).get('value', 'N/A')
            logger.info(f"ATTOM success: {one_line} -> {value} (variant: {variant})")
            return one_line, value
    logger.info(f"ATTOM failed for all variants: {address1_variants} {address2}")
    return f"{address1_variants[0]}, {address2}", 'N/A'

@app.route('/cross-reference', methods=['POST'])
def cross_reference():
    logging.info('Received cross-reference request')
    try:
        data = request.json
        logging.info(f"Input data: {data}")
        if not data or not isinstance(data, list):
            logging.error(f"Invalid data format: {data}")
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400

        results_dict = {}  # Deduplicate by oneLine address
        for idx, row in enumerate(data):
            logging.info(f"Row {idx}: {row}")
            raw_address1 = row.get('street address') or row.get('Street Address') or ''
            raw_address2 = row.get('CSZ', '')
            logging.info(f"Raw address1: '{raw_address1}', raw address2: '{raw_address2}'")
            address1 = clean_address1(raw_address1)
            address2 = raw_address2.strip().upper().replace(' ,', ',').replace('  ', ' ')
            logging.info(f"Cleaned address1: '{address1}', address2: '{address2}'")

            if not address1 or not address2 or not is_valid_florida_address(address2):
                results_dict[f"{address1}, {address2}"] = 'N/A'
                continue

            address1_variants = generate_address_variants(address1)
            one_line, value = try_attom_variants(address1_variants, address2)
            results_dict[one_line] = value

        # Output as sorted list of dicts for frontend
        results = [
            {'address': addr, 'Valuation': val}
            for addr, val in sorted(results_dict.items())
        ]
        logging.info(f"Final deduped results list: {results}")
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        logging.error(f'Error in cross-reference: {e}')
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/cross-reference-single', methods=['POST'])
def cross_reference_single():
    logging.info('Received cross-reference-single request')
    try:
        row = request.json
        logging.info(f"cross-reference-single input: {row}")
        if not isinstance(row, dict):
            logging.error('cross-reference-single: Invalid data format')
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400
        # Clean and prep address as before
        raw_address1 = row.get('street address') or row.get('Street Address') or ''
        raw_address2 = row.get('CSZ', '')
        address1 = clean_address1(raw_address1)
        address2 = raw_address2.strip().upper().replace(' ,', ',').replace('  ', ' ')
        if not address1 or not address2 or not is_valid_florida_address(address2):
            return jsonify({'success': True, 'data': {'Valuation': 'N/A', 'Address': address1}})
        address1_variants = generate_address_variants(address1)
        one_line, value = try_attom_variants(address1_variants, address2)
        logging.info(f"Returning: {one_line} -> {value}")
        return jsonify({'success': True, 'data': {'Valuation': value, 'Address': one_line}})
    except Exception as e:
        logging.exception('cross-reference-single: Exception')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/distress-single', methods=['POST'])
def distress_single():
    try:
        row = request.json
        app.logger.info(f"distress-single input: {row}")
        # Validate input
        if not isinstance(row, dict):
            app.logger.error('distress-single: Invalid data format')
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400
        # Extract relevant fields for distress scoring, defaulting to 0/False if missing
        attom_data = {
            'loanToValuePct': row.get('loanToValuePct', 0) or 0,
            'daysOnMarket': row.get('daysOnMarket', 0) or 0,
            'medianDaysOnMarket': row.get('medianDaysOnMarket', 0) or 0,
            'originalListPrice': row.get('originalListPrice', 0) or 0,
            'currentListPrice': row.get('currentListPrice', 0) or 0,
            'preforeclosureActive': row.get('preforeclosureActive', False) or False,
            'taxDelinquent': row.get('taxDelinquent', False) or False,
            'absenteeOwner': row.get('absenteeOwner', False) or False,
            'absorptionRate': row.get('absorptionRate', 0) or 0
        }
        from src.services.calculateDistressScore import calculateDistressScore
        result = calculateDistressScore(attom_data)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        import traceback
        app.logger.error(f"Distress error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # Always run on port 5001 for local dev
        run_simple('127.0.0.1', 5001, app, use_debugger=True, use_reloader=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(traceback.format_exc()) 

