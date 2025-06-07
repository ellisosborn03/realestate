#!/usr/bin/env python3

def calculateDistressScore(data):
    """
    Calculate distress score as a weighted percentage based on the new risk factor table.
    Only output distress_score (X/100) and confidence. No discount bands.
    """
    def get_bool(*keys):
        for k in keys:
            v = data.get(k)
            if isinstance(v, bool): return v
            if isinstance(v, (int, float)): return v != 0
        return False
    def get_num(*keys, default=0):
        for k in keys:
            v = data.get(k)
            if v is not None: return v
        return default
    signals = [
        (get_bool('court_ordered_sale_timeline'), 5),
        (get_bool('dual_mortgage_obligations'), 4),
        (get_bool('high_legal_fee_burden'), 4),
        (get_bool('child_support_obligations'), 3),
        (get_bool('spousal_support_orders'), 3),
        (get_bool('contested_divorce_case'), 3),
        (get_bool('extended_case_duration_18mo'), 3),
        (get_bool('required_equity_split'), 2),
        (get_bool('high_value_property'), 2),
        (get_bool('buyers_market_conditions'), 2),
        (get_bool('urgent_sale_deadline_90d'), 2),
        (get_bool('seasonal_timing_challenges'), 1),
        (get_bool('property_over_30_years'), 1),
        (get_bool('flood_or_coastal_risk'), 1),
    ]
    # Debug print for first property
    import os
    if os.environ.get('DEBUG_DISTRESS_SCORE', '1') == '1':
        print('\n[DEBUG] Incoming data:', data, flush=True)
        print('[DEBUG] Triggered signals:', [(i, s[1]) for i, s in enumerate(signals) if s[0]], flush=True)
    total_weight = sum(w for _, w in signals)
    triggered = sum(w for cond, w in signals if cond)
    distress_score = round((triggered / total_weight) * 100) if total_weight else 0
    return {
        'distress_score': distress_score,
        'confidence': 95
    } 