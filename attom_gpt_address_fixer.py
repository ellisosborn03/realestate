import os
import re
import csv
import time
import requests
import openai
import pandas as pd
from typing import List
import sys

# --- CONFIG: Paste your OpenAI API key here if you don't want to use an environment variable ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# If you want to hardcode your key, paste it below (uncomment the next line):
OPENAI_API_KEY = "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"

ATTOM_API_KEY = "ad91f2f30426f1ee54aec35791aaa044"
ATTOM_URL = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"

# --- Address variant generation ---
def strip_unit(address):
    return re.sub(r'\b(UNIT|APT|LOT|STE|SUITE|#)\s*[A-Z0-9\-]+$', '', address, flags=re.IGNORECASE).strip().rstrip(',')

def usps_suffix_variants(address):
    # Try both long and short forms
    usps_map = [
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
    variants = set()
    for pattern, repl in usps_map:
        alt = re.sub(pattern, repl, address, flags=re.IGNORECASE)
        if alt != address:
            variants.add(alt)
    return list(variants)

def gpt_address_variants(address, address2, n=5):
    if not OPENAI_API_KEY:
        return []
    openai.api_key = OPENAI_API_KEY
    prompt = f"""
Given the US address '{address}' in '{address2}', generate {n} alternative ways it might appear in real estate or property records, including common abbreviations, alternate spellings, or formatting. Only output the address lines, one per line, no commentary.
"""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=128,
            temperature=0.7,
        )
        lines = resp.choices[0].message.content.strip().split('\n')
        return [l.strip() for l in lines if l.strip()]
    except Exception as e:
        print(f"[GPT ERROR] {e}")
        return []

def attom_query(address1, address2):
    params = {'address1': address1, 'address2': address2}
    headers = {'accept': 'application/json', 'apikey': ATTOM_API_KEY}
    try:
        print(f"  [TRY] {address1}, {address2}", flush=True)
        resp = requests.get(ATTOM_URL, params=params, headers=headers, timeout=10)
        print(f"    [ATTOM STATUS] {resp.status_code}", flush=True)
        print(f"    [ATTOM BODY] {resp.text[:200]}...", flush=True)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status', {}).get('code') == 0 and data.get('property'):
            prop = data['property'][0]
            value = prop.get('avm', {}).get('amount', {}).get('value', None)
            if value:
                return value, prop.get('address', {}).get('oneLine', address1)
        return None, None
    except Exception as e:
        print(f"    [ATTOM ERROR] {e}", flush=True)
        return None, None

def try_all_variants(address1, address2):
    tried = set()
    for variant in [address1, strip_unit(address1)] + usps_suffix_variants(address1):
        if not variant or variant in tried:
            continue
        tried.add(variant)
        val, used = attom_query(variant, address2)
        if val:
            return val, used, variant, 'success'
    print("  [GPT] Generating variants...", flush=True)
    gpt_variants = gpt_address_variants(address1, address2)
    for variant in gpt_variants:
        if not variant or variant in tried:
            continue
        tried.add(variant)
        val, used = attom_query(variant, address2)
        if val:
            return val, used, variant, 'gpt-success'
    return None, None, None, 'fail'

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Brute-force ATTOM AVM for addresses with GPT assist')
    parser.add_argument('--input', required=True, help='Input CSV with columns: address1,address2')
    parser.add_argument('--output', required=True, help='Output CSV')
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    results = []
    for idx, row in df.iterrows():
        address1 = str(row['address1']).strip()
        address2 = str(row['address2']).strip()
        print(f"[{idx+1}/{len(df)}] {address1}, {address2}")
        val, used, variant, status = try_all_variants(address1, address2)
        results.append({
            'original_address1': address1,
            'address2': address2,
            'variant_used': variant,
            'attom_oneLine': used,
            'valuation': val if val else 'N/A',
            'status': status
        })
        time.sleep(0.5)  # avoid hammering API
    pd.DataFrame(results).to_csv(args.output, index=False)
    print(f"Done. Results written to {args.output}")

if __name__ == "__main__":
    main() 