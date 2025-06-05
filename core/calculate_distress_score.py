#!/usr/bin/env python3

def calculateDistressScore(data):
    """
    Python implementation of the distress score calculation algorithm
    Based on the JavaScript version in src/services/calculateDistressScore.js
    """
    
    # Extract input parameters with defaults
    loan_to_value_pct = data.get('loanToValuePct', 0)
    days_on_market = data.get('daysOnMarket', 0)
    median_days_on_market = data.get('medianDaysOnMarket', 1)  # Avoid division by zero
    original_list_price = data.get('originalListPrice', 0)
    current_list_price = data.get('currentListPrice', 0)
    preforeclosure_active = data.get('preforeclosureActive', False)
    tax_delinquent = data.get('taxDelinquent', False)
    absentee_owner = data.get('absenteeOwner', False)
    absorption_rate = data.get('absorptionRate', 0)
    
    # Calculate component scores
    
    # LTV score: 1.0 if LTV > 0.9, else scaled
    ltv_score = 1.0 if loan_to_value_pct >= 0.9 else loan_to_value_pct / 0.9
    
    # DOM score: DOM / median DOM, capped at 2
    dom_score = min(days_on_market / median_days_on_market, 2.0)
    
    # Price reduction score: (original - current) / original
    if original_list_price > 0:
        price_reduction_score = max((original_list_price - current_list_price) / original_list_price, 0)
    else:
        price_reduction_score = 0
    
    # Binary scores
    preforeclosure_score = 1.0 if preforeclosure_active else 0.0
    tax_delinquent_score = 1.0 if tax_delinquent else 0.0
    absentee_score = 1.0 if absentee_owner else 0.0
    
    # Absorption score: 1.0 if > 6 months
    absorption_score = 1.0 if absorption_rate > 6 else absorption_rate / 6
    
    # Calculate weighted distress score
    distress_score = (
        0.25 * ltv_score +
        0.20 * dom_score +
        0.15 * price_reduction_score +
        0.15 * preforeclosure_score +
        0.10 * tax_delinquent_score +
        0.10 * absentee_score +
        0.05 * absorption_score
    ) * 100
    
    # Round and cap at 100
    distress_score = round(min(distress_score, 100))
    
    # Determine estimated discount
    if distress_score < 30:
        estimated_discount = "0–2%"
    elif distress_score < 60:
        estimated_discount = "3–9%"
    elif distress_score < 80:
        estimated_discount = "10–15%"
    else:
        estimated_discount = "15–20%+"
    
    # Build explanation
    reasons = []
    if ltv_score >= 0.9:
        reasons.append('High loan-to-value')
    if dom_score > 1.5:
        reasons.append('Long days on market')
    if price_reduction_score > 0.08:
        reasons.append('Significant price reduction')
    if preforeclosure_active:
        reasons.append('Preforeclosure')
    if tax_delinquent:
        reasons.append('Tax delinquent')
    if absentee_owner:
        reasons.append('Absentee owner')
    if absorption_score > 0.8:
        reasons.append('High absorption rate')
    
    distress_reason = f"Main factors: {', '.join(reasons)}." if reasons else 'No major distress factors detected.'
    
    return {
        'distress_score': distress_score,
        'estimated_discount': estimated_discount,
        'distress_reason': distress_reason
    } 