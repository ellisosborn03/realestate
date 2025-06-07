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
import sys

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), '..', 'data', 'distress_analysis.db')

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
            id, address, distress_score, risk_factors, analysis_type, 
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
        risk_factors = json.loads(row[3]) if row[3] else []
        property_value = 0  # No DB column, so always 0 for now
        properties.append({
            'id': row[0],
            'address': row[1],
            'distress_score': row[2],
            'risk_factors': risk_factors,
            'analysis_type': row[4],
            'source_file': row[5],
            'case_id': row[6],
            'party_name': row[7],
            'created_at': row[8],
            'distress_explanation': row[9],
            'property_value': property_value,
        })
    
    # Add attom_available flag
    for prop in properties:
        prop['attom_available'] = bool(prop.get('property_value') or prop.get('attom_id'))

    # Debug print: show the property id and dict for each property
    for prop in properties:
        print(f'\n[DEBUG] Property ID: {prop.get("id")} | Property dict: {prop}', flush=True)

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
        
        # Extract REAL property data from the analysis results
        property_data = {}
        
        # Get actual property value (from ATTOM AVM)
        property_value = data.get('property_value', 0)
        if property_value > 0:
            property_data['current_value'] = property_value
            
        # Extract real property characteristics from the analysis
        if 'year_built' in data and data.get('year_built', 0) > 0:
            property_data['year_built'] = data.get('year_built')
            
        # Tax data from actual analysis
        if 'tax_liens' in data and data.get('tax_liens', 0) > 0:
            property_data['tax_liens'] = data.get('tax_liens')
            
        # Additional real data fields from divorce analysis
        if 'assessed_value' in data and data.get('assessed_value', 0) > 0:
            property_data['assessed_value'] = data.get('assessed_value')
            
        if 'tax_amount' in data and data.get('tax_amount', 0) > 0:
            property_data['tax_amount'] = data.get('tax_amount')
            
        if 'tax_year' in data:
            property_data['tax_year'] = data.get('tax_year')
            
        # Property characteristics 
        if 'property_type' in data and data.get('property_type'):
            property_data['property_type'] = data.get('property_type')
            
        if 'building_size' in data and data.get('building_size', 0) > 0:
            property_data['building_size'] = data.get('building_size')
            
        if 'lot_size' in data and data.get('lot_size', 0) > 0:
            property_data['lot_size'] = data.get('lot_size')
            
        if 'bedrooms' in data and data.get('bedrooms', 0) > 0:
            property_data['bedrooms'] = data.get('bedrooms')
            
        if 'bathrooms' in data and data.get('bathrooms', 0) > 0:
            property_data['bathrooms'] = data.get('bathrooms')
            
        # Ownership and occupancy status
        if 'owner_occupied' in data:
            property_data['owner_occupied'] = data.get('owner_occupied')
            
        if 'owner_name' in data and data.get('owner_name'):
            property_data['owner_name'] = data.get('owner_name')
            
        # Sales history and market data
        if 'last_sale_price' in data and data.get('last_sale_price', 0) > 0:
            property_data['last_sale_price'] = data.get('last_sale_price')
            
        if 'last_sale_date' in data and data.get('last_sale_date'):
            property_data['last_sale_date'] = data.get('last_sale_date')
            
        if 'sales_history_count' in data and data.get('sales_history_count', 0) > 0:
            property_data['sales_history_count'] = data.get('sales_history_count')
            
        if 'price_appreciation' in data:
            property_data['price_appreciation'] = data.get('price_appreciation')
            
        # Valuation confidence and range data
        if 'confidence_score' in data and data.get('confidence_score', 0) > 0:
            property_data['confidence_score'] = data.get('confidence_score')
            
        if 'value_high' in data and data.get('value_high', 0) > 0:
            property_data['value_high'] = data.get('value_high')
            
        if 'value_low' in data and data.get('value_low', 0) > 0:
            property_data['value_low'] = data.get('value_low')
            
        # Days on market from analysis
        if 'days_on_market' in data and data.get('days_on_market', 0) > 0:
            property_data['days_on_market'] = data.get('days_on_market')
            
        # Divorce-specific factors (use realistic defaults if not provided)
        case_duration_months = 18  # Default Florida divorce duration
        court_deadline = 90  # Default court deadline
        
        # Extract actual case data if available from divorce analysis
        if 'divorce_signals' in data:
            divorce_signals = data.get('divorce_signals')
            case_duration_months = divorce_signals.get('case_duration_months', 18)
            court_deadline = divorce_signals.get('court_ordered_sale_deadline', 90)
            
            # Extract more divorce-specific factors
            if divorce_signals.get('children_involved'):
                property_data['children_involved'] = True
            if divorce_signals.get('contested_case'):
                property_data['contested_case'] = True
            if divorce_signals.get('forced_sale_timeline'):
                property_data['forced_sale'] = True
                
        # Add divorce-specific timeline factors
        property_data['case_duration_months'] = case_duration_months
        property_data['court_deadline'] = court_deadline
        
        # Calculate tax burden if we have both assessed value and tax amount
        assessed_value = property_data.get('assessed_value', 0)
        tax_amount = property_data.get('tax_amount', 0)
        if assessed_value > 0 and tax_amount > 0:
            tax_rate = (tax_amount / assessed_value) * 100
            property_data['tax_rate'] = tax_rate
            if tax_rate > 3.0:  # High tax burden
                property_data['high_tax_burden'] = True
                
        # Market timing factors
        if 'urgency' in data and data.get('urgency') == 'HIGH':
            property_data['urgent_sale'] = True
            
        # Property type specific risks
        property_type = property_data.get('property_type', '').lower()
        if 'condo' in property_type:
            property_data['condo_risk'] = True
        elif 'commercial' in property_type:
            property_data['commercial_property'] = True
        elif 'mobile' in property_type or 'manufactured' in property_type:
            property_data['mobile_home_risk'] = True
                
        # Market conditions from ZIP analysis
        address = data.get('address', '')
        zip_match = re.search(r'\b(\d{5})\b', address)
        if zip_match:
            zip_code = zip_match.group(1)
            # Add market-specific factors based on ZIP
            high_stress_zips = ['33467', '33460', '33418']  # Lake Worth, PB Gardens
            if zip_code in high_stress_zips:
                property_data['difficult_market'] = True
                
        # Price depreciation analysis
        current_value = property_data.get('current_value', 0)
        last_sale_price = property_data.get('last_sale_price', 0)
        if current_value > 0 and last_sale_price > 0:
            value_change = ((current_value - last_sale_price) / last_sale_price) * 100
            property_data['value_change'] = value_change
            if value_change < -5:  # Value declined more than 5%
                property_data['declining_value'] = True
        
        explanation = generate_distress_explanation(distress_score, risk_factors, property_data)
        
        cursor.execute('''
            INSERT INTO properties 
            (address, distress_score, risk_factors, analysis_type, source_file, case_id, 
             party_name, distress_explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('address'),
            data.get('distress_score'),
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

def generate_distress_explanation(distress_score, risk_factors, property_data=None):
    """Generate concise explanation based on real property data and distress factors"""
    
    # Extract real metrics from property data if available
    factors = []
    
    # Add property-specific metrics from ATTOM API
    if property_data:
        value = property_data.get('current_value', 0)
        if value > 0:
            if value > 500000:
                factors.append(f"${value:,} high-value property")
            elif value > 300000:
                factors.append(f"${value:,} mid-market property")
            else:
                factors.append(f"${value:,} affordable property")
        
        # Property size and characteristics
        bedrooms = property_data.get('bedrooms', 0)
        bathrooms = property_data.get('bathrooms', 0)
        building_size = property_data.get('building_size', 0)
        
        if bedrooms > 0 or bathrooms > 0:
            if bedrooms >= 4 and bathrooms >= 3:
                factors.append(f"{bedrooms}BR/{bathrooms}BA family home")
            elif bedrooms >= 2:
                factors.append(f"{bedrooms}BR/{bathrooms}BA property")
        elif building_size > 0:
            if building_size > 3000:
                factors.append(f"{building_size:,} sqft large home")
            elif building_size > 2000:
                factors.append(f"{building_size:,} sqft home")
        
        # Property condition and age factors
        year_built = property_data.get('year_built', 0)
        if year_built > 0:
            property_age = 2024 - year_built
            if property_age > 50:
                factors.append(f"{property_age}-year vintage property")
            elif property_age > 30:
                factors.append(f"{property_age}-year established property")
            elif property_age < 10:
                factors.append(f"{property_age}-year newer construction")
        
        # Value change analysis
        value_change = property_data.get('value_change', 0)
        price_appreciation = property_data.get('price_appreciation', 0)
        
        if property_data.get('declining_value'):
            factors.append(f"{abs(value_change):.1f}% value decline")
        elif value_change < -2:
            factors.append(f"{abs(value_change):.1f}% depreciation")
        elif price_appreciation < -10:
            factors.append(f"{abs(price_appreciation):.1f}% price drop")
            
        # Sales history patterns
        sales_count = property_data.get('sales_history_count', 0)
        if sales_count > 3:
            factors.append(f"{sales_count} recent sales")
        elif sales_count > 1:
            last_sale_date = property_data.get('last_sale_date', '')
            if '2023' in last_sale_date or '2024' in last_sale_date:
                factors.append("recent sale activity")
        
        # Tax and financial burden factors
        tax_rate = property_data.get('tax_rate', 0)
        tax_amount = property_data.get('tax_amount', 0)
        tax_liens = property_data.get('tax_liens', 0)
        
        if property_data.get('high_tax_burden') or tax_rate > 3.0:
            factors.append(f"{tax_rate:.1f}% tax rate")
        elif tax_amount > 10000:
            factors.append(f"${tax_amount:,} annual taxes")
        elif tax_liens > 10000:
            factors.append(f"${tax_liens:,} tax burden")
        elif tax_liens > 5000:
            factors.append(f"${tax_liens:,} tax obligations")
        elif tax_liens > 0:
            factors.append(f"${tax_liens:,} tax liens")
            
        # Divorce-specific timing pressure
        court_deadline = property_data.get('court_deadline', 0)
        if court_deadline > 0 and court_deadline < 60:
            factors.append(f"{court_deadline}-day urgent deadline")
        elif court_deadline > 0 and court_deadline < 120:
            factors.append(f"{court_deadline}-day court deadline")
        
        case_duration = property_data.get('case_duration_months', 0)
        if case_duration > 24:
            factors.append(f"{case_duration}-month prolonged case")
        elif case_duration > 12:
            factors.append(f"{case_duration}-month case duration")
            
        # Divorce complexity factors
        if property_data.get('children_involved'):
            factors.append("children involved")
        if property_data.get('contested_case'):
            factors.append("contested proceedings")
        if property_data.get('forced_sale'):
            factors.append("court-ordered sale")
        
        # Property type risks
        if property_data.get('condo_risk'):
            factors.append("condo association risks")
        elif property_data.get('commercial_property'):
            factors.append("commercial property complexity")
        elif property_data.get('mobile_home_risk'):
            factors.append("mobile home factors")
            
        # Market conditions
        if property_data.get('difficult_market'):
            factors.append("challenging market conditions")
        elif property_data.get('urgent_sale'):
            factors.append("urgent sale timeline")
            
        # Days on market
        days_on_market = property_data.get('days_on_market', 0)
        if days_on_market > 120:
            factors.append(f"{days_on_market} days unsold")
        elif days_on_market > 60:
            factors.append(f"{days_on_market} days on market")
        
        # Valuation uncertainty
        confidence_score = property_data.get('confidence_score', 0)
        value_high = property_data.get('value_high', 0)
        value_low = property_data.get('value_low', 0)
        
        if confidence_score > 0 and confidence_score < 70:
            factors.append("valuation uncertainty")
        elif value_high > 0 and value_low > 0 and value:
            value_range = ((value_high - value_low) / value) * 100
            if value_range > 20:
                factors.append("wide value range")
        
        # Owner occupancy status
        if property_data.get('owner_occupied') == False:
            factors.append("absentee owner")
        elif property_data.get('owner_name'):
            factors.append("owner-occupied property")
    
    # Process risk factors more intelligently
    key_factors = []
    processed_factors = set()  # Avoid duplicates
    
    for factor in risk_factors[:4]:  # Top 4 factors
        factor_lower = factor.lower()
        
        # Skip if we already processed a similar factor
        if any(processed in factor_lower for processed in processed_factors):
            continue
            
        if "court-ordered" in factor_lower:
            key_factors.append("court-ordered sale")
            processed_factors.add("court")
        elif "dual mortgage" in factor_lower:
            key_factors.append("dual mortgage obligations")
            processed_factors.add("mortgage")
        elif "contested" in factor_lower:
            key_factors.append("contested divorce")
            processed_factors.add("contested")
        elif "child support" in factor_lower:
            key_factors.append("child support obligations")
            processed_factors.add("child")
        elif "extended" in factor_lower and "case" in factor_lower:
            key_factors.append("extended legal proceedings")
            processed_factors.add("extended")
        elif "legal fee" in factor_lower or "high legal" in factor_lower:
            key_factors.append("substantial legal fees")
            processed_factors.add("legal")
        elif "declining" in factor_lower and "value" in factor_lower:
            key_factors.append("declining property value")
            processed_factors.add("declining")
        elif "tax" in factor_lower and ("delinquent" in factor_lower or "burden" in factor_lower):
            key_factors.append("tax payment issues")
            processed_factors.add("tax")
        elif "buyer" in factor_lower and "market" in factor_lower:
            key_factors.append("buyer's market")
            processed_factors.add("market")
        elif "underwater" in factor_lower:
            key_factors.append("underwater mortgage")
            processed_factors.add("underwater")
        elif "older property" in factor_lower or "aging" in factor_lower:
            key_factors.append("aging property concerns")
            processed_factors.add("aging")
        elif "high-value" in factor_lower:
            key_factors.append("high-value complexity")
            processed_factors.add("value")
        elif "urgent" in factor_lower or "deadline" in factor_lower:
            key_factors.append("urgent timeline")
            processed_factors.add("urgent")
        elif "turnover" in factor_lower:
            key_factors.append("property instability")
            processed_factors.add("turnover")
        elif "seasonal" in factor_lower:
            key_factors.append("seasonal market challenges")
            processed_factors.add("seasonal")
    
    # Combine property metrics with key factors, prioritizing property-specific data
    all_factors = factors + key_factors
    
    # Create more varied explanation based on distress level
    if distress_score >= 85:
        explanation = f"CRITICAL opportunity from {', '.join(all_factors[:4])}."
    elif distress_score >= 70:
        explanation = f"HIGH potential from {', '.join(all_factors[:4])}."
    elif distress_score >= 55:
        explanation = f"MODERATE discount from {', '.join(all_factors[:3])}."
    elif all_factors:
        explanation = f"discount from {', '.join(all_factors[:3])}."
    else:
        explanation = f"potential based on divorce proceedings."
    
    return explanation

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
        from calculate_distress_score import calculateDistressScore
        result = calculateDistressScore(attom_data)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        import traceback
        app.logger.error(f"Distress error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5001))
        run_simple('127.0.0.1', port, app, use_debugger=True, use_reloader=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(traceback.format_exc()) 

