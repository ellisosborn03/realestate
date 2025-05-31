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

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    Always strip trailing LOT, UNIT, or APT suffixes and their values.
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
    # Always strip trailing LOT/UNIT/APT and value
    address = re.sub(r'\b(UNIT|APT|LOT)\s*[A-Z0-9#\-]+$', '', address).strip().rstrip(',')
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

            response = query_attom_avm(address1, address2)
            logging.info(f"ATTOM response: {response}")
            one_line = address1 + ', ' + address2
            value = 'N/A'
            if response and response.get('status', {}).get('code') == 0 and response.get('status', {}).get('msg') == 'SuccessWithResult':
                prop = response.get('property', [{}])[0]
                one_line = prop.get('address', {}).get('oneLine', one_line)
                value = prop.get('avm', {}).get('amount', {}).get('value', 'N/A')
            elif response and (response.get('status', {}).get('code') == 400 or response.get('status', {}).get('msg') == 'SuccessWithoutResult' or not response.get('property')):
                value = 'N/A'
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
        # Query ATTOM
        response = query_attom_avm(address1, address2)
        logging.info(f"ATTOM response: {response}")
        # Default values
        one_line = address1 + ', ' + address2
        value = 'N/A'
        if response and response.get('status', {}).get('code') == 0 and response.get('status', {}).get('msg') == 'SuccessWithResult':
            prop = response.get('property', [{}])[0]
            one_line = prop.get('address', {}).get('oneLine', one_line)
            value = prop.get('avm', {}).get('amount', {}).get('value', 'N/A')
        # Only N/A if 400/SuccessWithoutResult or property is empty
        elif response and (response.get('status', {}).get('code') == 400 or response.get('status', {}).get('msg') == 'SuccessWithoutResult' or not response.get('property')):
            value = 'N/A'
        logging.info(f"Returning: {one_line} -> {value}")
        return jsonify({'success': True, 'data': {'Valuation': value, 'Address': one_line}})
    except Exception as e:
        logging.exception('cross-reference-single: Exception')
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # Always run on port 5001 for local dev
        run_simple('127.0.0.1', 5001, app, use_debugger=True, use_reloader=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(traceback.format_exc()) 

