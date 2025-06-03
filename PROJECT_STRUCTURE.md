# Project Structure

## 📁 Directory Organization

```
realestate/
├── core/                    # Main application
│   ├── app.py              # Flask web application
│   └── templates/          # HTML templates
├── analysis/               # Analysis modules
│   ├── divorce_lead_analyzer.py    # Divorce-specific analysis
│   └── ai_distress_analyzer.py     # AI-powered analysis  
├── data/                   # Data storage
│   └── distress_analysis.db       # SQLite database
├── scripts/                # Utility scripts
│   ├── update_explanations.py     # Update property explanations
│   ├── process_divorce_excel.py   # Process divorce data
│   └── test_dashboard_with_sample_data.py  # Testing
├── src/                    # Core services
│   └── services/
│       └── calculateDistressScore.js  # Distress scoring algorithm
├── __tests__/              # Test files
│   └── distressScore.test.js       # Algorithm tests
├── uploads/                # File uploads
├── docs/                   # Documentation
│   └── README.md          # Project documentation
├── requirements.txt        # Python dependencies  
├── .gitignore             # Git ignore rules
└── run_app.py             # Simple application launcher
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python run_app.py
```

## 📍 Key Files

- **run_app.py** - Start the application
- **core/app.py** - Main Flask application
- **analysis/divorce_lead_analyzer.py** - Divorce analysis logic
- **src/services/calculateDistressScore.js** - Core distress algorithm
- **data/distress_analysis.db** - Property database (486 properties)
