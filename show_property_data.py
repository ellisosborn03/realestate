#!/usr/bin/env python3

import sys
import os
sys.path.append('analysis')

from ai_distress_analyzer import AIDistressAnalyzer
import json

def show_raw_property_data(address1, address2):
    """Display raw property data to verify distress claims"""
    
    print("🔍 RAW PROPERTY DATA EXTRACTION")
    print("=" * 60)
    print(f"📍 Property: {address1}, {address2}")
    print("=" * 60)
    
    analyzer = AIDistressAnalyzer(openai_api_key="dummy-key")  # Don't need real key for data collection
    
    # Get comprehensive property data
    property_data = analyzer.comprehensive_property_lookup(address1, address2)
    
    if not property_data.get('data_sources'):
        print("❌ No property data found")
        return
    
    print("\n💰 FINANCIAL DATA:")
    print("-" * 30)
    
    # AVM Data
    if 'avm' in property_data:
        avm = property_data['avm']
        current_value = avm.get('current_value', 0)
        value_low = avm.get('value_low', 0)
        value_high = avm.get('value_high', 0)
        
        print(f"Current Value: ${current_value:,}" if current_value else "Current Value: N/A")
        print(f"Value Range: ${value_low:,} - ${value_high:,}" if value_low and value_high else "Value Range: N/A")
        print(f"Confidence: {avm.get('confidence_score', 'N/A')}")
    
    # Tax Assessment
    if 'tax_assessment' in property_data:
        tax = property_data['tax_assessment']
        assessed_value = tax.get('assessed_value', 0)
        market_value = tax.get('market_value', 0)
        tax_amount = tax.get('tax_amount', 0)
        
        print(f"Assessed Value: ${assessed_value:,}" if assessed_value else "Assessed Value: N/A")
        print(f"Market Value: ${market_value:,}" if market_value else "Market Value: N/A")
        print(f"Annual Taxes: ${tax_amount:,}" if tax_amount else "Annual Taxes: N/A")
        
        # Calculate tax burden
        if current_value and tax_amount:
            tax_rate = (tax_amount / current_value) * 100
            print(f"Tax Rate: {tax_rate:.2f}%")
            print(f"Tax Burden: {'HIGH' if tax_rate > 2.0 else 'MODERATE' if tax_rate > 1.0 else 'LOW'}")
    
    print("\n🏠 PROPERTY DETAILS:")
    print("-" * 30)
    
    if 'property_detail' in property_data:
        detail = property_data['property_detail']
        print(f"Year Built: {detail.get('year_built', 'N/A')}")
        print(f"Property Type: {detail.get('property_type', 'N/A')}")
        print(f"Bedrooms: {detail.get('bedrooms', 'N/A')}")
        print(f"Bathrooms: {detail.get('bathrooms', 'N/A')}")
        print(f"Owner Name: {detail.get('owner_name', 'N/A')}")
        
        # Check for absentee ownership
        mail_address = detail.get('mail_address', '')
        if mail_address and mail_address != property_data['address']:
            print(f"⚠️  ABSENTEE OWNER: Mail to {mail_address}")
        else:
            print("✅ Owner-occupied (same mailing address)")
        
        # Check building age for FL risk
        year_built = detail.get('year_built')
        if year_built:
            age = 2024 - year_built
            print(f"Building Age: {age} years")
            if age > 50:
                print("⚠️  FL RISK: Building >50 years (post-Surfside concerns)")
    
    print("\n📊 SALES HISTORY:")
    print("-" * 30)
    
    if 'sales_history' in property_data:
        sales = property_data['sales_history']
        transaction_count = sales.get('transaction_count', 0)
        print(f"Total Transactions: {transaction_count}")
        
        if transaction_count == 0:
            print("⚠️  NO SALES HISTORY: Possible long-term ownership or data limitation")
        else:
            for i, sale in enumerate(sales.get('sales', [])[:3]):
                sale_date = sale.get('sale_date', 'N/A')
                sale_price = sale.get('sale_price', 0)
                if sale_price:
                    print(f"Sale {i+1}: {sale_date} - ${sale_price:,}")
                else:
                    print(f"Sale {i+1}: {sale_date} - Price N/A")
    
    print("\n🚨 DISTRESS INDICATORS:")
    print("-" * 30)
    
    distress_found = False
    
    # Check for active distress signals
    if 'distress_indicators' in property_data:
        indicators = property_data['distress_indicators'].get('indicators', [])
        if indicators:
            for indicator in indicators:
                print(f"🔴 {indicator.get('type', 'Unknown').upper()}: {indicator.get('status', 'N/A')}")
                distress_found = True
    
    # Look for other distress signals in the data
    if 'tax_assessment' in property_data:
        tax = property_data['tax_assessment']
        current_value = property_data.get('avm', {}).get('current_value', 0)
        tax_amount = tax.get('tax_amount', 0)
        
        if current_value and tax_amount:
            tax_rate = (tax_amount / current_value) * 100
            if tax_rate > 2.5:
                print(f"🔴 HIGH TAX BURDEN: {tax_rate:.2f}% annual rate")
                distress_found = True
    
    if not distress_found:
        print("✅ No active distress indicators found in available data")
    
    print(f"\n💾 RAW DATA AVAILABLE FOR VERIFICATION")
    print(f"📊 Data Sources: {', '.join(property_data['data_sources'])}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 show_property_data.py \"STREET ADDRESS\" \"CITY, STATE ZIP\"")
        print("Example: python3 show_property_data.py \"8716 WENDY LANE EAST\" \"WEST PALM BEACH, FL 33411\"")
    else:
        show_raw_property_data(sys.argv[1], sys.argv[2]) 