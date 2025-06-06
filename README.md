# Real Estate Distress Analysis System

## Purpose
This app is designed to help real estate investors and analysts identify distressed properties with high potential for profit. It aggregates data from public records (like divorce filings), enriches it with property and valuation data from the ATTOM API, and presents actionable insights in a dashboard. The goal is to streamline the process of finding, analyzing, and acting on distressed real estate leads.

## Features
- **Data Import:** Uploads and processes county data (e.g., divorce records) to generate property leads.
- **ATTOM API Integration:** Enriches leads with property details, AVM (automated valuation model), and comparable sales from ATTOM.
- **Distress Scoring:** Assigns a distress score and risk level to each property based on custom logic.
- **Dashboard:** Interactive web dashboard to filter, sort, and review properties, including expanded details and comparable sales.
- **Manual Analysis:** Allows users to add notes, explanations, and custom analysis to each property.
- **Source Tracking:** Tracks the origin of each lead (file, case, party, etc.).

## How It Works (Function-by-Function)

### 1. Data Import & Processing
- **Excel/CSV Upload:** User uploads county data (e.g., divorce filings).
- **Processing Scripts:** `process_divorce_excel.py` and related scripts parse the data, extract addresses, and create property records in the database.

### 2. Property Enrichment
- **ATTOM Property Lookup:** For each address, the app queries ATTOM's `/property/detail` endpoint to get the PropID and property details.
- **Valuation (AVM):** Uses ATTOM's `/attomavm/detail` to get an estimated property value.
- **Comparable Sales:** Uses `/salescomparables/propid/{propId}` to fetch recent comparable sales for each property.

### 3. Database & API
- **SQLite Database:** Stores all properties, including distress score, risk, value, comparable sales (as JSON), and source info.
- **API Endpoints:**
  - `/api/properties`: Returns all properties for the dashboard.
  - `/api/comparable-sales/<prop_id>`: Returns comparable sales for a given PropID.
  - `/api/comparable-sales-by-address`: (POST) Looks up PropID by address, then fetches comparable sales.
  - `/api/source-files`: Lists uploaded source files.
  - `/api/save-analysis`: Saves manual analysis/notes for a property.

### 4. Dashboard (Frontend)
- **Table View:** Shows all properties with columns for address, ATTOM match, distress score, risk, value, comparable sales, discount potential, and more.
- **Filtering:** Toggle to show only properties with ATTOM data/valuation.
- **Expandable Rows:** Show extra details (case, party, confidence, etc.).
- **Comparable Sales Column:** Shows up to 3 recent comps (price/date) for each property.

### 5. Error Handling & Logging
- **Graceful Fallbacks:** Handles missing ATTOM data, no comps, and API errors with clear UI messages.
- **Logging:** Errors and API failures are logged for debugging.

## Not Implemented Yet (TBD)
- **Full Automation:**
  - The system does not yet automatically buy or import new distress leads from county data sources. Manual upload is required.
  - No automated scraping or API integration with county court systems.
- **Automated Alerts:**
  - No Telegram (or other messaging) bot is implemented yet.
  - The vision is to have a bot that notifies users instantly when a new, high-potential property (e.g., massive discount, high distress score) is detected.
- **Automated Deal Analysis & Offer Generation:**
  - No automated offer calculation or deal submission.
- **Skip Tracing/Phone Append:**
  - No integration with skip-tracing APIs to append owner phone numbers.
- **Production-Ready Deployment:**
  - The app runs in development mode only. No Docker, cloud, or production WSGI setup yet.

## Setup & Usage
1. **Clone the repo:**
   ```sh
   git clone <repo-url>
   cd realestate
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Set up ATTOM API key:**
   - Add your ATTOM API key to your environment or directly in `core/app.py` (not recommended for production).
4. **Run the app:**
   ```sh
   python3 core/app.py
   ```
   - Dashboard: [http://127.0.0.1:5001/distress-dashboard](http://127.0.0.1:5001/distress-dashboard)
5. **Upload data:**
   - Use the dashboard to upload Excel/CSV files with county data.
6. **Review & analyze:**
   - Use the dashboard to review, filter, and analyze properties.

## Contributing
- PRs welcome! Please open issues for bugs or feature requests.

## License
MIT (or specify your license) 