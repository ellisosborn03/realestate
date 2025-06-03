# Florida Property Distress Score – Enhanced Model (ATTOM + Public APIs)

**Purpose:**
Compute a more granular and context-aware distress score by combining ATTOM data with public external APIs. This version includes employment, health, code violations, and environmental factors not available in ATTOM alone. Still assumes all inputs are divorce-driven.

---

## ✅ Inputs

* Street address, city, state, zip

---

## 🔌 Integrated APIs

* **ATTOM:** all endpoints from the core model
* **BLS API:** unemployment rate by zip
* **CDC PLACES:** zip-level chronic illness & hospitalization prevalence
* **Local Open Data Portals:** code violations (e.g. Miami-Dade, Broward)
* **NOAA or FEMA flood zones:** water proximity and flood risk
* **USPS + LexisNexis (optional):** owner age/occupancy proxies

---

## 📊 Extended Distress Score Formula

| Metric                            | Weight | Description                                                     |
| --------------------------------- | ------ | --------------------------------------------------------------- |
| Loan-to-Value Ratio (LTV)         | 20%    | Measures equity stress                                          |
| Price Drop Behavior               | 15%    | Multiple/rapid drops = higher motivation                        |
| DOM vs Median                     | 10%    | High DOM implies urgency                                        |
| Foreclosure Status                | 10%    | Pre-foreclosure or REO ups score                                |
| Code Violation Presence           | 10%    | Signals deferred maintenance or property neglect                |
| Building Age (>30 years)          | 5%     | Older homes face inspection/legal challenges in FL              |
| Flood Zone + Ocean Proximity Risk | 5%     | High risk = higher insurance and less liquidity                 |
| Neighborhood Hazard Risk (ATTOM)  | 5%     | Includes hurricane/wind/flood composites                        |
| Chronic Health Risk (CDC PLACES)  | 5%     | Community-level health burden implies stress or lower valuation |
| Unemployment Rate (BLS)           | 5%     | Local job loss = more seller hardship or fewer buyers           |
| Crime Index (ATTOM)               | 5%     | High-crime zones sell slower and cheaper                        |
| Median Income + Vacancy (ATTOM)   | 5%     | Low demand zones, often undervalued                             |

---

## 📈 Output

```json
{
  "address": "500 Palm Way, West Palm Beach, FL",
  "distress_score": 87,
  "estimated_discount_range": "15–20%",
  "risk_breakdown": {
    "ltv": 20,
    "price_cuts": 15,
    "dom_index": 10,
    "foreclosure": 8,
    "code_violations": 10,
    "building_age": 4,
    "water_risk": 4,
    "hazard": 4,
    "health_risk": 4,
    "unemployment": 4,
    "crime": 2,
    "income_vacancy": 2
  }
}
```

---

## 🔧 Best Used For:

* Deep prioritization of which distressed properties to pursue
* Surfacing "silent distress" cases where sellers haven't yet dropped price but other indicators point to urgency 