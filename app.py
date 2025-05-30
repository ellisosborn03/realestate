import os
import logging
import traceback
import requests
from flask import Flask, request, render_template, jsonify
import pandas as pd
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

logging.basicConfig(level=logging.DEBUG)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
        if 'file' not in request.files:
            logging.error('No file part in request')
            return jsonify({'success': False, 'error': 'No file part'}), 400
        file = request.files['file']
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
        return jsonify({'success': True, 'data': cleaned_data})
    except Exception as e:
        logging.error(f'Error processing file: {e}')
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/cross-reference', methods=['POST'])
def cross_reference():
    logging.info('Received cross-reference request')
    try:
        data = request.json
        if not data or not isinstance(data, list):
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400

        results = []
        for row in data:
            logging.info(f"Row: {row}")
            for handler in logging.root.handlers:
                handler.flush()
            street = row.get('street address', '').strip()
            csz = row.get('CSZ', '').strip()
            if not street or not csz or csz == ',' or csz == '':
                results.append({'address': street, 'Valuation': 'N/A'})
                continue
            try:
                city_state_zip = csz.split(',')
                city = city_state_zip[0].strip()
                state_zip = city_state_zip[1].strip().split(' ')
                state = state_zip[0]
                zip_code = state_zip[1]
                address1 = street
                address2 = f"{city}, {state} {zip_code}"
            except Exception:
                results.append({'address': street, 'Valuation': 'N/A'})
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
            if resp.status_code == 200:
                data = resp.json()
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
    app.run(debug=True, port=5001) 

