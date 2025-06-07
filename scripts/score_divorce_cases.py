import asyncio
import httpx
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
ATTOM_API_KEY = os.getenv("ATTOM_API_KEY")

DISTRESS_WEIGHTS = {
    'preforeclosure': 5,
    'below_avm_sale': 4,
    'long_dom': 4,
    'price_drops': 4,
    'tax_delinquency': 4,
    'old_building': 3,
    'high_tax_to_value': 3,
    'no_permits': 3,
    'long_ownership': 3,
    'high_crime': 3,
    'low_income': 3,
    'high_vacancy': 2,
    'high_unemployment': 2,
    'hazard_area': 2,
    'rent_lt_mortgage': 2,
    'missing_unit': 1,
    'absentee_owner': 1,
}

def parse_address(line):
    # Try to split on first comma for address1/address2
    parts = line.split(',', 1)
    if len(parts) == 2:
        address1 = parts[0].strip()
        address2 = parts[1].strip()
        return address1, address2
    return line.strip(), ''

async def fetch_attom(client, endpoint, params):
    url = f"https://api.gateway.attomdata.com/propertyapi/v1.0.0/{endpoint}"
    headers = {"accept": "application/json", "apikey": ATTOM_API_KEY}
    try:
        resp = await client.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

async def analyze_address(address_line, client):
    address1, address2 = parse_address(address_line)
    params = {"address1": address1, "address2": address2}
    result = {"address": f"{address1}, {address2}"}
    flags = []
    score = 0
    # 1. /property/detail
    prop = await fetch_attom(client, "property/detail", params)
    year_built = None
    geo_id = None
    if prop and 'property' in prop and prop['property']:
        p = prop['property'][0]
        year_built = p.get('yearBuilt')
        geo_id = p.get('geoIdV4')
        if year_built and year_built < 1994:
            score += DISTRESS_WEIGHTS['old_building']
            flags.append('Building age > 30')
    # 2. /saleshistory/expandedhistory
    sales_hist = await fetch_attom(client, "saleshistory/expandedhistory", params)
    preforeclosure = False
    if sales_hist and 'property' in sales_hist and sales_hist['property']:
        events = sales_hist['property'][0].get('event', [])
        for e in events:
            if e.get('eventType', '').lower() == 'preforeclosure':
                preforeclosure = True
        if preforeclosure:
            score += DISTRESS_WEIGHTS['preforeclosure']
            flags.append('Pre-Foreclosure')
        if len(events) > 1:
            try:
                years = abs(pd.to_datetime(events[0]['eventDate']) - pd.to_datetime(events[-1]['eventDate'])).days / 365
                if years > 15:
                    score += DISTRESS_WEIGHTS['long_ownership']
                    flags.append('Ownership > 15 years')
            except Exception:
                pass
        prices = [e.get('price') for e in events if e.get('price')]
        if len(prices) >= 2 and any(prices[i] > prices[i+1] for i in range(len(prices)-1)):
            score += DISTRESS_WEIGHTS['price_drops']
            flags.append('Frequent price drops')
    # 3. /sale/detail + /attomavm/detail
    sale = await fetch_attom(client, "sale/detail", params)
    avm = await fetch_attom(client, "attomavm/detail", params)
    sale_price = None
    avm_value = None
    if sale and 'property' in sale and sale['property']:
        sale_price = sale['property'][0].get('sale', {}).get('saleAmount')
    if avm and 'property' in avm and avm['property']:
        avm_value = avm['property'][0].get('avm', {}).get('amount', {}).get('value')
    if sale_price and avm_value and sale_price < avm_value:
        score += DISTRESS_WEIGHTS['below_avm_sale']
        flags.append('Below AVM sale')
    # 4. /assessment/detail
    assess = await fetch_attom(client, "assessment/detail", params)
    tax_amt = None
    assessed_val = None
    if assess and 'property' in assess and assess['property']:
        tax_amt = assess['property'][0].get('assessment', {}).get('tax', {}).get('taxamt')
        assessed_val = assess['property'][0].get('assessment', {}).get('assdttlvalue')
    if tax_amt and assessed_val and assessed_val > 0:
        tax_to_value = (tax_amt / assessed_val) * 100
        if tax_to_value > 3:
            score += DISTRESS_WEIGHTS['high_tax_to_value']
            flags.append('Tax-to-value > 3%')
    # 5. /buildingpermits
    permits = await fetch_attom(client, "buildingpermits", params)
    recent_permit = False
    if permits and 'permit' in permits:
        for permit in permits['permit']:
            try:
                years_ago = (pd.Timestamp.now() - pd.to_datetime(permit['permitissuedate'])).days / 365
                if years_ago < 5:
                    recent_permit = True
            except Exception:
                continue
    if not recent_permit:
        score += DISTRESS_WEIGHTS['no_permits']
        flags.append('No permits in last 5 years')
    # 6. /neighborhood/community
    if prop and 'property' in prop and prop['property']:
        geo_id = prop['property'][0].get('geoIdV4')
        if geo_id:
            neigh = await fetch_attom(client, "neighborhood/community", {"geoIdV4": geo_id})
            if neigh and 'neighborhood' in neigh and neigh['neighborhood']:
                n = neigh['neighborhood'][0]
                if n.get('household_median_income', 999999) < 50000:
                    score += DISTRESS_WEIGHTS['low_income']
                    flags.append('Median income < $50k')
                if n.get('crime_index_total', 0) > 70:
                    score += DISTRESS_WEIGHTS['high_crime']
                    flags.append('High crime index')
                if n.get('vacant_housing_units_pct', 0) > 10:
                    score += DISTRESS_WEIGHTS['high_vacancy']
                    flags.append('Vacancy rate > 10%')
                if n.get('unemployment_rate', 0) > 8:
                    score += DISTRESS_WEIGHTS['high_unemployment']
                    flags.append('Unemployment > 8%')
    # 7. /valuation/rentalavm + /property/detailmortgage
    rent = await fetch_attom(client, "valuation/rentalavm", params)
    mortgage = await fetch_attom(client, "property/detailmortgage", params)
    rent_val = None
    mortgage_val = None
    if rent and 'property' in rent and rent['property']:
        rent_val = rent['property'][0].get('rentalAVM', {}).get('rentalValue')
    if mortgage and 'property' in mortgage and mortgage['property']:
        mortgage_val = mortgage['property'][0].get('mortgage', {}).get('monthlyPayment')
    if rent_val and mortgage_val and rent_val < mortgage_val:
        score += DISTRESS_WEIGHTS['rent_lt_mortgage']
        flags.append('Rent < mortgage')
    # 8. Tax delinquency (from lien history in saleshistory/expandedhistory)
    if sales_hist and 'property' in sales_hist and sales_hist['property']:
        liens = sales_hist['property'][0].get('lien', [])
        for lien in liens:
            if lien.get('lientype', '').lower() == 'tax':
                score += DISTRESS_WEIGHTS['tax_delinquency']
                flags.append('Tax delinquency')
                break
    # 9. Days on market (from sale/detail)
    if sale and 'property' in sale and sale['property']:
        dom = sale['property'][0].get('sale', {}).get('daysOnMarket')
        if dom and dom > 90:
            score += DISTRESS_WEIGHTS['long_dom']
            flags.append('Days on market > 90')
    # 10. Absentee owner (mailing != site address)
    if prop and 'property' in prop and prop['property']:
        mailing = prop['property'][0].get('mailingAddress', {}).get('oneLine')
        site = prop['property'][0].get('address', {}).get('oneLine')
        if mailing and site and mailing != site:
            score += DISTRESS_WEIGHTS['absentee_owner']
            flags.append('Absentee owner')
    # 11. Missing unit number (optional)
    if address1 and not any(x in address1.lower() for x in ['apt', 'unit', '#']) and any(c.isdigit() for c in address1):
        score += DISTRESS_WEIGHTS['missing_unit']
        flags.append('Missing unit number')
    # 12. Hazard area (not implemented)
    result['distress_score'] = score
    result['flags'] = ', '.join(flags)
    result['discount'] = f"{min(30, score*2)}%"
    return result

async def main():
    with open('core/tests/test_addresses.txt') as f:
        addresses = [line.strip() for line in f if line.strip()]
    async with httpx.AsyncClient() as client:
        tasks = [analyze_address(addr, client) for addr in addresses]
        results = await asyncio.gather(*tasks)
    df = pd.DataFrame(results)
    df = df.sort_values('distress_score', ascending=False)
    print(df[['address', 'distress_score', 'flags', 'discount']].to_string(index=False))

if __name__ == "__main__":
    asyncio.run(main()) 