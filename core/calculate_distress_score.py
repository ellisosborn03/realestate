#!/usr/bin/env python3

def calculateDistressScore(data):
    """
    Calculate distress score as a weighted percentage based on predefined signal weights.
    Backward compatible: checks both old and new field names.
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
        (get_bool('preforeclosure', 'preforeclosureActive'), 5),
        (get_bool('below_avm_sale', 'belowAVMSale'), 4),
        (get_num('days_on_market', 'daysOnMarket', default=0) > 90, 4),
        (get_bool('frequent_price_drops', 'frequentPriceDrops'), 4),
        (get_bool('tax_delinquent', 'taxDelinquent'), 4),
        (get_num('building_age', 'buildingAge', default=0) > 30, 3),
        (get_num('tax_to_value', 'taxToValue', default=0) > 0.03, 3),
        (get_bool('no_permits_5yr', 'noPermits5yr'), 3),
        (get_num('ownership_years', 'ownershipYears', default=0) > 15, 3),
        (get_num('crime_index', 'crimeIndex', default=0) > 70, 3),
        (get_num('median_income', 'medianIncome', default=1e6) < 50000, 3),
        (get_num('vacancy_rate', 'vacancyRate', default=0) > 10, 2),
        (get_num('unemployment', 'unemploymentRate', default=0) > 8, 2),
        (get_bool('hazard_area', 'hazardArea'), 2),
        (get_bool('rent_below_mortgage', 'rentBelowMortgage'), 2),
        (get_bool('missing_unit_number', 'missingUnitNumber'), 1),
        (get_bool('absentee_owner', 'absenteeOwner'), 1),
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