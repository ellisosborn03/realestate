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

def clean_address1(address1):
    # Removes trailing punctuation, repeated commas, and replaces '&'
    return address1.strip().replace(',,', ',').rstrip(',').replace('&', 'and').replace(' .', '').replace('.', '')

def is_valid_florida_address(address2):
    # Ensures format is like: "PALM BEACH GARDENS, FL 33418"
    return bool(re.match(r'^([A-Z\s]+),\s?FL\s\d{5}$', address2.upper()))

@app.route('/cross-reference', methods=['POST'])
def cross_reference():
    logging.info('Received cross-reference request')
    try:
        data = request.json
        if not data or not isinstance(data, list):
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400

        results = []
        for row in data:
            raw_address1 = row.get('street address') or row.get('Street Address') or ''
            raw_address2 = row.get('CSZ', '')
            logging.info(f"Original row: {row}")
            address1 = clean_address1(raw_address1)
            address2 = raw_address2.strip().upper().replace(' ,', ',').replace('  ', ' ')
            logging.info(f"Cleaned address1: '{address1}', address2: '{address2}'")

            if not address1 or not address2:
                logger.warning(f"Missing address1 or address2 after cleaning. address1: '{address1}', address2: '{address2}'")
                results.append({'address': address1, 'Valuation': 'N/A'})
                continue

            if not is_valid_florida_address(address2):
                logger.warning(f"Invalid FL address format: {address2}")
                results.append({'address': f"{address1}, {address2}", 'Valuation': 'N/A'})
                continue

            logging.info(f"Querying ATTOM for: address1={address1}, address2={address2}")
            for handler in logging.root.handlers:
                handler.flush()
            params = {
                "address1": address1,
                "address2": address2
            }
            url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
            headers = {
                "apikey": "ad91f2f30426f1ee54aec35791aaa044",
                "accept": "application/json"
            }
            resp = requests.get(url, headers=headers, params=params)
            data = resp.json()
            logging.info(f"ATTOM API response status: {resp.status_code}, body: {data}")
            if data.get("status", {}).get("msg") == "SuccessWithoutResult" or not data.get("property"):
                logger.warning(f"No AVM result for: {address1}, {address2}")
                results.append({'address': f"{address1}, {address2}", 'Valuation': 'N/A'})
                continue
            if resp.status_code == 200:
                prop = (data.get("property") or [{}])[0]
                avm = prop.get("avm", {})
                value = avm.get("amount", {}).get("value", None)
                logging.info(f"ATTOM AVM for {address1}, {address2}: {avm}")
                logging.info(f"Extracted value: {value}")
                for handler in logging.root.handlers:
                    handler.flush()
                results.append({
                    'address': f"{address1}, {address2}",
                    'Valuation': value if value is not None else 'N/A'
                })
            else:
                logging.error(f'ATTOM API error for address {address1}: {resp.status_code} {resp.text}')
                for handler in logging.root.handlers:
                    handler.flush()
                results.append({
                    'address': f"{address1}, {address2}",
                    'Valuation': 'N/A'
                })
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        logging.error(f'Error in cross-reference: {e}')
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # Use werkzeug's run_simple for better stability
        run_simple('127.0.0.1', 5001, app, use_debugger=True, use_reloader=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(traceback.format_exc()) 

