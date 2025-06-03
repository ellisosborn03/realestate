#!/usr/bin/env python3

import sys
import os
sys.path.append('analysis')

from ai_distress_analyzer import AIDistressAnalyzer

def estimate_tokens(text):
    """Rough token estimation: ~4 characters per token for GPT-4"""
    return len(text) // 4

def calculate_prompt_tokens():
    """Calculate tokens used in our AI distress analyzer prompt"""
    
    # Sample property data (typical size)
    sample_formatted_data = """
COMPREHENSIVE PROPERTY ANALYSIS REQUEST

PROPERTY: 8716 WENDY LANE EAST, WEST PALM BEACH, FL 33411
ANALYSIS DATE: 2024-06-02T23:30:00
DATA SOURCES: ATTOM_AVM, ATTOM_DETAIL, ATTOM_SALES, ATTOM_TAX, ATTOM_DISTRESS

=== VALUATION DATA ===
Current AVM Value: $1,747,594
Value Range: $1,660,214 - $1,834,973
Confidence Score: N/A
Forecast Std Dev: N/A
Last Updated: N/A
Building Size: N/A
Lot Size: N/A

=== PROPERTY CHARACTERISTICS ===
Year Built: N/A
Property Type: SFR (N/A)
Bedrooms: 4
Bathrooms: 3.0
Stories: N/A
Pool: None
Garage: N/A
Heating: N/A
Cooling: N/A
Foundation: N/A
Roof: N/A
Exterior: N/A
Owner Occupied: N/A
Owner Name: N/A
Mailing Address: N/A

=== SALES HISTORY ===
Transaction Count: 0
Price Appreciation: N/A%

=== TAX ASSESSMENT ===
Tax Year: N/A
Assessed Value: N/A
Market Value: N/A
Annual Tax Amount: N/A
Assessment Ratio: N/A
Land Value: N/A
Improvement Value: N/A

=== LOCAL MARKET CONDITIONS ===
ZIP Code: N/A
Median Sale Price: N/A
Average Sale Price: N/A
Sales Count (12mo): N/A
Median Days on Market: N/A
Price per Sq Ft: N/A
Inventory Count: N/A
Absorption Rate: N/A months

=== DISTRESS INDICATORS ===
Distress Level: LOW
Active Indicators: 0
"""

    # Our comprehensive framework prompt
    framework_prompt = """You are the BEST REAL ESTATE AGENT OF ALL TIME with 30+ years of experience in distressed property acquisition and investment. You have an unparalleled ability to identify opportunity in distressed real estate markets and have generated millions in profits through expert property analysis.

Please analyze the following comprehensive property data using your world-class expertise and the complete distress factor framework:

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
{
    "distress_score": [0-100],
    "confidence_level": [0-100], 
    "valuation_discount": "[X-Y%]",
    "explanation": "[2-3 sentence detailed explanation referencing specific distress factors]"
}"""

    # Combine for full prompt
    full_prompt = framework_prompt + "\n\n" + sample_formatted_data
    
    # Calculate tokens
    prompt_tokens = estimate_tokens(full_prompt)
    
    # Typical response tokens (JSON + explanation)
    typical_response = """{
    "distress_score": 52,
    "confidence_level": 83,
    "valuation_discount": "12-18%",
    "explanation": "MODERATE-HIGH distress driven by Environmental & Structural Risk factors: Ocean Proximity + FL SB-4D regulations create emotional burnout from potential special assessments and re-certification requirements in post-Surfside environment. Building Age considerations and Condition & Market signals from absentee ownership patterns compound urgency. Strong investment opportunity due to regulatory fear exceeding actual financial impact."
}"""
    
    response_tokens = estimate_tokens(typical_response)
    
    return prompt_tokens, response_tokens

def calculate_costs():
    """Calculate costs for different usage scenarios"""
    
    prompt_tokens, response_tokens = calculate_prompt_tokens()
    total_tokens = prompt_tokens + response_tokens
    
    # GPT-4o pricing (as of 2024)
    input_cost_per_1k = 0.005   # $0.005 per 1K input tokens
    output_cost_per_1k = 0.015  # $0.015 per 1K output tokens
    
    input_cost = (prompt_tokens / 1000) * input_cost_per_1k
    output_cost = (response_tokens / 1000) * output_cost_per_1k
    total_cost = input_cost + output_cost
    
    print("🧮 TOKEN USAGE ANALYSIS FOR AI DISTRESS ANALYZER")
    print("=" * 60)
    
    print(f"\n📊 PER PROPERTY ANALYSIS:")
    print(f"Input Tokens: {prompt_tokens:,} tokens")
    print(f"Output Tokens: {response_tokens:,} tokens") 
    print(f"Total Tokens: {total_tokens:,} tokens")
    
    print(f"\n💰 COST PER PROPERTY:")
    print(f"Input Cost: ${input_cost:.4f}")
    print(f"Output Cost: ${output_cost:.4f}")
    print(f"Total Cost: ${total_cost:.4f}")
    
    print(f"\n📈 VOLUME ANALYSIS:")
    volumes = [1, 10, 50, 100, 500, 1000]
    
    for volume in volumes:
        volume_cost = total_cost * volume
        volume_tokens = total_tokens * volume
        
        if volume_tokens >= 1000000:
            tokens_display = f"{volume_tokens/1000000:.1f}M"
        elif volume_tokens >= 1000:
            tokens_display = f"{volume_tokens/1000:.0f}K"
        else:
            tokens_display = f"{volume_tokens}"
            
        print(f"{volume:4d} properties: {tokens_display:>6} tokens = ${volume_cost:6.2f}")
    
    print(f"\n⚠️  RATE LIMITS (GPT-4o):")
    print(f"• Requests: 5,000 per minute")
    print(f"• Tokens: 800,000 per minute") 
    print(f"• Daily: 10,000,000 tokens")
    
    properties_per_minute = 800000 // total_tokens
    properties_per_day = 10000000 // total_tokens
    
    print(f"\n🚀 THROUGHPUT ESTIMATES:")
    print(f"• Max properties/minute: {properties_per_minute}")
    print(f"• Max properties/day: {properties_per_day:,}")
    
    print(f"\n💡 OPTIMIZATION TIPS:")
    print(f"• Batch mode (3 properties): ~{total_tokens * 2.5 / 3:.0f} tokens/property")
    print(f"• Reduce framework detail: ~{total_tokens * 0.7:.0f} tokens/property")
    print(f"• Shorter responses: ~{total_tokens * 0.8:.0f} tokens/property")

if __name__ == "__main__":
    calculate_costs() 