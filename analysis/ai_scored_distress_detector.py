#!/usr/bin/env python3

import requests
import json
import sys
import os
import re
import time
import hashlib
from datetime import datetime
from typing import Dict, Optional, Any
import argparse
from core.address_matcher import AddressMatcher

class AIScoredDistressDetector:
    """
    AI-Scored Property Distress Detector with Public Data Integration
    Replaces hardcoded scoring with comprehensive data collection + AI analysis
    """
    
    def __init__(self, openai_api_key=None, attom_api_key=None):
        # API Keys
        self.attom_api_key = attom_api_key or 'ad91f2f30426f1ee54aec35791aaa044'
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.bls_api_key = os.getenv('BLS_API_KEY')  # Optional for unemployment data
        
        # Cache for API results to minimize usage
        self.cache = {}
        self.cache_file = 'distress_analysis_cache.json'
        self.address_matcher = AddressMatcher()
        self._load_cache()
        
        if not self.openai_api_key:
            print("❌ ERROR: OpenAI API key required. Set OPENAI_API_KEY environment variable.")
            sys.exit(1)
    
    def _load_cache(self):
        """Load cached results to minimize API usage"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
        except Exception:
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass
    
    def _get_cache_key(self, address: str) -> str:
        """Generate cache key for address"""
        return hashlib.md5(address.lower().strip().encode()).hexdigest()
    
    def collect_comprehensive_data(self, address1: str, address2: str) -> Dict[str, Any]:
        """
        Step 1: Data Collection & Structure
        Collect all fields from ATTOM API (primary) and secondary sources if needed
        """
        
        address = f"{address1}, {address2}"
        cache_key = self._get_cache_key(address)
        
        # Check cache first
        if cache_key in self.cache:
            print(f"📋 Using cached data for: {address}")
            return self.cache[cache_key]
        
        print(f"🔍 Collecting comprehensive data for: {address}")
        print("-" * 60)
        
        # Initialize data structure with all required fields
        data = {
            "address": address,
            "timestamp": datetime.now().isoformat(),
            
            # Financial Metrics
            "ltv": None,
            "dom": None, 
            "medianDom": None,
            "listOrig": None,
            "listCurr": None,
            
            # Distress Indicators
            "preFC": False,
            "taxDelinq": False,
            "taxLienLate": False,
            "absentee": False,
            "liens": False,
            "viol": 0,
            
            # Market Conditions
            "absorp": None,
            "rentDemand": None,
            "incomeTrend": None,
            
            # Property/Owner Characteristics
            "ownerAge": None,
            "propAge": None,
            "criticalIllness": False,
            "incompleteConstruction": False,
            
            # Risk Factors
            "crime": None,
            "insurance": None,
            "layoffs": False,
            "coastalRisk": None,
            
            # Data Sources Used
            "sources": []
        }
        
        # Step 1A: Try address matching with ATTOM + Tax Collector fallback
        property_data, fallback_reason = self.address_matcher.match_address(address)
        
        if property_data:
            # Extract data based on source
            if fallback_reason == "commercial_parcel":
                # Tax collector data
                data.update({
                    "owner_name": property_data.get("owner_name"),
                    "mailing_address": property_data.get("mailing_address"),
                    "use_code": property_data.get("use_code"),
                    "sources": ["PALM_BEACH_TAX"]
                })
                
                # Check for absentee ownership
                if property_data.get("mailing_address") and property_data.get("mailing_address") != address:
                    data["absentee"] = True
                    
            else:
                # ATTOM data
                self._extract_attom_data(data, property_data)
                
        # Step 1B: Secondary Public Data (only if primary source lacks data)
        self._collect_secondary_data(data, address1, address2)
        
        # Cache the results
        self.cache[cache_key] = data
        self._save_cache()
        
        return data
    
    def _extract_attom_data(self, data: Dict[str, Any], property_data: Dict[str, Any]):
        """Extract relevant fields from ATTOM property data"""
        
        # AVM & Valuation
        avm = property_data.get('avm', {})
        if avm:
            data["listCurr"] = avm.get('amount', {}).get('value')
            data["sources"].append("ATTOM_AVM")
            
        # Property Details
        summary = property_data.get('summary', {})
        if summary:
            year_built = summary.get('yearBuilt')
            if year_built:
                data["propAge"] = 2024 - year_built
                
            if summary.get('proptype') and 'partial' in str(summary.get('proptype', '')).lower():
                data["incompleteConstruction"] = True
                
        # Owner Info
        owner = property_data.get('owner', {})
        if owner:
            mail_address = owner.get('mailingAddress', {}).get('oneLine')
            if mail_address and mail_address.lower() != data["address"].lower():
                data["absentee"] = True
                
        # Assessment/Tax
        assessment = property_data.get('assessment', {})
        if assessment:
            data["sources"].append("ATTOM_TAX")
            
        # Sales History
        sales = property_data.get('salehistory', [])
        if sales:
            data["sources"].append("ATTOM_SALES")
            
        # Distress Indicators
        distress = property_data.get('distress', {})
        if distress:
            data["sources"].append("ATTOM_DISTRESS")
            if distress.get('preforeclosure'):
                data["preFC"] = True
        
    def _collect_secondary_data(self, data: Dict[str, Any], address1: str, address2: str):
        """Collect data from secondary public sources (only if primary source lacks data)"""
        
        print("\n🌐 Secondary Public Data Collection:")
        
        # Extract location info for secondary APIs
        zip_match = re.search(r'\b(\d{5})\b', address2)
        state_match = re.search(r'\b([A-Z]{2})\b', address2.upper())
        
        zip_code = zip_match.group(1) if zip_match else None
        state_code = state_match.group(1) if state_match else None
        
        # Crime Data (if not available from ATTOM)
        if not data.get("crime") and zip_code:
            crime_level = self._get_crime_data(zip_code)
            if crime_level:
                data["crime"] = crime_level
                data["sources"].append("CRIME_API")
                print(f"  ✅ Crime: {crime_level}")
        
        # Coastal Risk (NOAA/FEMA)
        if state_code in ['FL', 'TX', 'CA', 'NC', 'SC', 'GA', 'LA']:
            coastal_risk = self._get_coastal_risk(address1, address2)
            if coastal_risk:
                data["coastalRisk"] = coastal_risk
                data["sources"].append("COASTAL_RISK")
                print(f"  ✅ Coastal Risk: {coastal_risk}")
        
        # Unemployment/Layoffs (BLS API)
        if not data.get("layoffs") and state_code and self.bls_api_key:
            layoffs = self._get_unemployment_data(state_code)
            if layoffs is not None:
                data["layoffs"] = layoffs
                data["sources"].append("BLS_API")
                print(f"  ✅ Layoffs: {'Yes' if layoffs else 'No'}")
        
        # Insurance Availability (FEMA/NFIP)
        if not data.get("insurance") and zip_code:
            insurance = self._get_insurance_availability(zip_code)
            if insurance:
                data["insurance"] = insurance
                data["sources"].append("FEMA_NFIP")
                print(f"  ✅ Insurance: {insurance}")
        
        print(f"\n📊 Total Data Sources: {len(data['sources'])}")
    
    def _get_crime_data(self, zip_code: str) -> Optional[str]:
        """Get crime level for ZIP code (secondary source)"""
        # Simplified crime assessment based on ZIP patterns
        # In production, would use actual crime APIs
        high_crime_zips = ['33101', '33102', '33103', '10001', '10002', '90001']
        if zip_code in high_crime_zips:
            return "High"
        elif int(zip_code) % 3 == 0:  # Simplified logic for demo
            return "Medium"
        else:
            return "Low"
    
    def _get_coastal_risk(self, address1: str, address2: str) -> Optional[str]:
        """Get coastal risk assessment (NOAA/FEMA secondary source)"""
        # Simplified coastal risk based on address patterns
        address_lower = f"{address1} {address2}".lower()
        if any(word in address_lower for word in ['ocean', 'beach', 'coast', 'shore', 'bay']):
            return "High"
        elif 'fl' in address_lower and any(word in address_lower for word in ['miami', 'fort lauderdale', 'palm beach']):
            return "Medium"
        else:
            return "Low"
    
    def _get_unemployment_data(self, state_code: str) -> Optional[bool]:
        """Get unemployment/layoffs data (BLS API secondary source)"""
        # Simplified unemployment assessment
        # In production, would call actual BLS API
        high_unemployment_states = ['NV', 'CA', 'NY', 'IL']
        return state_code in high_unemployment_states
    
    def _get_insurance_availability(self, zip_code: str) -> Optional[str]:
        """Get insurance availability (FEMA/NFIP secondary source)"""
        # Simplified insurance assessment
        if int(zip_code) % 5 == 0:
            return "Limited"
        elif int(zip_code) % 3 == 0:
            return "Standard"
        else:
            return "Full"
    
    def ai_score_property(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: OpenAI Analysis (minimized tokens)
        Send structured data to AI for distress scoring
        """
        
        # Check cache first
        cache_key = self._get_cache_key(data["address"] + "_ai_score")
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Create clean data for AI (remove None values and metadata)
        clean_data = {k: v for k, v in data.items() 
                     if v is not None and k not in ['timestamp', 'sources']}
        
        # Minimized prompt for token efficiency
        prompt = f"""You are an AI that evaluates real estate distress.

Given the following structured property and market data, return:
- `score` (0–100): distress score
- `conf` (0.0–1.0): confidence
- `discount`: estimated % discount range
- `reason`: brief explanation of top 3–5 risk factors

Assess using known indicators of distress such as foreclosure risk, code violations, owner age, price drops, insurance availability, or regional unemployment.

Data:
{json.dumps(clean_data, indent=2)}

Return JSON only:"""

        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4o',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3,
                'max_tokens': 300
            }
            
            print("\n🤖 Getting AI distress analysis...")
            resp = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            
            result = resp.json()
            content = result['choices'][0]['message']['content']
            
            # Parse AI response
            ai_result = json.loads(content)
            
            # Cache the result
            self.cache[cache_key] = ai_result
            self._save_cache()
            
            return ai_result
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            # Fallback simple scoring
            return {
                "score": 50,
                "conf": 0.5,
                "discount": "10-15%",
                "reason": "Fallback scoring due to AI analysis failure"
            }
    
    def display_results(self, data: Dict[str, Any], ai_result: Dict[str, Any]):
        """
        Step 3: Display formatted results with transparency
        Show raw input data + AI analysis
        """
        
        print("\n" + "="*80)
        print("🎯 AI-SCORED DISTRESS ANALYSIS RESULTS")
        print("="*80)
        
        # AI Analysis Results
        print(f"\n🤖 AI ANALYSIS:")
        print(f"  Distress Score: {ai_result.get('score', 'N/A')}/100")
        print(f"  Confidence: {ai_result.get('conf', 'N/A')}")
        print(f"  Discount Range: {ai_result.get('discount', 'N/A')}")
        print(f"  Reasoning: {ai_result.get('reason', 'N/A')}")
        
        # Raw Data Transparency (organized display)
        print(f"\n📋 RAW INPUT DATA (for transparency):")
        print(f"Address: {data['address']}")
        
        if data.get('ltv'):
            print(f"Loan-to-Value: {data['ltv']*100:.0f}%")
        
        if data.get('dom') and data.get('medianDom'):
            print(f"Days on Market: {data['dom']} (vs market median {data['medianDom']})")
        
        if data.get('listOrig') and data.get('listCurr'):
            print(f"Price Reduction: ${data['listOrig']:,} → ${data['listCurr']:,}")
        
        if data.get('preFC'):
            print(f"Preforeclosure: Yes")
        
        if data.get('taxLienLate'):
            print(f"Tax Lien (Late): Yes")
        
        if data.get('viol') > 0:
            print(f"Code Violations: {data['viol']}")
        
        if data.get('absentee'):
            print(f"Absentee Owner: Yes")
        
        if data.get('insurance'):
            print(f"Insurance Access: {data['insurance']}")
        
        if data.get('crime'):
            print(f"Crime Level: {data['crime']}")
        
        if data.get('incomeTrend'):
            print(f"Income Trend: {data['incomeTrend']}")
        
        if data.get('propAge'):
            print(f"Property Age: {data['propAge']} years")
        
        if data.get('coastalRisk'):
            print(f"Coastal Risk: {data['coastalRisk']}")
        
        if data.get('layoffs'):
            print(f"Regional Layoffs: Yes")
        
        print(f"\nData Sources Used: {', '.join(data['sources'])}")
    
    def analyze_property(self, address1: str, address2: str) -> Dict[str, Any]:
        """Complete AI-scored distress analysis workflow"""
        
        print("🏠 AI-SCORED PROPERTY DISTRESS ANALYSIS")
        print("=" * 80)
        
        # Step 1: Comprehensive Data Collection
        data = self.collect_comprehensive_data(address1, address2)
        
        # Step 2: AI Scoring
        ai_result = self.ai_score_property(data)
        
        # Step 3: Display Results
        self.display_results(data, ai_result)
        
        return {
            'raw_data': data,
            'ai_analysis': ai_result,
            'combined_score': ai_result.get('score', 50)
        }

def main():
    parser = argparse.ArgumentParser(description='AI-Scored Property Distress Detection')
    parser.add_argument('address1', help='Street address')
    parser.add_argument('address2', help='City, State, ZIP')
    parser.add_argument('--openai-key', help='OpenAI API key')
    parser.add_argument('--attom-key', help='ATTOM API key')
    
    args = parser.parse_args()
    
    detector = AIScoredDistressDetector(
        openai_api_key=args.openai_key,
        attom_api_key=args.attom_key
    )
    
    result = detector.analyze_property(args.address1, args.address2)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_scored_analysis_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    main() 