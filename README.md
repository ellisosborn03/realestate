# Real Estate Distress Analysis System

## Overview

An advanced property distress analysis system that identifies motivated sellers and potential real estate investment opportunities. The system integrates multiple data sources including ATTOM Data API, court records, and public property databases to provide comprehensive distress scoring.

## Enhanced Distress Algorithm v2.0

### Data Sources Integration

#### Primary Data Sources:
1. **ATTOM Data API** - Comprehensive property data including:
   - Property valuation (AVM)
   - Sales history and price trends
   - Property characteristics (age, size, type)
   - Tax assessments and liens
   - Owner occupancy status
   - Mortgage and deed information

2. **Court Records** - Divorce case data including:
   - Case type (contested vs. uncontested)
   - Case duration and complexity
   - Child involvement
   - Court-ordered deadlines

3. **Public Records** - Property distress indicators:
   - Code violations
   - Building permits status
   - Tax delinquency
   - Lien information

### Distress Scoring Algorithm

The enhanced algorithm evaluates properties across **6 major categories** with a maximum score of 100:

#### 1. Divorce-Specific Factors (50 points max)
**High Impact Indicators:**
- **Court-ordered sale timeline** (20 points) - Properties with forced sale deadlines
- **Dual mortgage obligations** (8 points) - Both spouses on mortgage creating financial strain
- **High legal fee burden** (7 points) - Average Florida divorce costs $15k+
- **Child support obligations** (8 points) - Additional financial pressure
- **Spousal support orders** (7 points) - Income reduction for paying spouse
- **Contested divorce case** (6 points) - Higher complexity and costs
- **Extended case duration** (4 points) - Cases over 12 months indicate complexity

#### 2. Property-Specific Factors (30 points max)
**Real Property Data from ATTOM API:**
- **High-value property assessment** (5 points) - Properties >$500k have higher legal implications
- **Required equity split** (6 points) - Forced liquidation scenarios
- **Property age and condition** (8 points):
  - Properties >30 years old (5 points)
  - Properties >50 years old (additional 3 points)
- **Owner occupancy status** (8 points) - Non-owner occupied properties indicate investment stress
- **Property value vs. debt analysis** (6 points) - Underwater mortgage identification

#### 3. Tax and Lien Analysis (12 points max)
**Assessment and Tax Data:**
- **High tax burden** (6 points) - Tax rates >3% of assessed value
- **Tax delinquency indicators** (6 points) - Properties with overdue taxes
- **Assessment vs. market value gaps** - Indicates valuation uncertainty

#### 4. Market Activity and Sales History (10 points max)
**Historical Sales Data:**
- **Frequent property turnover** (4 points) - More than 3 sales indicating issues
- **Recent purchase patterns** (3 points) - Potential flips or quick sales
- **Long-term ownership** (2 points) - Emotional attachment factors
- **Price appreciation trends** (8 points):
  - Declining value >10% (8 points)
  - Negative appreciation (4 points)

#### 5. Valuation Uncertainty (6 points max)
**AVM Confidence Indicators:**
- **Low confidence scores** (3 points) - ATTOM AVM confidence <70%
- **Wide valuation ranges** (3 points) - High-low spread >20% indicates uncertainty

#### 6. Market Timing and Conditions (10 points max)
**Local Market Analysis:**
- **Buyer's market conditions** (6 points) - Market favors buyers
- **Seasonal timing challenges** (4 points) - Selling during slow seasons
- **Market absorption rates** (3 points) - Days on market >75 days expected
- **Urgent sale deadlines** (10 points) - Court deadlines <120 days

### Risk Level Classification

Based on total distress score:

- **CRITICAL (85-100 points)**: 25-35% discount potential
  - Immediate forced sale scenarios
  - Multiple high-impact factors
  - Court deadlines <90 days

- **HIGH (70-84 points)**: 15-25% discount potential
  - Significant financial pressure
  - Property-specific distress indicators
  - Market timing challenges

- **MEDIUM-HIGH (55-69 points)**: 10-20% discount potential
  - Moderate distress factors
  - Some urgency indicators
  - Property condition issues

- **MEDIUM (40-54 points)**: 5-15% discount potential
  - Basic divorce-related pressure
  - Standard market conditions
  - Minor property factors

- **LOW (<40 points)**: 0-10% discount potential
  - Minimal distress indicators
  - Favorable market conditions
  - Well-maintained properties

### Example Analysis Output

```
Property: 123 Main St, West Palm Beach, FL 33467
Distress Score: 87 (CRITICAL)
Discount Potential: 25-35%

Key Factors:
- $850,000 high-value property
- 90-day court deadline
- 18-month case duration
- $12,400 tax burden
- 45-year property
- Court-ordered sale
- Dual mortgage obligations
- Extended case duration
- Contested divorce
- Buyer's market

Explanation: "25-35% discount from $850,000 high-value property, 90-day court deadline, 18-month case duration, $12,400 tax burden, 45-year property."
```

### Data Quality and Confidence

The system provides confidence scores based on:
- **Real property data availability** (ATTOM API coverage)
- **Recent sales comparables** (market validation)
- **Number of distress factors identified**
- **Data source reliability**

Confidence levels:
- **95%+**: Multiple verified data sources
- **85-94%**: ATTOM data + court records
- **75-84%**: Limited data sources
- **<75%**: Minimal data availability

### Integration APIs

#### ATTOM Data Endpoints Used:
1. `/propertyapi/v1.0.0/attomavm/detail` - Property valuation
2. `/propertyapi/v1.0.0/property/detailmortgage` - Comprehensive property data
3. `/propertyapi/v1.0.0/saleshistory/detail` - Sales history and trends

#### Future Enhancements:
- MLS integration for days on market data
- Code violation databases
- Foreclosure filing databases
- Mechanic lien searches
- Property condition assessments

## Technical Implementation

### Core Components:
- **DivorceLeadAnalyzer**: Main analysis engine
- **Enhanced ATTOM API integration**: Multi-endpoint data collection
- **Distress scoring algorithm**: 6-category evaluation system
- **Market analysis module**: Local market condition assessment
- **Explanation generator**: Concise, data-driven summaries

### File Structure:
```
├── divorce_lead_analyzer.py    # Enhanced analysis engine
├── app.py                     # Flask web application
├── flexible_divorce_processor.py  # Batch processing
├── templates/
│   └── distress_dashboard.html    # Web interface
└── uploads/                   # Excel data files
```

### Usage:
```python
analyzer = DivorceLeadAnalyzer()
result = analyzer.analyze_divorce_lead("123 Main St, City, FL 12345")
```

## Installation & Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export ATTOM_API_KEY="your_attom_api_key"
export OPENAI_API_KEY="your_openai_key"
```

3. Run the application:
```bash
python app.py
```

4. Access dashboard at: `http://localhost:5001/distress-dashboard`

## Features

### Dashboard Capabilities:
- **Multi-select source file filtering** - Checkbox-based file selection
- **Risk level filtering** - Filter by CRITICAL, HIGH, MEDIUM-HIGH, etc.
- **Analysis type filtering** - Focus on specific distress categories
- **Export functionality** - CSV export of filtered results
- **Real-time analysis** - Process new addresses instantly

### Batch Processing:
- **Excel file processing** - Handle large datasets
- **Progress tracking** - Monitor analysis progress
- **Error handling** - Robust data validation
- **Database storage** - SQLite for result persistence

This enhanced system provides institutional-grade property distress analysis with real market data integration, enabling precise identification of motivated seller opportunities in the divorce market segment. 