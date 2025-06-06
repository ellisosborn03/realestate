import os
import re
import requests
from typing import Dict, Optional, Tuple, List
from bs4 import BeautifulSoup
from urllib.parse import quote

class AddressMatcher:
    """Handles address matching with ATTOM API and Palm Beach Tax Collector fallback"""
    
    def __init__(self):
        self.attom_key = os.environ.get('ATTOM_API_KEY')
        if not self.attom_key:
            raise ValueError("ATTOM_API_KEY environment variable not set")
            
    def normalize_address(self, address: str) -> str:
        """Normalize address to USPS format"""
        if not address:
            return ""
        address = address.strip().upper()
        address = re.sub(r"\s{2,}", " ", address)            # Remove double spaces
        address = re.sub(r"\.\s*$", "", address)             # Remove trailing periods
        
        # Normalize unit/apartment/lot spacing
        address = re.sub(r"\bAPT(\d+)", r"APT \1", address)
        address = re.sub(r"\bUNIT(\s?)([A-Z0-9]+)", r"UNIT \2", address)
        address = re.sub(r"\bLOT(\s?)(\d+)", r"LOT \2", address)
        address = re.sub(r"\bSTE(\s?)([A-Z0-9]+)", r"STE \2", address)
        address = re.sub(r"\bSUITE(\s?)([A-Z0-9]+)", r"STE \2", address)
        address = re.sub(r"#(\s?)([A-Z0-9]+)", r"UNIT \2", address)
        
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
        
        return address.strip()

    def generate_address_variants(self, address: str) -> List[str]:
        """Generate address variants for better matching"""
        variants = [address]
        
        # Try without unit/suite numbers
        stripped = re.sub(r'\b(UNIT|APT|LOT|STE)\s*[A-Z0-9#\-]+$', '', address).strip().rstrip(',')
        if stripped != address:
            variants.append(stripped)
        
        # Try alternate suffixes
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

    def query_attom(self, address1: str, address2: str) -> Optional[Dict]:
        """Query ATTOM API for property data"""
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/basicprofile"
        params = {
            "address1": address1,
            "address2": address2
        }
        headers = {
            "accept": "application/json",
            "apikey": self.attom_key
        }
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('status', {}).get('code') == 0:
                return data.get('property', [{}])[0]
        except Exception as e:
            print(f"ATTOM API error: {e}")
            
        return None
        
    def query_palm_beach_tax(self, street_number: str, street_name: str) -> Optional[Dict]:
        """Query Palm Beach County Tax Collector site"""
        base_url = "https://pbctax.publicaccessnow.com/PropertyTax.aspx"
        params = {
            "s": f"Situsstreetnumber:{street_number}%20Situsstreetname:{quote(street_name)}",
            "pg": "1",
            "g": "4",
            "moduleId": "449"
        }
        
        try:
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            
            # Parse HTML response
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract data from first matching result
            result = {}
            
            # Find PCN (Parcel ID)
            pcn_elem = soup.find('span', string=re.compile(r'PCN:'))
            if pcn_elem:
                result['pcn'] = pcn_elem.text.split(':')[1].strip()
                
            # Find Situs Address
            situs_elem = soup.find('span', string=re.compile(r'Situs Address:'))
            if situs_elem:
                result['situs_address'] = situs_elem.text.split(':')[1].strip()
                
            # Find Owner Name
            owner_elem = soup.find('span', string=re.compile(r'Owner Name:'))
            if owner_elem:
                result['owner_name'] = owner_elem.text.split(':')[1].strip()
                
            # Find Mailing Address
            mail_elem = soup.find('span', string=re.compile(r'Mailing Address:'))
            if mail_elem:
                result['mailing_address'] = mail_elem.text.split(':')[1].strip()
                
            # Find Use Code
            use_elem = soup.find('span', string=re.compile(r'Use Code:'))
            if use_elem:
                result['use_code'] = use_elem.text.split(':')[1].strip()
                
            return result if result else None
            
        except Exception as e:
            print(f"Palm Beach Tax Collector error: {e}")
            return None
            
    def match_address(self, address1: str, address2: str) -> Dict:
        """Match address using ATTOM API with fallback to Palm Beach Tax Collector"""
        try:
            # Normalize addresses
            address1 = self.normalize_address(address1)
            address2 = self.normalize_address(address2)
            
            # Generate variants
            variants = self.generate_address_variants(address1)
            
            # Try ATTOM API with each variant
            for variant in variants:
                try:
                    response = self.query_attom(variant, address2)
                    if response and response.get('status', {}).get('code') == 0:
                        return response.get('property', [{}])[0]
                except Exception as e:
                    print(f"ATTOM API error: {e}")
                    continue
            
            # If ATTOM fails, try Palm Beach Tax Collector
            if "PALM BEACH" in address2.upper():
                try:
                    tax_data = self.query_palm_beach_tax(address1, address2)
                    if tax_data:
                        # Try ATTOM again with canonical address from tax collector
                        canonical_address = tax_data.get('situs_address')
                        if canonical_address:
                            try:
                                response = self.query_attom(canonical_address, address2)
                                if response and response.get('status', {}).get('code') == 0:
                                    return response.get('property', [{}])[0]
                            except Exception:
                                pass
                        return tax_data
                except Exception as e:
                    print(f"Tax collector error: {e}")
            
            return None
        except Exception as e:
            print(f"Error in match_address: {e}")
            return None 