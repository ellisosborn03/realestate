#!/usr/bin/env python3

import requests
import json
import sys
import os
import re
import time
from datetime import datetime
import argparse

class OptimizedAIDistressAnalyzer:
    """
    Optimized AI-Powered Real Estate Distress Analysis 
    Reduced token usage while maintaining analysis quality
    """
    
    def __init__(self, openai_api_key=None):
        self.attom_api_key = 'ad91f2f30426f1ee54aec35791aaa044'
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            print("❌ ERROR: OpenAI API key required. Set OPENAI_API_KEY environment variable or pass as parameter.")
            sys.exit(1)
    
    def comprehensive_property_lookup(self, address1, address2):
        """Pull property data from ATTOM API - same as original"""
        
        print(f"🔍 Analyzing: {address1}, {address2}")
        print("-" * 60)
        
        property_data = {
            'address': f"{address1}, {address2}",
            'analysis_timestamp': datetime.now().isoformat(),
            'data_sources': []
        }
        
        # Get data from ATTOM endpoints (same as original)
        from ai_distress_analyzer import AIDistressAnalyzer
        original_analyzer = AIDistressAnalyzer()
        
        # Reuse original data collection methods
        avm_data = original_analyzer.get_attom_avm(address1, address2)
        if avm_data:
            property_data['avm'] = avm_data
            property_data['data_sources'].append('ATTOM_AVM')
            print(f"✅ AVM Data: Current Value ${avm_data.get('current_value', 'N/A'):,}")
        
        detail_data = original_analyzer.get_attom_property_detail(address1, address2)
        if detail_data:
            property_data['property_detail'] = detail_data
            property_data['data_sources'].append('ATTOM_DETAIL')
            print(f"✅ Property Detail: {detail_data.get('property_type', 'N/A')}")
        
        sales_data = original_analyzer.get_attom_sales_history(address1, address2)
        if sales_data:
            property_data['sales_history'] = sales_data
            property_data['data_sources'].append('ATTOM_SALES')
            print(f"✅ Sales History: {len(sales_data.get('sales', []))} transactions")
        
        tax_data = original_analyzer.get_attom_tax_assessment(address1, address2)
        if tax_data:
            property_data['tax_assessment'] = tax_data
            property_data['data_sources'].append('ATTOM_TAX')
            print(f"✅ Tax Data: Available")
        
        distress_data = original_analyzer.get_attom_distress_data(address1, address2)
        if distress_data:
            property_data['distress_indicators'] = distress_data
            property_data['data_sources'].append('ATTOM_DISTRESS')
            print(f"✅ Distress Signals: {len(distress_data.get('indicators', []))} found")
        
        print(f"\n📊 Data Sources: {', '.join(property_data['data_sources'])}")
        return property_data

    def format_data_for_ai_optimized(self, property_data):
        """Optimized format with reduced detail (30% token savings)"""
        
        formatted = f"""PROPERTY: {property_data['address']}
DATA: {', '.join(property_data['data_sources'])}

VALUATION:"""

        if 'avm' in property_data:
            avm = property_data['avm']
            current_value = avm.get('current_value', 0)
            if current_value:
                formatted += f" ${current_value:,}"
            
        if 'property_detail' in property_data:
            detail = property_data['property_detail']
            year_built = detail.get('year_built')
            bedrooms = detail.get('bedrooms')
            bathrooms = detail.get('bathrooms')
            prop_type = detail.get('property_type', 'N/A')
            
            formatted += f"\nPROPERTY: {prop_type}"
            if year_built:
                formatted += f", Built: {year_built}"
            if bedrooms and bathrooms:
                formatted += f", {bedrooms}BR/{bathrooms}BA"
            
            # Key distress indicators only
            mail_address = detail.get('mail_address', '')
            if mail_address and mail_address != property_data['address']:
                formatted += f"\nABSENTEE OWNER: {mail_address}"

        if 'sales_history' in property_data:
            sales = property_data['sales_history']
            count = sales.get('transaction_count', 0)
            formatted += f"\nSALES: {count} transactions"
            if count > 0:
                recent_sales = sales.get('sales', [])[:2]  # Only 2 most recent
                for sale in recent_sales:
                    date = sale.get('sale_date', 'N/A')
                    price = sale.get('sale_price', 0)
                    if price:
                        formatted += f"\n  {date}: ${price:,}"

        if 'tax_assessment' in property_data:
            tax = property_data['tax_assessment']
            assessed_value = tax.get('assessed_value', 0)
            tax_amount = tax.get('tax_amount', 0)
            
            if assessed_value:
                formatted += f"\nTAX: Assessed ${assessed_value:,}"
            if tax_amount:
                formatted += f", Annual ${tax_amount:,}"

        if 'distress_indicators' in property_data:
            distress = property_data['distress_indicators']
            indicators = distress.get('indicators', [])
            if indicators:
                formatted += f"\nDISTRESS: {len(indicators)} active"
                for indicator in indicators:
                    formatted += f"\n  {indicator.get('type', 'Unknown').upper()}"

        return formatted

    def safe_openai_call(self, prompt, retries=5):
        """Safe OpenAI API call with exponential backoff"""
        
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-4o',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.3,
            'max_tokens': 300  # Reduced from 800 for shorter responses
        }
        
        for attempt in range(retries):
            try:
                print(f"🤖 Sending data to ChatGPT (attempt {attempt + 1}/{retries})...")
                
                if attempt > 0:
                    print(f"⏱️  Throttling: waiting 1.2 seconds...")
                time.sleep(1.2)
                
                resp = requests.post('https://api.openai.com/v1/chat/completions', 
                                   headers=headers, json=data, timeout=30)
                
                if resp.status_code == 429:
                    wait_time = 2 ** attempt
                    print(f"🔄 Rate limited (429). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                resp.raise_for_status()
                result = resp.json()
                
                if 'error' in result:
                    print(f"❌ OpenAI API error: {result['error']}")
                    return None
                
                content = result['choices'][0]['message']['content']
                
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
                
                wait_time = 2 ** attempt
                print(f"⏱️  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                return None
        
        return None

    def analyze_with_chatgpt_optimized(self, formatted_data):
        """Optimized prompt with reduced framework (30% savings) and shorter responses (20% savings)"""
        
        prompt = f"""You are the BEST REAL ESTATE AGENT OF ALL TIME with 30+ years experience in distressed property acquisition.

Analyze this property using the distress framework:

{formatted_data}

DISTRESS FACTORS:
💰 FINANCIAL: Tax liens, foreclosure, job loss, code violations, insurance issues
⚠️ MARKET: Price drops, long DOM, absentee ownership, low absorption
👵 LIFE EVENTS: Age >75, divorce, illness, probate
🌍 RISK: Crime, building age >50 (FL), ocean proximity (SB-4D), negative trends

Provide:
1. DISTRESS SCORE (0-100)
2. CONFIDENCE LEVEL (0-100) 
3. VALUATION DISCOUNT (X-Y%)
4. EXPLANATION (1 sentence with specific factors)

JSON format:
{{"distress_score": [0-100], "confidence_level": [0-100], "valuation_discount": "[X-Y%]", "explanation": "[1 sentence]"}}"""

        return self.safe_openai_call(prompt)

    def batch_analyze_properties_optimized(self, property_list, max_batch_size=3):
        """Optimized batch analysis with SAFETY LIMITS to prevent excessive API usage"""
        
        # SAFETY CHECK: Warn if more than 10 properties
        if len(property_list) > 10:
            print(f"\n⚠️  SAFETY WARNING: You're about to analyze {len(property_list)} properties!")
            print(f"💰 Estimated cost: ${len(property_list) * 0.0013:.2f}")
            print(f"⏱️  Estimated time: {len(property_list) * 1.5 / 60:.1f} minutes")
            
            response = input(f"\n🚨 Type 'CONFIRM' to proceed with {len(property_list)} properties (or 'n' to cancel): ")
            if response.upper() != 'CONFIRM':
                print("❌ Batch analysis cancelled for safety.")
                return []
            
            print(f"✅ Confirmed: Processing {len(property_list)} properties...")
        
        # TESTING LIMIT: Hard limit for testing mode
        if len(property_list) > 50:
            print(f"\n🛑 HARD LIMIT: Maximum 50 properties per batch for safety.")
            print(f"   Please split into smaller batches.")
            return []
        
        results = []
        
        for i in range(0, len(property_list), max_batch_size):
            batch = property_list[i:i + max_batch_size]
            
            print(f"\n📦 Processing optimized batch {i//max_batch_size + 1} ({len(batch)} properties)")
            print("=" * 60)
            
            batch_data = []
            for address1, address2 in batch:
                property_data = self.comprehensive_property_lookup(address1, address2)
                if property_data.get('data_sources'):
                    formatted_data = self.format_data_for_ai_optimized(property_data)
                    batch_data.append({
                        'address': f"{address1}, {address2}",
                        'data': formatted_data,
                        'property_data': property_data
                    })
            
            if batch_data:
                batch_analysis = self.analyze_batch_with_chatgpt_optimized(batch_data)
                
                if batch_analysis:
                    for j, analysis in enumerate(batch_analysis):
                        if j < len(batch_data):
                            results.append({
                                'address': batch_data[j]['address'],
                                'property_data': batch_data[j]['property_data'],
                                'ai_analysis': analysis
                            })
                
                if i + max_batch_size < len(property_list):
                    print(f"⏱️  Batch complete. Waiting 3 seconds before next batch...")
                    time.sleep(3)
        
        return results

    def analyze_batch_with_chatgpt_optimized(self, batch_data):
        """Optimized batch prompt"""
        
        batch_prompt = f"""You are the BEST REAL ESTATE AGENT OF ALL TIME. Analyze these {len(batch_data)} properties using distress factors.

FACTORS: Financial (tax/foreclosure), Market (DOM/price drops), Life Events (age/divorce), Environmental Risk (crime/age/regulations)

PROPERTIES:
"""

        for i, prop in enumerate(batch_data):
            batch_prompt += f"""
{i+1}. {prop['address']}
{prop['data']}
"""

        batch_prompt += f"""
Return JSON array:
[{{"property_index": 1, "distress_score": [0-100], "confidence_level": [0-100], "valuation_discount": "[X-Y%]", "explanation": "[1 sentence]"}}, {{"property_index": 2, ...}}]"""

        print(f"🔄 Sending optimized batch of {len(batch_data)} properties to AI...")
        result = self.safe_openai_call(batch_prompt)
        
        if result and 'raw_response' not in result:
            return result
        elif result and 'raw_response' in result:
            try:
                import re
                json_match = re.search(r'\[.*\]', result['raw_response'], re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return None

    def analyze_property(self, address1, address2):
        """Single property analysis with optimizations"""
        
        print("🏠 OPTIMIZED AI-POWERED REAL ESTATE DISTRESS ANALYSIS")
        print("=" * 80)
        
        property_data = self.comprehensive_property_lookup(address1, address2)
        
        if not property_data.get('data_sources'):
            print("❌ No property data found. Please verify the address.")
            return None
        
        formatted_data = self.format_data_for_ai_optimized(property_data)
        ai_analysis = self.analyze_with_chatgpt_optimized(formatted_data)
        
        if not ai_analysis:
            print("❌ AI analysis failed.")
            return None
        
        self.display_results(property_data, ai_analysis)
        
        return {
            'property_data': property_data,
            'ai_analysis': ai_analysis
        }

    def display_results(self, property_data, ai_analysis):
        """Display formatted analysis results"""
        
        print("\n" + "="*80)
        print("🎯 OPTIMIZED AI DISTRESS ANALYSIS RESULTS")
        print("="*80)
        
        print(f"📍 Property: {property_data['address']}")
        print(f"📊 Data Sources: {', '.join(property_data['data_sources'])}")
        
        if 'avm' in property_data and property_data['avm'].get('current_value'):
            print(f"💰 Current Value: ${property_data['avm']['current_value']:,}")
        
        print("\n🤖 OPTIMIZED AI EXPERT ANALYSIS:")
        print("-" * 40)
        
        if 'distress_score' in ai_analysis:
            print(f"📈 Distress Score: {ai_analysis['distress_score']}/100")
            print(f"🎯 Confidence Level: {ai_analysis['confidence_level']}/100")
            print(f"💸 Valuation Discount: {ai_analysis['valuation_discount']}")
            print(f"📝 Explanation: {ai_analysis['explanation']}")
        else:
            print("Raw AI Response:")
            print(ai_analysis.get('raw_response', 'No response'))

def main():
    parser = argparse.ArgumentParser(description='Optimized AI-Powered Real Estate Distress Analysis')
    parser.add_argument('address1', nargs='?', help='Street address')
    parser.add_argument('address2', nargs='?', help='City, State, ZIP')
    parser.add_argument('--api-key', help='OpenAI API key')
    parser.add_argument('--batch', action='store_true', help='Run in batch mode')
    parser.add_argument('--test', action='store_true', help='Test mode: 3-property limit with cost display')
    
    args = parser.parse_args()
    
    analyzer = OptimizedAIDistressAnalyzer(openai_api_key=args.api_key)
    
    if args.test or args.batch:
        if args.test:
            print("🧪 TEST MODE: Maximum 3 properties for safe testing")
            print("💰 Cost limit: ~$0.004 total")
            max_test_properties = 3
        else:
            print("🔄 OPTIMIZED BATCH MODE: Enter properties")
            print("💡 TESTING TIP: Use 3-9 properties for testing (automatic safety above 10)")
            print("💰 Cost per property: ~$0.0013")
            max_test_properties = None
            
        print("-" * 60)
        
        property_list = []
        count = 0
        
        while True:
            count += 1
            
            # Test mode limit
            if args.test and len(property_list) >= max_test_properties:
                print(f"\n🧪 TEST MODE LIMIT: Maximum {max_test_properties} properties reached")
                break
            
            # Safety reminder every 5 properties (batch mode only)
            if not args.test and count > 5 and count % 5 == 1:
                print(f"\n⚠️  You've entered {count-1} properties so far...")
                if count > 10:
                    print(f"💰 Current estimated cost: ${(count-1) * 0.0013:.3f}")
            
            address1 = input(f"Property #{count} Street Address (or Enter to finish): ").strip()
            if not address1:
                break
                
            address2 = input(f"Property #{count} City, State, ZIP: ").strip()
            if address2:
                property_list.append((address1, address2))
            
            # Encourage testing with small batches (batch mode only)
            if not args.test:
                if len(property_list) == 3:
                    print(f"\n💡 Perfect testing size! 3 properties = ~$0.004 cost")
                elif len(property_list) == 5:
                    print(f"\n👍 Good testing size! 5 properties = ~$0.007 cost")
                elif len(property_list) == 9:
                    print(f"\n✅ Max recommended testing! 9 properties = ~$0.012 cost")
                elif len(property_list) == 10:
                    print(f"\n⚠️  Next property will trigger safety confirmation!")
        
        if property_list:
            print(f"\n📊 Starting optimized {'test' if args.test else 'batch'} analysis of {len(property_list)} properties...")
            print(f"💰 Estimated cost: ${len(property_list) * 0.0013:.3f}")
            
            # Final safety check for testing
            if len(property_list) <= 10:
                print(f"✅ Safe testing batch size")
            
            results = analyzer.batch_analyze_properties_optimized(property_list)
            
            if results:  # Only save if we got results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                mode = "test" if args.test else "batch"
                filename = f"optimized_{mode}_analysis_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                
                print(f"\n💾 Results saved to: {filename}")
                
                print(f"\n📈 OPTIMIZED {'TEST' if args.test else 'BATCH'} SUMMARY:")
                for result in results:
                    if result.get('ai_analysis'):
                        analysis = result['ai_analysis']
                        score = analysis.get('distress_score', 'N/A')
                        discount = analysis.get('valuation_discount', 'N/A')
                        print(f"📍 {result['address']}: Score {score}/100, Discount {discount}")
            else:
                print("❌ No results to save.")
        else:
            print("❌ No properties entered.")
    
    elif args.address1 and args.address2:
        result = analyzer.analyze_property(args.address1, args.address2)
        
        if result:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimized_ai_analysis_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {filename}")
    
    else:
        print("❌ Usage:")
        print("  Single property: python3 ai_distress_analyzer_optimized.py \"STREET\" \"CITY, STATE ZIP\"")
        print("  🧪 Test mode:   python3 ai_distress_analyzer_optimized.py --test (3 properties max, ~$0.004)")
        print("  📊 Batch mode:   python3 ai_distress_analyzer_optimized.py --batch (safety limits above 10)")
        print("\n💡 Examples:")
        print("  python3 ai_distress_analyzer_optimized.py \"123 MAIN ST\" \"MIAMI, FL 33101\"")
        print("  python3 ai_distress_analyzer_optimized.py --test")
        print("\n⚠️  Always test with small batches first!")

if __name__ == "__main__":
    main() 