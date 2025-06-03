# Florida Property Distress Score – Core Model (ATTOM-Only)

**Purpose:**
Compute a property distress score (0–100) for Florida residential real estate leads using only ATTOM APIs. All input addresses are pre-qualified as divorce-related, so no need to include a divorce flag. The model identifies financial, structural, and market-based seller distress using property-level and neighborhood-level data from ATTOM.

---

## ✅ Inputs

* Street address, city, state, zip

---

## 🔌 ATTOM API Endpoints Used

* `/property/detail` – basic property info (year built, property type)
* `/attomavm/detail` – estimated property value (AVM)
* `/mortgage/detail` – current mortgage amount
* `/sale/snapshot` – local market trends (median DOM, inventory, turnover)
* `/sale/comparable` – price change history, DOM
* `/neighborhood/detail` – income, education, vacancy
* `/neighborhood/crime` – crime index
* `/neighborhood/hazard` – environmental risk (flood, hurricane, wind)

---

## 📊 Distress Score Formula (Normalized 0–100)

| Metric                    | Weight | Description                                                               |
| ------------------------- | ------ | ------------------------------------------------------------------------- |
| Loan-to-Value Ratio (LTV) | 25%    | Higher LTV = more financial pressure (Mortgage ÷ AVM)                     |
| DOM vs Median (DOM Index) | 15%    | Longer time-on-market signals trouble (Listing DOM ÷ Median DOM)          |
| Price Reduction Index     | 15%    | More/faster price drops = seller urgency (from comparable sales)          |
| Foreclosure Indicator     | 10%    | Presence of any pre-foreclosure/REO info                                  |
| Neighborhood Hazard Risk  | 10%    | High risk = fewer buyers, higher insurance, lower marketability           |
| Year Built Risk           | 10%    | Older buildings may face engineering/legal scrutiny in FL (e.g., >30 yrs) |
| Crime Rate Index          | 5%     | Higher crime = lower buyer demand, lower appraisal risk tolerance         |
| Income & Vacancy Factors  | 10%    | Low income + high vacancy area = market stress and fewer qualified buyers |

---

## 📈 Output

```json
{
  "address": "123 Ocean Dr, Miami Beach, FL",
  "distress_score": 78,
  "estimated_discount_range": "10–15%",
  "risk_breakdown": {
    "ltv": 23,
    "dom_index": 12,
    "price_cuts": 15,
    "foreclosure": 8,
    "hazard_risk": 7,
    "building_age": 5,
    "crime": 4,
    "income_vacancy": 4
  }
}
```

---

## 🧪 Best Used For:

* Quick distress analysis with zero 3rd-party setup
* Consistent results across all addresses using existing ATTOM access 