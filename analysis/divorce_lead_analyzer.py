#!/usr/bin/env python3

import requests
import json
import time
import re
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append('src')
sys.path.append('src/services')

load_dotenv()

ATTOM_API_KEY = "ad91f2f30426f1ee54aec35791aaa044"

@dataclass
class DivorceDistressSignals:
    """Divorce-specific distress signal data structure"""
    # Property basics
    address: str = ""
    property_value: float = 0
    property_type: str = ""
    year_built: int = 0
    
    # Divorce-specific indicators (AUTOMATIC HIGH DISTRESS)
    divorce_case_type: str = ""  # contested, uncontested, simplified
    children_involved: bool = False
    asset_value_estimate: float = 0
    case_duration_months: int = 0
    attorney_representation: bool = True
    
    # Financial stress multipliers for divorce
    dual_mortgage_likely: bool = False  # Both parties on mortgage
    forced_sale_timeline: bool = False  # Court ordered sale
    spousal_support_orders: bool = False
    child_support_obligations: bool = False
    legal_fee_burden: bool = False  # $10k+ in legal fees
    
    # Property-specific divorce factors
    marital_home: bool = True  # Primary residence vs investment
    equity_split_required: bool = True
    refinance_required: bool = False  # One spouse keeping home
    underwater_mortgage: bool = False
    
    # Market timing pressure
    court_ordered_sale_deadline: int = 0  # Days until forced sale
    market_conditions_favor_buyer: bool = False
    seasonal_timing_poor: bool = False  # Selling in slow season
    
    # Standard distress indicators
    days_on_market: int = 0
    price_reductions: int = 0
    building_age_risk: bool = False
    coastal_insurance_risk: bool = False
    market_absorption_rate: float = 0.18

