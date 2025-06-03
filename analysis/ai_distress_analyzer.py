#!/usr/bin/env python3

import requests
import json
import sys
import os
import re
import time
from datetime import datetime
import argparse

class AIDistressAnalyzer:
    """
    AI-Powered Real Estate Distress Analysis using ChatGPT's latest model
    Pulls comprehensive property data and gets expert AI assessment
    """
    
    def __init__(self, openai_api_key=None):
        self.attom_api_key = 'ad91f2f30426f1ee54aec35791aaa044'
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            print("❌ ERROR: OpenAI API key required. Set OPENAI_API_KEY environment variable or pass as parameter.")
            sys.exit(1)
    
    def comprehensive_property_lookup(self, address1, address2):
        """Pull maximum available data from ATTOM API across multiple endpoints"""
        
        print(f"🔍 Analyzing: {address1}, {address2}")
        print("-" * 60)
        
        property_data = {
            'address': f"{address1}, {address2}",
            'analysis_timestamp': datetime.now().isoformat(),
            'data_sources': []
        }
        
        # 1. AVM (Automated Valuation Model)
        avm_data = self.get_attom_avm(address1, address2)
        if avm_data:
            property_data['avm'] = avm_data
            property_data['data_sources'].append('ATTOM_AVM')
            print(f"✅ AVM Data: Current Value ${avm_data.get('current_value', 'N/A'):,}")
        
        # 2. Property Detail (comprehensive property info)
        detail_data = self.get_attom_property_detail(address1, address2)
        if detail_data:
            property_data['property_detail'] = detail_data
            property_data['data_sources'].append('ATTOM_DETAIL')
            print(f"✅ Property Detail: {detail_data.get('property_type', 'N/A')} - {detail_data.get('year_built', 'N/A')}")
        
        # 3. Sales History
        sales_data = self.get_attom_sales_history(address1, address2)
        if sales_data:
            property_data['sales_history'] = sales_data
            property_data['data_sources'].append('ATTOM_SALES')
            print(f"✅ Sales History: {len(sales_data.get('sales', []))} transactions")
        
        # 4. Tax Assessment
        tax_data = self.get_attom_tax_assessment(address1, address2)
        if tax_data:
            property_data['tax_assessment'] = tax_data
            property_data['data_sources'].append('ATTOM_TAX')
            assessed_value = tax_data.get('assessed_value', 0)
            if assessed_value:
                print(f"✅ Tax Data: ${assessed_value:,} assessed")
            else:
                print(f"✅ Tax Data: Available")
        
        # 5. Market Data & Comparables
        market_data = self.get_attom_market_data(address1, address2)
        if market_data:
            property_data['market_data'] = market_data
            property_data['data_sources'].append('ATTOM_MARKET')
            median_price = market_data.get('median_sale_price', 0)
            if median_price:
                print(f"✅ Market Data: ${median_price:,} median price")
            else:
                print(f"✅ Market Data: Available")
        
        # 6. Foreclosure & Distress Signals
        distress_data = self.get_attom_distress_data(address1, address2)
        if distress_data:
            property_data['distress_indicators'] = distress_data
            property_data['data_sources'].append('ATTOM_DISTRESS')
            print(f"✅ Distress Signals: {len(distress_data.get('indicators', []))} found")
        
        print(f"\n📊 Data Sources: {', '.join(property_data['data_sources'])}")
        return property_data
    
    def get_attom_avm(self, address1, address2):
        """Get ATTOM AVM data with comprehensive valuation info"""
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
        params = {'address1': address1, 'address2': address2}
        headers = {'accept': 'application/json', 'apikey': self.attom_api_key}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('status', {}).get('code') == 0:
                prop = data.get('property', [{}])[0]
                avm = prop.get('avm', {})
                
                return {
                    'current_value': avm.get('amount', {}).get('value'),
                    'value_high': avm.get('amount', {}).get('high'),
                    'value_low': avm.get('amount', {}).get('low'),
                    'confidence_score': avm.get('condCode'),
                    'forecast_standard_deviation': avm.get('fsd'),
                    'last_updated': avm.get('eventDate'),
                    'property_type': prop.get('lot', {}).get('propertyType'),
                    'building_area': prop.get('building', {}).get('size', {}).get('bldgSize'),
                    'lot_size': prop.get('lot', {}).get('lotSize1')
                }
        except Exception as e:
            print(f"⚠️  AVM lookup failed: {e}")
            return None
    
    def get_attom_property_detail(self, address1, address2):
        """Get comprehensive property details"""
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
        params = {'address1': address1, 'address2': address2}
        headers = {'accept': 'application/json', 'apikey': self.attom_api_key}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('status', {}).get('code') == 0:
                prop = data.get('property', [{}])[0]
                
                return {
                    'year_built': prop.get('summary', {}).get('yearBuilt'),
                    'bedrooms': prop.get('building', {}).get('rooms', {}).get('beds'),
                    'bathrooms': prop.get('building', {}).get('rooms', {}).get('bathstotal'),
                    'property_type': prop.get('summary', {}).get('proptype'),
                    'property_sub_type': prop.get('summary', {}).get('propsubtype'),
                    'stories': prop.get('building', {}).get('construction', {}).get('storiesNumber'),
                    'pool': prop.get('building', {}).get('pool', {}).get('pooltype'),
                    'garage': prop.get('building', {}).get('parking', {}).get('garagetype'),
                    'heating': prop.get('building', {}).get('interior', {}).get('heatingtype'),
                    'cooling': prop.get('building', {}).get('interior', {}).get('coolingtype'),
                    'foundation': prop.get('building', {}).get('construction', {}).get('foundationtype'),
                    'roof_material': prop.get('building', {}).get('construction', {}).get('rooftype'),
                    'exterior_walls': prop.get('building', {}).get('construction', {}).get('walltype'),
                    'last_sale_date': prop.get('sale', {}).get('amount', {}).get('salerecdate'),
                    'last_sale_price': prop.get('sale', {}).get('amount', {}).get('saleamt'),
                    'owner_occupied': prop.get('summary', {}).get('owneroccupied'),
                    'owner_name': prop.get('owner', {}).get('owner1', {}).get('fullName'),
                    'mail_address': prop.get('owner', {}).get('mailingAddress', {}).get('oneLine')
                }
        except Exception as e:
            print(f"⚠️  Property detail lookup failed: {e}")
            return None
    
    def get_attom_sales_history(self, address1, address2):
        """Get sales history and transaction patterns"""
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/saleshistory/detail"
        params = {'address1': address1, 'address2': address2}
        headers = {'accept': 'application/json', 'apikey': self.attom_api_key}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('status', {}).get('code') == 0:
                sales = data.get('property', [{}])[0].get('sale', [])
                
                sales_list = []
                for sale in sales:
                    sales_list.append({
                        'sale_date': sale.get('amount', {}).get('salerecdate'),
                        'sale_price': sale.get('amount', {}).get('saleamt'),
                        'transaction_type': sale.get('saleTransType'),
                        'deed_type': sale.get('deedType'),
                        'seller_name': sale.get('seller', {}).get('fullName'),
                        'buyer_name': sale.get('buyer', {}).get('fullName')
                    })
                
                return {
                    'sales': sales_list,
                    'transaction_count': len(sales_list),
                    'price_appreciation': self.calculate_price_appreciation(sales_list)
                }
        except Exception as e:
            print(f"⚠️  Sales history lookup failed: {e}")
            return None
    
    def get_attom_tax_assessment(self, address1, address2):
        """Get tax assessment and burden information"""
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/assessment/detail"
        params = {'address1': address1, 'address2': address2}
        headers = {'accept': 'application/json', 'apikey': self.attom_api_key}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('status', {}).get('code') == 0:
                prop = data.get('property', [{}])[0]
                assessment = prop.get('assessment', {})
                
                return {
                    'assessed_value': assessment.get('assessed', {}).get('assdTtlValue'),
                    'market_value': assessment.get('market', {}).get('mktTtlValue'),
                    'tax_year': assessment.get('tax', {}).get('taxYear'),
                    'tax_amount': assessment.get('tax', {}).get('taxAmt'),
                    'assessment_ratio': assessment.get('assessed', {}).get('assdTtlValue') / assessment.get('market', {}).get('mktTtlValue', 1) if assessment.get('market', {}).get('mktTtlValue') else None,
                    'land_value': assessment.get('assessed', {}).get('assdLandValue'),
                    'improvement_value': assessment.get('assessed', {}).get('assdImpValue')
                }
        except Exception as e:
            print(f"⚠️  Tax assessment lookup failed: {e}")
            return None
    
    def get_attom_market_data(self, address1, address2):
        """Get local market conditions and comparables"""
        # Extract ZIP for market analysis
        zip_match = re.search(r'\b(\d{5})\b', address2)
        if not zip_match:
            return None
            
        zip_code = zip_match.group(1)
        
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/sale/snapshot"
        params = {'postalcode': zip_code, 'propertytype': 'SFR,CON,TH'}
        headers = {'accept': 'application/json', 'apikey': self.attom_api_key}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('status', {}).get('code') == 0:
                results = data.get('results', [])
                if results:
                    market = results[0]
                    return {
                        'zip_code': zip_code,
                        'median_sale_price': market.get('medianSalePrice'),
                        'average_sale_price': market.get('avgSalePrice'),
                        'sales_count_12m': market.get('salesCount12Mo'),
                        'median_days_on_market': market.get('medianDaysOnMarket'),
                        'price_per_sqft': market.get('medianPricePerSqFt'),
                        'inventory_count': market.get('inventoryCount'),
                        'absorption_rate': market.get('absorptionRate')
                    }
        except Exception as e:
            print(f"⚠️  Market data lookup failed: {e}")
            return None
    
    def get_attom_distress_data(self, address1, address2):
        """Check for foreclosure and distress indicators"""
        indicators = []
        
        # Check for preforeclosure
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/preforeclosure/detail"
        params = {'address1': address1, 'address2': address2}
        headers = {'accept': 'application/json', 'apikey': self.attom_api_key}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status', {}).get('code') == 0:
                    indicators.append({
                        'type': 'preforeclosure',
                        'status': 'active',
                        'details': data.get('property', [{}])[0]
                    })
        except Exception:
            pass
        
        return {
            'indicators': indicators,
            'distress_level': 'high' if len(indicators) > 0 else 'low'
        }
    
    def calculate_price_appreciation(self, sales_list):
        """Calculate price appreciation from sales history"""
        if len(sales_list) < 2:
            return None
            
        # Sort by date
        sorted_sales = sorted(sales_list, key=lambda x: x.get('sale_date', ''))
        
        if len(sorted_sales) >= 2:
            oldest = sorted_sales[0]
            newest = sorted_sales[-1]
            
            old_price = oldest.get('sale_price', 0)
            new_price = newest.get('sale_price', 0)
            
            if old_price > 0:
                appreciation = ((new_price - old_price) / old_price) * 100
                return round(appreciation, 2)
        
        return None
    
    def format_data_for_ai(self, property_data):
        """Format comprehensive property data for ChatGPT analysis"""
        
        formatted = f"""
COMPREHENSIVE PROPERTY ANALYSIS REQUEST

PROPERTY: {property_data['address']}
ANALYSIS DATE: {property_data['analysis_timestamp']}
DATA SOURCES: {', '.join(property_data['data_sources'])}

=== VALUATION DATA ==="""

        if 'avm' in property_data:
            avm = property_data['avm']
            current_value = avm.get('current_value', 0)
            value_low = avm.get('value_low', 0)
            value_high = avm.get('value_high', 0)
            building_area = avm.get('building_area', 0)
            lot_size = avm.get('lot_size', 0)
            
            formatted += f"""
Current AVM Value: ${current_value:,} """ if current_value else """
Current AVM Value: N/A"""
            
            formatted += f"""
Value Range: ${value_low:,} - ${value_high:,}""" if value_low and value_high else """
Value Range: N/A"""
            
            formatted += f"""
Confidence Score: {avm.get('confidence_score', 'N/A')}
Forecast Std Dev: {avm.get('forecast_standard_deviation', 'N/A')}
Last Updated: {avm.get('last_updated', 'N/A')}"""
            
            formatted += f"""
Building Size: {building_area:,} sq ft""" if building_area else """
Building Size: N/A"""
            
            formatted += f"""
Lot Size: {lot_size:,} sq ft""" if lot_size else """
Lot Size: N/A"""

        if 'property_detail' in property_data:
            detail = property_data['property_detail']
            formatted += f"""

=== PROPERTY CHARACTERISTICS ===
Year Built: {detail.get('year_built', 'N/A')}
Property Type: {detail.get('property_type', 'N/A')} ({detail.get('property_sub_type', 'N/A')})
Bedrooms: {detail.get('bedrooms', 'N/A')}
Bathrooms: {detail.get('bathrooms', 'N/A')}
Stories: {detail.get('stories', 'N/A')}
Pool: {detail.get('pool', 'None')}
Garage: {detail.get('garage', 'N/A')}
Heating: {detail.get('heating', 'N/A')}
Cooling: {detail.get('cooling', 'N/A')}
Foundation: {detail.get('foundation', 'N/A')}
Roof: {detail.get('roof_material', 'N/A')}
Exterior: {detail.get('exterior_walls', 'N/A')}
Owner Occupied: {detail.get('owner_occupied', 'N/A')}
Owner Name: {detail.get('owner_name', 'N/A')}
Mailing Address: {detail.get('mail_address', 'Same as property' if detail.get('mail_address') == property_data['address'] else detail.get('mail_address', 'N/A'))}"""

        if 'sales_history' in property_data:
            sales = property_data['sales_history']
            formatted += f"""

=== SALES HISTORY ===
Transaction Count: {sales.get('transaction_count', 0)}
Price Appreciation: {sales.get('price_appreciation', 'N/A')}%"""
            
            for i, sale in enumerate(sales.get('sales', [])[:5]):  # Last 5 sales
                sale_price = sale.get('sale_price', 0)
                if sale_price:
                    formatted += f"""
Sale #{i+1}: {sale.get('sale_date', 'N/A')} - ${sale_price:,} ({sale.get('transaction_type', 'N/A')})"""
                else:
                    formatted += f"""
Sale #{i+1}: {sale.get('sale_date', 'N/A')} - Price N/A ({sale.get('transaction_type', 'N/A')})"""

        if 'tax_assessment' in property_data:
            tax = property_data['tax_assessment']
            assessed_value = tax.get('assessed_value', 0)
            market_value = tax.get('market_value', 0)
            tax_amount = tax.get('tax_amount', 0)
            land_value = tax.get('land_value', 0)
            improvement_value = tax.get('improvement_value', 0)
            assessment_ratio = tax.get('assessment_ratio', 0)
            
            formatted += f"""

=== TAX ASSESSMENT ===
Tax Year: {tax.get('tax_year', 'N/A')}"""
            
            formatted += f"""
Assessed Value: ${assessed_value:,}""" if assessed_value else """
Assessed Value: N/A"""
            
            formatted += f"""
Market Value: ${market_value:,}""" if market_value else """
Market Value: N/A"""
            
            formatted += f"""
Annual Tax Amount: ${tax_amount:,}""" if tax_amount else """
Annual Tax Amount: N/A"""
            
            if assessment_ratio:
                formatted += f"""
Assessment Ratio: {assessment_ratio:.2%}"""
            else:
                formatted += """
Assessment Ratio: N/A"""
            
            formatted += f"""
Land Value: ${land_value:,}""" if land_value else """
Land Value: N/A"""
            
            formatted += f"""
Improvement Value: ${improvement_value:,}""" if improvement_value else """
Improvement Value: N/A"""

        if 'market_data' in property_data:
            market = property_data['market_data']
            median_sale_price = market.get('median_sale_price', 0)
            average_sale_price = market.get('average_sale_price', 0)
            price_per_sqft = market.get('price_per_sqft', 0)
            
            formatted += f"""

=== LOCAL MARKET CONDITIONS ===
ZIP Code: {market.get('zip_code', 'N/A')}"""
            
            formatted += f"""
Median Sale Price: ${median_sale_price:,}""" if median_sale_price else """
Median Sale Price: N/A"""
            
            formatted += f"""
Average Sale Price: ${average_sale_price:,}""" if average_sale_price else """
Average Sale Price: N/A"""
            
            formatted += f"""
Sales Count (12mo): {market.get('sales_count_12m', 'N/A')}
Median Days on Market: {market.get('median_days_on_market', 'N/A')}"""
            
            formatted += f"""
Price per Sq Ft: ${price_per_sqft}""" if price_per_sqft else """
Price per Sq Ft: N/A"""
            
            formatted += f"""
Inventory Count: {market.get('inventory_count', 'N/A')}
Absorption Rate: {market.get('absorption_rate', 'N/A')} months"""

        if 'distress_indicators' in property_data:
            distress = property_data['distress_indicators']
            formatted += f"""

=== DISTRESS INDICATORS ===
Distress Level: {distress.get('distress_level', 'N/A').upper()}
Active Indicators: {len(distress.get('indicators', []))}"""
            
            for indicator in distress.get('indicators', []):
                formatted += f"""
- {indicator.get('type', 'Unknown').upper()}: {indicator.get('status', 'N/A')}"""

        return formatted

    def safe_openai_call(self, prompt, retries=5):
        """Safe OpenAI API call with exponential backoff and rate limiting"""
        
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-4o',  # Latest model
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,  # Lower temperature for more consistent analysis
            'max_tokens': 800  # Increased for more detailed explanations
        }
        
        for attempt in range(retries):
            try:
                print(f"🤖 Sending data to ChatGPT (attempt {attempt + 1}/{retries})...")
                
                # Throttle requests - wait 1.2 seconds before each call
                if attempt > 0:
                    print(f"⏱️  Throttling: waiting 1.2 seconds...")
                time.sleep(1.2)
                
                resp = requests.post('https://api.openai.com/v1/chat/completions', 
                                   headers=headers, json=data, timeout=30)
                
                if resp.status_code == 429:
                    # Rate limit error - use exponential backoff
                    wait_time = 2 ** attempt
                    print(f"🔄 Rate limited (429). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                resp.raise_for_status()
                result = resp.json()
                
                # Check for API errors in response
                if 'error' in result:
                    print(f"❌ OpenAI API error: {result['error']}")
                    return None
                
                content = result['choices'][0]['message']['content']
                
                # Try to parse JSON response
                try:
                    analysis = json.loads(content)
                    print("✅ Successfully received AI analysis!")
                    return analysis
                except json.JSONDecodeError:
                    print("⚠️  Received non-JSON response, returning raw content")
                    return {'raw_response': content}
                    
            except requests.exceptions.RequestException as e:
                print(f"🌐 Network error on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    print("❌ Max retries reached. API call failed.")
                    return None
                
                # Wait before retry
                wait_time = 2 ** attempt
                print(f"⏱️  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                return None
        
        return None

    def analyze_with_chatgpt(self, formatted_data):
        """Send formatted data to ChatGPT for expert analysis with rate limiting"""
        
        prompt = f"""You are the BEST REAL ESTATE AGENT OF ALL TIME with 30+ years of experience in distressed property acquisition and investment. You have an unparalleled ability to identify opportunity in distressed real estate markets and have generated millions in profits through expert property analysis.

Please analyze the following comprehensive property data using your world-class expertise and the complete distress factor framework:

{formatted_data}

=== COMPREHENSIVE DISTRESS FACTOR FRAMEWORK ===

💰 FINANCIAL DISTRESS SIGNALS:
• Delinquent Tax Liens - Mounting unpaid taxes signal inability to maintain ownership; fear of asset seizure triggers anxiety and urgency
• Preforeclosure/Foreclosure - Legal proceedings introduce helplessness and public record shame; fear of eviction and credit ruin compounds distress
• Mechanic's Liens - Financial conflict with contractors indicates failed repairs or stalled progress, often leading to disrepair
• Job Loss/Income Drop - Sudden income loss reduces ability to meet obligations; triggers forced-sale behavior
• Code Violations - Legal notices create financial and reputational stress; often indicate deferred maintenance
• Insurance Ineligibility - Cannot secure coverage due to building risk; creates exposure feelings and urgency to offload

⚠️ CONDITION & MARKET SIGNALS:
• Incomplete Construction - Visual reminder of failure or resource exhaustion; indicates owner burnout
• Frequent Price Reductions - Repeated price drops trigger self-doubt, urgency, and perceived loss of control
• Long Days on Market - Extended duration leads to stagnation, anxiety, and urgency to liquidate
• Absentee Ownership - Distance creates disconnection and lowers motivation to maintain/maximize value
• Low Absorption Rate - Local market stagnation signals futility; leads to resignation and price capitulation

👵 DEMOGRAPHICS & LIFE EVENTS:
• Owner Age > 75 - Associated with downsizing, estate planning, or caregiving transitions
• Divorce Filing - Legal pressure to liquidate shared assets creates time stress and tension
• Critical Illness/Disability - Shift in priorities toward care creates urgency to sell
• Probate/Inheritance - Grief, legal confusion, and distance lead to rapid disposition of inherited assets

🌍 ENVIRONMENTAL & STRUCTURAL RISK:
• High Crime Rate - Owner feels unsafe and emotionally ready to relocate quickly
• Building Age > 50 (FL risk) - Fear of hidden structural issues and surprise assessments in post-Surfside environment
• Ocean Proximity + Regulation (FL SB-4D) - Exposure to new re-certification laws and engineering assessments causes emotional burnout
• Negative Local Sales Trends - Nearby underperforming sales deflate seller morale and lead to urgency

ANALYSIS REQUIRED:

1. DISTRESS SCORE (0-100): Based on all available data and the comprehensive distress framework above, what distress score would you assign? Consider multiple factor categories and their cumulative impact.

2. CONFIDENCE LEVEL (0-100): How confident are you in this assessment given the data quality, completeness, and alignment with known distress patterns?

3. VALUATION DISCOUNT (percentage): What discount from current market value would you expect due to distress factors? Consider both emotional urgency and financial constraints.

4. EXPLANATION (2-3 sentences): Provide a detailed explanation referencing specific distress factors from the framework above. Include which category of distress is most prominent and why this creates investment opportunity.

Please respond in this exact JSON format:
""" + """{
    "distress_score": [0-100],
    "confidence_level": [0-100], 
    "valuation_discount": "[X-Y%]",
    "explanation": "[2-3 sentence detailed explanation referencing specific distress factors]"
}"""

        return self.safe_openai_call(prompt)

    def analyze_property(self, address1, address2):
        """Complete property analysis workflow"""
        
        print("🏠 AI-POWERED REAL ESTATE DISTRESS ANALYSIS")
        print("=" * 80)
        
        # Step 1: Gather comprehensive data
        property_data = self.comprehensive_property_lookup(address1, address2)
        
        if not property_data.get('data_sources'):
            print("❌ No property data found. Please verify the address.")
            return None
        
        # Step 2: Format for AI analysis
        formatted_data = self.format_data_for_ai(property_data)
        
        # Step 3: Get AI analysis
        ai_analysis = self.analyze_with_chatgpt(formatted_data)
        
        if not ai_analysis:
            print("❌ AI analysis failed.")
            return None
        
        # Step 4: Display results
        self.display_results(property_data, ai_analysis)
        
        return {
            'property_data': property_data,
            'ai_analysis': ai_analysis
        }

    def display_results(self, property_data, ai_analysis):
        """Display formatted analysis results"""
        
        print("\n" + "="*80)
        print("🎯 AI DISTRESS ANALYSIS RESULTS")
        print("="*80)
        
        print(f"📍 Property: {property_data['address']}")
        print(f"📊 Data Sources: {', '.join(property_data['data_sources'])}")
        
        if 'avm' in property_data and property_data['avm'].get('current_value'):
            print(f"💰 Current Value: ${property_data['avm']['current_value']:,}")
        
        print("\n🤖 AI EXPERT ANALYSIS:")
        print("-" * 40)
        
        if 'distress_score' in ai_analysis:
            print(f"📈 Distress Score: {ai_analysis['distress_score']}/100")
            print(f"🎯 Confidence Level: {ai_analysis['confidence_level']}/100")
            print(f"💸 Valuation Discount: {ai_analysis['valuation_discount']}")
            print(f"📝 Explanation: {ai_analysis['explanation']}")
        else:
            print("Raw AI Response:")
            print(ai_analysis.get('raw_response', 'No response'))

    def batch_analyze_properties(self, property_list, max_batch_size=3):
        """Analyze multiple properties in batches to optimize API usage"""
        
        results = []
        
        for i in range(0, len(property_list), max_batch_size):
            batch = property_list[i:i + max_batch_size]
            
            print(f"\n📦 Processing batch {i//max_batch_size + 1} ({len(batch)} properties)")
            print("=" * 60)
            
            # Collect data for all properties in batch
            batch_data = []
            for address1, address2 in batch:
                property_data = self.comprehensive_property_lookup(address1, address2)
                if property_data.get('data_sources'):
                    formatted_data = self.format_data_for_ai(property_data)
                    batch_data.append({
                        'address': f"{address1}, {address2}",
                        'data': formatted_data,
                        'property_data': property_data
                    })
            
            if batch_data:
                batch_analysis = self.analyze_batch_with_chatgpt(batch_data)
                
                if batch_analysis:
                    for j, analysis in enumerate(batch_analysis):
                        if j < len(batch_data):
                            results.append({
                                'address': batch_data[j]['address'],
                                'property_data': batch_data[j]['property_data'],
                                'ai_analysis': analysis
                            })
                
                # Longer delay between batches
                if i + max_batch_size < len(property_list):
                    print(f"⏱️  Batch complete. Waiting 3 seconds before next batch...")
                    time.sleep(3)
        
        return results

    def analyze_batch_with_chatgpt(self, batch_data):
        """Send multiple properties to ChatGPT for batch analysis"""
        
        # Format multiple properties for batch analysis
        batch_prompt = """You are the BEST REAL ESTATE AGENT OF ALL TIME with 30+ years of experience in distressed property acquisition and investment.

Analyze the following properties using the comprehensive distress factor framework. Return a JSON array with one analysis object per property.

=== COMPREHENSIVE DISTRESS FACTOR FRAMEWORK ===

💰 FINANCIAL DISTRESS SIGNALS:
• Delinquent Tax Liens • Preforeclosure/Foreclosure • Mechanic's Liens • Job Loss/Income Drop • Code Violations • Insurance Ineligibility

⚠️ CONDITION & MARKET SIGNALS:
• Incomplete Construction • Frequent Price Reductions • Long Days on Market • Absentee Ownership • Low Absorption Rate

👵 DEMOGRAPHICS & LIFE EVENTS:
• Owner Age > 75 • Divorce Filing • Critical Illness/Disability • Probate/Inheritance

🌍 ENVIRONMENTAL & STRUCTURAL RISK:
• High Crime Rate • Building Age > 50 (FL risk) • Ocean Proximity + Regulation (FL SB-4D) • Negative Local Sales Trends

PROPERTIES TO ANALYZE:

"""

        for i, prop in enumerate(batch_data):
            batch_prompt += f"""
=== PROPERTY {i+1}: {prop['address']} ===
{prop['data']}

"""

        batch_prompt += """

Please respond with a JSON array in this exact format:
[
  {
    "property_index": 1,
    "distress_score": [0-100],
    "confidence_level": [0-100],
    "valuation_discount": "[X-Y%]",
    "explanation": "[2-3 sentence detailed explanation referencing specific distress factors]"
  },
  {
    "property_index": 2,
    "distress_score": [0-100],
    "confidence_level": [0-100],
    "valuation_discount": "[X-Y%]",
    "explanation": "[2-3 sentence detailed explanation referencing specific distress factors]"
  }
]"""

        print(f"🔄 Sending batch of {len(batch_data)} properties to AI...")
        result = self.safe_openai_call(batch_prompt)
        
        if result and 'raw_response' not in result:
            return result
        elif result and 'raw_response' in result:
            # Try to extract JSON array from raw response
            try:
                import re
                json_match = re.search(r'\[.*\]', result['raw_response'], re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return None

def main():
    parser = argparse.ArgumentParser(description='AI-Powered Real Estate Distress Analysis')
    parser.add_argument('address1', nargs='?', help='Street address (e.g., "123 MAIN STREET")')
    parser.add_argument('address2', nargs='?', help='City, State, ZIP (e.g., "PALM BEACH GARDENS, FL 33418")')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--batch', action='store_true', help='Run in batch mode for multiple properties')
    parser.add_argument('--check-usage', action='store_true', help='Display usage information and exit')
    
    args = parser.parse_args()
    
    if args.check_usage:
        print("💡 CHECK YOUR OPENAI USAGE:")
        print("🔗 Usage: https://platform.openai.com/account/usage")
        print("🔗 Billing: https://platform.openai.com/account/billing/limits")
        print("💰 Consider upgrading for higher rate limits if needed")
        return
    
    analyzer = AIDistressAnalyzer(openai_api_key=args.api_key)
    
    if args.batch:
        print("🔄 BATCH MODE: Enter properties (press Enter twice when done)")
        property_list = []
        
        while True:
            address1 = input("Street Address (or press Enter to finish): ").strip()
            if not address1:
                break
            address2 = input("City, State, ZIP: ").strip()
            if address2:
                property_list.append((address1, address2))
        
        if property_list:
            print(f"\n📊 Starting batch analysis of {len(property_list)} properties...")
            results = analyzer.batch_analyze_properties(property_list)
            
            # Save batch results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_analysis_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n💾 Batch results saved to: {filename}")
            
            # Display summary
            print(f"\n📈 BATCH ANALYSIS SUMMARY:")
            print("-" * 40)
            for result in results:
                if result.get('ai_analysis'):
                    analysis = result['ai_analysis']
                    score = analysis.get('distress_score', 'N/A')
                    discount = analysis.get('valuation_discount', 'N/A')
                    print(f"📍 {result['address']}")
                    print(f"   Score: {score}/100, Discount: {discount}")
        else:
            print("❌ No properties entered.")
    
    elif args.address1 and args.address2:
        # Single property mode
        result = analyzer.analyze_property(args.address1, args.address2)
        
        if result:
            # Save results to JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_analysis_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {filename}")
    
    else:
        print("❌ Usage:")
        print("  Single property: python3 ai_distress_analyzer.py \"STREET\" \"CITY, STATE ZIP\"")
        print("  Batch mode: python3 ai_distress_analyzer.py --batch")
        print("  Check usage: python3 ai_distress_analyzer.py --check-usage")
        print("\nExample:")
        print("  python3 ai_distress_analyzer.py \"123 MAIN ST\" \"MIAMI, FL 33101\"")

if __name__ == "__main__":
    main() 