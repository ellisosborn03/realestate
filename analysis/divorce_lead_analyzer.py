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
        """Calculate enhanced divorce-specific distress score with real data"""
        print("📊 Calculating enhanced divorce distress score...")
        
        score = 25  # Base score for any divorce case
        risk_factors = ["Active divorce proceedings"]
        
        # DIVORCE-SPECIFIC HIGH IMPACT FACTORS (50% of total score)
        
        # Forced sale scenarios (20 points)
        if signals.forced_sale_timeline:
            score += 20
            risk_factors.append("Court-ordered sale timeline")
        
        # Financial pressure multipliers (15 points)
        if signals.dual_mortgage_likely:
            score += 8
            risk_factors.append("Dual mortgage obligations")
        
        if signals.legal_fee_burden:
            score += 7
            risk_factors.append("High legal fee burden ($15k+)")
        
        # Child/spousal support obligations (15 points)
        if signals.child_support_obligations:
            score += 8
            risk_factors.append("Child support obligations")
        
        if signals.spousal_support_orders:
            score += 7
            risk_factors.append("Spousal support orders")
        
        # Case complexity factors (10 points)
        if signals.divorce_case_type == "contested":
            score += 6
            risk_factors.append("Contested divorce case")
        
        if signals.case_duration_months > 12:
            score += 4
            risk_factors.append(f"Extended case duration ({signals.case_duration_months} months)")
        
        # PROPERTY-SPECIFIC FACTORS FROM REAL DATA (30% of total score)
        
        property_value = property_data.get("current_value", 0)
        if property_value > 0:
            signals.property_value = property_value
            
            # High-value homes = higher legal/tax implications
            if property_value > 500000:
                score += 5
                risk_factors.append("High-value property (>$500k)")
            
            # Equity split complexity
            if signals.equity_split_required:
                score += 6
                risk_factors.append("Required equity split")
        
        # REAL PROPERTY AGE AND CONDITION FACTORS (10 points)
        year_built = property_data.get("year_built", 0)
        current_year = 2024
        if year_built > 0:
            property_age = current_year - year_built
            if property_age > 30:
                score += 5
                risk_factors.append(f"Older property ({property_age} years)")
                signals.building_age_risk = True
            
            if property_age > 50:
                score += 3
                risk_factors.append("High maintenance risk property")
        
        # OWNER OCCUPANCY STATUS (8 points)
        if not property_data.get("owner_occupied", True):
            score += 8
            risk_factors.append("Non-owner occupied (absentee owner)")
        
        # TAX LIEN AND ASSESSMENT FACTORS (12 points)
        tax_amount = property_data.get("tax_amount", 0)
        assessed_value = property_data.get("assessed_value", 0)
        
        if tax_amount > 0 and assessed_value > 0:
            tax_rate = (tax_amount / assessed_value) * 100
            if tax_rate > 3.0:  # High tax rate indicating distress
                score += 6
                risk_factors.append(f"High tax burden ({tax_rate:.1f}%)")
        
        if property_data.get("tax_year", 0) < current_year - 1:
            score += 6
            risk_factors.append("Potential tax delinquency")
        
        # SALES HISTORY AND MARKET ACTIVITY (10 points)
        sales_count = property_data.get("sales_history_count", 0)
        if sales_count > 3:  # Frequent turnover indicates issues
            score += 4
            risk_factors.append("Frequent property turnover")
        
        last_sale_date = property_data.get("last_sale_date", "")
        if last_sale_date:
            try:
                import datetime
                sale_date = datetime.datetime.strptime(last_sale_date, "%Y-%m-%d")
                days_since_sale = (datetime.datetime.now() - sale_date).days
                
                if days_since_sale < 365:  # Recent purchase may indicate flip
                    score += 3
                    risk_factors.append("Recent purchase (potential flip)")
                elif days_since_sale > 3650:  # Long ownership, emotional attachment
                    score += 2
                    risk_factors.append("Long-term ownership (emotional attachment)")
            except:
                pass
        
        # PRICE APPRECIATION TRENDS (8 points)
        price_appreciation = property_data.get("price_appreciation", 0)
        if price_appreciation < -10:  # Declining value
            score += 8
            risk_factors.append(f"Declining property value ({price_appreciation:.1f}%)")
        elif price_appreciation < 0:
            score += 4
            risk_factors.append("Negative price appreciation")
        
        # AVM CONFIDENCE AND VALUE RANGE (6 points)
        confidence_score = property_data.get("confidence_score", 0)
        if confidence_score < 70:  # Low confidence indicates uncertainty
            score += 3
            risk_factors.append("Property valuation uncertainty")
        
        value_high = property_data.get("value_high", 0)
        value_low = property_data.get("value_low", 0)
        if value_high > 0 and value_low > 0:
            value_range = ((value_high - value_low) / property_value) * 100
            if value_range > 20:  # Wide valuation range
                score += 3
                risk_factors.append("Wide property value range")
        
        # MARKET TIMING FACTORS (10% of total score)
        
        # Extract ZIP for market analysis
        zip_match = re.search(r'\b(\d{5})\b', signals.address)
        if zip_match:
            zip_code = zip_match.group(1)
            
            # Florida market conditions affecting divorce sales
            florida_divorce_markets = {
                "33403": {"buyer_market": False, "slow_season": False, "absorption_days": 45},  # Lake Park
                "33463": {"buyer_market": False, "slow_season": False, "absorption_days": 35},  # Greenacres
                "33418": {"buyer_market": True, "slow_season": True, "absorption_days": 85},   # PB Gardens
                "33467": {"buyer_market": True, "slow_season": True, "absorption_days": 95},   # Lake Worth
                "33460": {"buyer_market": True, "slow_season": True, "absorption_days": 90},   # Lake Worth
            }
            
            market_info = florida_divorce_markets.get(zip_code, 
                {"buyer_market": True, "slow_season": False, "absorption_days": 75})
            
            if market_info["buyer_market"]:
                score += 6
                risk_factors.append("Buyer's market conditions")
                signals.market_conditions_favor_buyer = True
            
            if market_info["slow_season"]:
                score += 4
                risk_factors.append("Seasonal timing challenges")
                signals.seasonal_timing_poor = True
                
            # Market absorption rate (days on market expectation)
            expected_dom = market_info["absorption_days"]
            if expected_dom > 75:
                score += 3
                risk_factors.append(f"Slow market absorption ({expected_dom} days)")
                signals.market_absorption_rate = expected_dom / 30  # Convert to months
        
        # DESPERATION MULTIPLIERS (10% of total score)
        
        # Time pressure creates desperation
        if signals.court_ordered_sale_deadline > 0 and signals.court_ordered_sale_deadline < 120:
            score += 10
            risk_factors.append(f"Urgent sale deadline ({signals.court_ordered_sale_deadline} days)")
        
        # Multiple children = higher urgency for resolution
        if signals.children_involved and signals.case_duration_months > 18:
            score += 8
            risk_factors.append("Extended divorce with children involved")
        
        # Property value vs debt stress
        last_sale_price = property_data.get("last_sale_price", 0)
        if last_sale_price > 0 and property_value > 0:
            if property_value < last_sale_price * 0.95:  # Underwater or losing equity
                score += 6
                risk_factors.append("Potential underwater mortgage")
                signals.underwater_mortgage = True
        
        # Cap at 100
        final_score = min(score, 100)
        
        # Risk level determination (more aggressive for divorce)
        if final_score >= 85:
            risk_level = "CRITICAL"
            discount_potential = "25-35%"
        elif final_score >= 70:
            risk_level = "HIGH"
            discount_potential = "15-25%"
        elif final_score >= 55:
            risk_level = "MEDIUM-HIGH"
            discount_potential = "10-20%"
        elif final_score >= 40:
            risk_level = "MEDIUM"
            discount_potential = "5-15%"
        else:
            risk_level = "LOW"
            discount_potential = "0-10%"
        
        return {
            "distress_score": final_score,
            "risk_level": risk_level,
            "discount_potential": discount_potential,
            "risk_factors": risk_factors,
            "total_factors": len(risk_factors),
            "confidence": min(95, 70 + len(risk_factors) * 2),  # High confidence with real data
            "urgency": "HIGH" if signals.court_ordered_sale_deadline < 90 else "MEDIUM",
            "property_value": property_value,
            "year_built": year_built,
            "tax_liens": tax_amount,
            "days_on_market": 0,  # To be enhanced with listing data
            "price_reductions": 0,  # To be enhanced with listing data
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
        risk_level = result["risk_level"]
        discount_potential = result["discount_potential"]
        urgency = result["urgency"]
        
        # Risk level emoji
        risk_emojis = {
            "CRITICAL": "🔴🚨",
            "HIGH": "🔴",
            "MEDIUM-HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        emoji = risk_emojis.get(risk_level, "⚪")
        
        print(f"\n📊 DIVORCE DISTRESS ANALYSIS:")
        print(f"   {emoji} Distress Score: {score}/100")
        print(f"   {emoji} Risk Level: {risk_level}")
        print(f"   💰 Discount Potential: {discount_potential}")
        print(f"   ⏰ Urgency Level: {urgency}")
        print(f"   🎯 Confidence: {result['confidence']}%")
        
        print(f"\n💔 DIVORCE-SPECIFIC FACTORS:")
        print(f"   Case Type: {divorce_signals.divorce_case_type.title()}")
        print(f"   Children Involved: {divorce_signals.children_involved}")
        print(f"   Case Duration: {divorce_signals.case_duration_months} months")
        print(f"   Forced Sale Timeline: {divorce_signals.forced_sale_timeline}")
        
        if result['risk_factors']:
            print(f"\n⚠️  DISTRESS INDICATORS:")
            for factor in result['risk_factors']:
                print(f"   • {factor}")
        
        return {
            "address": address,
            "distress_score": score,
            "risk_level": risk_level,
            "discount_potential": discount_potential,
            "urgency": urgency,
            "confidence": result['confidence'],
            "risk_factors": result['risk_factors'],
            "property_value": property_data.get('current_value', 0),
            "divorce_signals": asdict(divorce_signals),
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
            urgency = lead.get("urgency", "N/A")
            print(f"  Score {score}/100 | Discount: {discount} | Urgency: {urgency}")
            print(f"    {lead['address']}")

if __name__ == "__main__":
    main() 