class DivorceLeadAnalyzer:
    """Specialized AI analyzer for divorce real estate leads"""
    
    def __init__(self):
        self.attom_key = ATTOM_API_KEY
        self.session = requests.Session()
        
    def split_address(self, full_address: str) -> Tuple[str, str]:
        """Split full address for ATTOM API"""
        parts = full_address.rsplit(',', 2)
        
        if len(parts) >= 3:
            address1 = parts[0].strip()
            city_state_zip = f"{parts[1].strip()}, {parts[2].strip()}"
            return address1, city_state_zip
        elif len(parts) == 2:
            address1 = parts[0].strip()
            city_state_zip = parts[1].strip()
            return address1, city_state_zip
        else:
            return full_address, ""
    
    def get_property_data(self, address1: str, address2: str) -> Dict:
        """Get comprehensive ATTOM property data for distress analysis"""
        print("🏠 Fetching comprehensive property data...")
        
        headers = {"accept": "application/json", "apikey": self.attom_key}
        property_data = {}
        
        # 1. AVM endpoint for current value
        try:
            avm_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
            avm_params = {"address1": address1, "address2": address2}
            
            resp = self.session.get(avm_url, params=avm_params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status", {}).get("code") == 0:
                    properties = data.get("property", [])
                    if properties:
                        prop = properties[0]
                        avm_data = prop.get("avm", {}).get("amount", {})
                        property_data.update({
                            "current_value": avm_data.get("value", 0),
                            "value_high": avm_data.get("high", 0),
                            "value_low": avm_data.get("low", 0),
                            "confidence_score": prop.get("avm", {}).get("amount", {}).get("scr", 0),
                            "address": prop.get("address", {}).get("oneLine", ""),
                        })
        except Exception as e:
            print(f"    AVM Error: {e}")
        
        # 2. Property detail with mortgage info for liens/distress
        try:
            detail_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detailmortgage"
            detail_params = {"address1": address1, "address2": address2}
            
            resp = self.session.get(detail_url, params=detail_params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status", {}).get("code") == 0:
                    properties = data.get("property", [])
                    if properties:
                        prop = properties[0]
                        
                        # Building/property details
                        building = prop.get("building", {})
                        summary = prop.get("summary", {})
                        
                        property_data.update({
                            "year_built": summary.get("yearbuilt", 0),
                            "property_type": summary.get("proptype", ""),
                            "building_size": building.get("size", {}).get("universalsize", 0),
                            "lot_size": prop.get("lot", {}).get("lotsize1", 0),
                            "bedrooms": building.get("rooms", {}).get("beds", 0),
                            "bathrooms": building.get("rooms", {}).get("bathstotal", 0),
                        })
                        
                        # Assessment/tax data for liens
                        assessment = prop.get("assessment", {})
                        if assessment:
                            property_data.update({
                                "assessed_value": assessment.get("assessed", {}).get("assdttlvalue", 0),
                                "tax_amount": assessment.get("tax", {}).get("taxamt", 0),
                                "tax_year": assessment.get("tax", {}).get("taxyear", 0),
                            })
                        
                        # Owner information for absentee status
                        owner = prop.get("owner", {})
                        if owner:
                            property_data.update({
                                "owner_occupied": summary.get("absenteeInd", "").upper() == "OWNER OCCUPIED",
                                "owner_name": owner.get("owner1", {}).get("lastname", ""),
                            })
        except Exception as e:
            print(f"    Property Detail Error: {e}")
        
        # 3. Sales history for market activity and price trends
        try:
            sales_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/saleshistory/detail"
            sales_params = {"address1": address1, "address2": address2}
            
            resp = self.session.get(sales_url, params=sales_params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status", {}).get("code") == 0:
                    properties = data.get("property", [])
                    if properties:
                        prop = properties[0]
                        sales_history = prop.get("salehistory", [])
                        
                        if sales_history:
                            # Most recent sale
                            recent_sale = sales_history[0]
                            property_data.update({
                                "last_sale_date": recent_sale.get("saleTransDate", ""),
                                "last_sale_price": recent_sale.get("amount", {}).get("saleamt", 0),
                                "sales_history_count": len(sales_history),
                            })
                            
                            # Price trend analysis
                            if len(sales_history) >= 2:
                                older_sale = sales_history[1]
                                recent_price = recent_sale.get("amount", {}).get("saleamt", 0)
                                older_price = older_sale.get("amount", {}).get("saleamt", 0)
                                
                                if recent_price > 0 and older_price > 0:
                                    price_change = ((recent_price - older_price) / older_price) * 100
                                    property_data["price_appreciation"] = price_change
        except Exception as e:
            print(f"    Sales History Error: {e}")
        
        # 4. Check for foreclosure/distressed data
        try:
            # Some ATTOM endpoints may include foreclosure status in property details
            # This would require specific foreclosure API access
            property_data["foreclosure_status"] = "Unknown"  # Placeholder
        except Exception as e:
            print(f"    Foreclosure Check Error: {e}")
        
        return property_data
    
    def analyze_divorce_distress_factors(self, address: str, case_data: Dict = None) -> DivorceDistressSignals:
        """Analyze divorce-specific distress factors with AI inference"""
        print("💔 Analyzing divorce distress factors...")
        
        signals = DivorceDistressSignals()
        signals.address = address
        
        # If we have actual case data, use it
        if case_data:
            signals.divorce_case_type = case_data.get("case_type", "contested")
            signals.children_involved = case_data.get("children", False)
            signals.case_duration_months = case_data.get("duration_months", 12)
        else:
            # AI inference based on typical divorce patterns
            signals.divorce_case_type = "contested"  # Assume contested (70% of cases)
            signals.children_involved = True  # Assume children (60% of divorces)
            signals.case_duration_months = 18  # Average Florida divorce duration
        
        # Divorce financial stress factors (HIGH IMPACT)
        signals.dual_mortgage_likely = True  # Both spouses typically on mortgage
        signals.equity_split_required = True  # Always required in divorce
        signals.legal_fee_burden = True  # Average divorce costs $15k+ in FL
        
        if signals.children_involved:
            signals.child_support_obligations = True
            signals.spousal_support_orders = True  # Likely with children
        
        # Timing pressure factors
        if signals.case_duration_months > 12:
            signals.forced_sale_timeline = True  # Court pushing for resolution
            signals.court_ordered_sale_deadline = 90  # Typical deadline
        
        # Property-specific factors
        signals.marital_home = True  # Assume marital home
        signals.refinance_required = False  # Assume forced sale (easier/faster)
        
        return signals
    
    def calculate_divorce_distress_score(self, signals: DivorceDistressSignals, property_data: Dict) -> Dict:
        """Calculate divorce-specific distress score using new weighted system"""
        print("📊 Calculating enhanced divorce distress score...")

        # New risk factor table (no 'Active divorce proceedings')
        risk_factors = []
        weights = {
            'court_ordered_sale_timeline': 5,
            'dual_mortgage_obligations': 4,
            'high_legal_fee_burden': 4,
            'child_support_obligations': 3,
            'spousal_support_orders': 3,
            'contested_divorce_case': 3,
            'extended_case_duration_18mo': 3,
            'required_equity_split': 2,
            'high_value_property': 2,
            'buyers_market_conditions': 2,
            'urgent_sale_deadline_90d': 2,
            'seasonal_timing_challenges': 1,
            'property_over_30_years': 1,
            'flood_or_coastal_risk': 1,
        }
        # Map signals/property_data to risk factors
        triggered = []
        # 1. Court-ordered sale timeline
        if signals.forced_sale_timeline:
            triggered.append(('court_ordered_sale_timeline', weights['court_ordered_sale_timeline']))
            risk_factors.append('Court-ordered sale timeline')
        # 2. Dual mortgage obligations
        if signals.dual_mortgage_likely:
            triggered.append(('dual_mortgage_obligations', weights['dual_mortgage_obligations']))
            risk_factors.append('Dual mortgage obligations')
        # 3. High legal fee burden
        if signals.legal_fee_burden:
            triggered.append(('high_legal_fee_burden', weights['high_legal_fee_burden']))
            risk_factors.append('High legal fee burden ($15k+)')
        # 4. Child support obligations
        if signals.child_support_obligations:
            triggered.append(('child_support_obligations', weights['child_support_obligations']))
            risk_factors.append('Child support obligations')
        # 5. Spousal support orders
        if signals.spousal_support_orders:
            triggered.append(('spousal_support_orders', weights['spousal_support_orders']))
            risk_factors.append('Spousal support orders')
        # 6. Contested divorce case
        if signals.divorce_case_type == "contested":
            triggered.append(('contested_divorce_case', weights['contested_divorce_case']))
            risk_factors.append('Contested divorce case')
        # 7. Extended case duration (18 months)
        if signals.case_duration_months >= 18:
            triggered.append(('extended_case_duration_18mo', weights['extended_case_duration_18mo']))
            risk_factors.append('Extended case duration (18 months)')
        # 8. Required equity split
        if signals.equity_split_required:
            triggered.append(('required_equity_split', weights['required_equity_split']))
            risk_factors.append('Required equity split')
        # 9. High-value property (>$500k)
        property_value = property_data.get("current_value", 0)
        if property_value > 500000:
            triggered.append(('high_value_property', weights['high_value_property']))
            risk_factors.append('High-value property (>$500k)')
        # 10. Buyer's market conditions
        if signals.market_conditions_favor_buyer:
            triggered.append(('buyers_market_conditions', weights['buyers_market_conditions']))
            risk_factors.append("Buyer's market conditions")
        # 11. Urgent sale deadline (90 days)
        if 0 < signals.court_ordered_sale_deadline <= 90:
            triggered.append(('urgent_sale_deadline_90d', weights['urgent_sale_deadline_90d']))
            risk_factors.append('Urgent sale deadline (90 days)')
        # 12. Seasonal timing challenges
        if signals.seasonal_timing_poor:
            triggered.append(('seasonal_timing_challenges', weights['seasonal_timing_challenges']))
            risk_factors.append('Seasonal timing challenges')
        # 13. Property >30 years old
        year_built = property_data.get("year_built", 0)
        if year_built > 0:
            property_age = 2024 - year_built
            if property_age > 30:
                triggered.append(('property_over_30_years', weights['property_over_30_years']))
                risk_factors.append('Property >30 years old')
        # 14. Flood or coastal risk (use property_data['flood_or_coastal_risk'] or similar)
        if property_data.get('flood_or_coastal_risk', False):
            triggered.append(('flood_or_coastal_risk', weights['flood_or_coastal_risk']))
            risk_factors.append('Flood or coastal risk')
        # Calculate score
        total_weight = sum(weights.values())
        triggered_weight = sum(w for _, w in triggered)
        distress_score = round((triggered_weight / total_weight) * 100) if total_weight else 0
        # Debug
        print(f"[DEBUG] Triggered: {triggered}")
        print(f"[DEBUG] Score: {distress_score}/100")
        return {
            "distress_score": distress_score,
            "risk_factors": risk_factors,
            "confidence": 95,
            "property_value": property_value,
            "year_built": year_built,
        }
    
    def analyze_divorce_lead(self, address: str, case_data: Dict = None) -> Dict:
        """Complete divorce lead analysis"""
        print(f"\n💔 DIVORCE LEAD ANALYSIS: {address}")
        print("=" * 90)
        
        # Step 1: Parse address
        address1, address2 = self.split_address(address)
        if not address2:
            return {"error": "Could not parse address", "address": address}
        
        print(f"📍 Property: '{address1}' + '{address2}'")
        
        # Step 2: Get property valuation
        property_data = self.get_property_data(address1, address2)
        
        if property_data.get('current_value'):
            print(f"💰 Current Value: ${property_data['current_value']:,}")
            print(f"📍 Verified Address: {property_data.get('address', 'N/A')}")
        else:
            print("❌ No valuation data - using market estimates")
        
        # Step 3: Analyze divorce distress factors
        divorce_signals = self.analyze_divorce_distress_factors(address, case_data)
        
        # Step 4: Calculate distress score
        result = self.calculate_divorce_distress_score(divorce_signals, property_data)
        
        # Display results
        score = result["distress_score"]
        risk_factors = result["risk_factors"]
        
        print(f"\n📊 DIVORCE DISTRESS ANALYSIS:")
        print(f"   Distress Score: {score}/100")
        
        print(f"\n💔 DIVORCE-SPECIFIC FACTORS:")
        for factor in risk_factors:
            print(f"   • {factor}")
        
        return {
            "address": address,
            "distress_score": score,
            "risk_factors": risk_factors,
            "confidence": result['confidence'],
            "property_value": property_data.get('current_value', 0),
            "year_built": property_data.get('year_built', 0),
            "status": "success"
        }
    
    def process_divorce_excel(self, file_path: str, address_column: str = "Property Address") -> List[Dict]:
        """Process Excel file of divorce leads"""
        print(f"📊 Processing divorce leads from {file_path}...")
        
        try:
            df = pd.read_excel(file_path)
            print(f"Found {len(df)} leads in Excel file")
            
            results = []
            
            for index, row in df.iterrows():
                address = row.get(address_column, "")
                if not address:
                    continue
                
                print(f"\nProcessing lead {index + 1}/{len(df)}: {address}")
                
                # Extract any additional case data from Excel
                case_data = {
                    "children": row.get("Children", True),  # Default assume children
                    "case_type": row.get("Case Type", "contested"),
                    "duration_months": row.get("Duration Months", 12),
                }
                
                result = self.analyze_divorce_lead(address, case_data)
                results.append(result)
                
                time.sleep(0.5)  # Rate limiting
            
            return results
            
        except Exception as e:
            print(f"Error processing Excel file: {e}")
            return []

def main():
    """Test divorce lead analyzer"""
    print("💔 DIVORCE REAL ESTATE DISTRESS ANALYZER")
    print("=" * 90)
    print("Specialized AI analysis for divorce-related property leads\n")
    
    analyzer = DivorceLeadAnalyzer()
    
    # Test with known addresses plus divorce context
    test_leads = [
        {
            "address": "920 POPLAR DRIVE, LAKE PARK, FL 33403",
            "case_data": {"case_type": "contested", "children": True, "duration_months": 24}
        },
        {
            "address": "4704 COHUNE PALM DRIVE, GREENACRES, FL 33463", 
            "case_data": {"case_type": "uncontested", "children": False, "duration_months": 6}
        },
        {
            "address": "4520 PGA BLVD, PALM BEACH GARDENS, FL 33418",
            "case_data": {"case_type": "contested", "children": True, "duration_months": 30}
        },
        {
            "address": "8401 LAKE WORTH ROAD, LAKE WORTH, FL 33467",
            "case_data": {"case_type": "contested", "children": True, "duration_months": 18}
        },
    ]
    
    results = []
    risk_summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM-HIGH": 0, "MEDIUM": 0, "LOW": 0}
    total_discount_potential = 0
    
    for lead in test_leads:
        result = analyzer.analyze_divorce_lead(lead["address"], lead["case_data"])
        results.append(result)
        
        if result.get("risk_level"):
            risk_summary[result["risk_level"]] += 1
        
        # Extract discount potential for ROI calculation
        discount_str = result.get("discount_potential", "0-0%")
        avg_discount = sum(int(x.rstrip('%')) for x in discount_str.split('-')) / 2
        total_discount_potential += avg_discount
        
        time.sleep(1)
    
    # Summary report
    print(f"\n📋 DIVORCE LEAD ANALYSIS SUMMARY")
    print("=" * 90)
    print(f"Total leads analyzed: {len(test_leads)}")
    
    for level, count in risk_summary.items():
        if count > 0:
            emoji = {"CRITICAL": "🔴🚨", "HIGH": "🔴", "MEDIUM-HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[level]
            print(f"{emoji} {level} Risk: {count}")
    
    avg_discount = total_discount_potential / len(test_leads) if test_leads else 0
    print(f"💰 Average Discount Potential: {avg_discount:.1f}%")
    
    # High-priority leads
    high_priority = [r for r in results if r.get("distress_score", 0) >= 70]
    if high_priority:
        print(f"\n🎯 HIGH-PRIORITY DIVORCE LEADS:")
        for lead in high_priority:
            score = lead.get("distress_score", 0)
            discount = lead.get("discount_potential", "N/A")
            print(f"  Score {score}/100 | Discount: {discount}")
            print(f"    {lead['address']}")

if __name__ == "__main__":
    main() 