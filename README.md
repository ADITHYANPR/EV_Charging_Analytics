# Data-Driven Analytics for EV Charging Demand Forecasting and Anomaly Detection in Smart Grids

An academic research software system and interactive analytics dashboard built on the Caltech Adaptive Charging Network (ACN-Data) dataset.

---

## 1. Project Overview & Research Questions

Electrification of passenger transportation presents substantial challenges and flexibility opportunities for smart electrical distribution networks. This project builds an empirical, data-driven analytics system that quantifies EV charging behaviors, forecasts future aggregated EV energy demand, identifies statistical charging anomalies, and evaluates smart-grid demand management potential.

### Research Questions
* **RQ1 (Charging Behavior):** What temporal and behavioral patterns exist in real-world EV charging sessions?
* **RQ2 (Demand Dynamics):** How does EV charging energy demand vary across diurnal hours, weekdays, weekends, and COVID-19 restriction periods?
* **RQ3 (Demand Forecasting):** How accurately can future aggregated hourly EV charging energy demand be forecast using regularized linear and gradient boosted machine learning models?
* **RQ4 (Anomaly Detection):** Can statistical outliers and unusual charging sessions be isolated using unsupervised learning (Isolation Forest and Local Outlier Factor) without ground-truth labels?
* **RQ5 (Smart-Grid Insights):** How can empirical dwell-time idle buffers and demand forecasting inform site-level demand management and grid integration?

> **Academic Terminology Notice:** The system distinguishes between **aggregated EV charging energy demand** across the study site and total utility-grid load. Outliers are strictly described using neutral statistical terminology (*"anomalous session"*, *"unusual charging behavior"*) rather than asserting unverified claims of fraud or hardware failure.

---

## 2. Dataset Description & Ground Truth

* **Data Source:** Caltech Adaptive Charging Network (ACN-Data Garage Site `0002`, Station Cluster `0039`).
* **Raw Dataset:** `data/raw/acn_caltech_5000.json` (SHA-256 Digest: `1f567bffbc947673...`, verified read-only).
* **Sample Size:** Exactly `5,000` real EV charging sessions (100% preserved; 0 dropped).
* **Coverage Horizon (Local California Time):** **January 21, 2020 (20:23 PST)** to **September 13, 2021 (18:52 PDT)**.
* **Registered vs Unregistered:** 4,410 registered sessions with driver app preferences; 590 guest sessions (explicitly preserved with `is_registered_user = 0` and `user_id_clean = 'ANONYMOUS'`).
* **Continuous Hourly Grid:** 14,422 continuous intervals in `America/Los_Angeles` local time, preserving zero-demand periods (79.14% of hours) without artificial omissions.
* **Total Energy Delivered:** Exactly **53,668.78 kWh** (53.67 MWh), conserved identically across session records and continuous hourly demand aggregations.

---

## 3. Project Architecture & Modular Structure

```text
EV_Charging_Analytics/
├── data/
│   ├── raw/
│   │   └── acn_caltech_5000.json       # Untouched original raw dataset (SHA-256 verified)
│   └── processed/
│       ├── cleaned_sessions.csv        # 5,000 session records with 56 engineered features
│       └── hourly_demand.csv           # 14,422 continuous hourly intervals with lag/rolling features
├── src/
│   ├── __init__.py                     # Package metadata
│   ├── data_loader.py                  # Read-only ingestion and schema validation
│   ├── preprocessing.py               # Flattening, missing indicators, PST/PDT timezone standardization
│   ├── feature_engineering.py         # Session behavioral features & leak-free time-series lags
│   ├── eda.py                         # 12 publication-quality figures & 5 summary tables
│   ├── demand_analysis.py             # Diurnal demand profiles and station utilization
│   ├── forecasting.py                 # Strict chronological splitting, Baselines, Ridge, RF, XGBoost
│   ├── anomaly_detection.py           # Isolation Forest, LOF, consensus, profiling, explanations
│   └── evaluation.py                  # MAE, RMSE, MSE, R², sMAPE, Jaccard agreement metrics
├── dashboard/
│   ├── __init__.py
│   └── app.py                         # 6-section Streamlit research dashboard
├── models/                            # Serialized model artifacts (.joblib)
├── outputs/
│   ├── figures/                       # 27 publication-quality figures (300 DPI, PNG)
│   ├── tables/                        # 14 formatted empirical CSV summary tables
│   └── results/                       # Test forecast predictions and session anomaly scores
├── tests/
│   ├── test_structure.py              # Architecture and module functionality tests
│   ├── test_phase4.py                 # Preprocessing and row preservation tests
│   ├── test_forecasting.py            # Chronological splitting and zero-leakage tests
│   ├── test_anomaly.py                # Anomaly scoring and consensus tests
│   └── test_dashboard.py              # System integration and KPI alignment tests
├── requirements.txt                   # Frozen dependency specifications
├── README.md                          # Research documentation
└── main.py                            # CLI orchestration pipeline entrypoint
```

---

## 4. Analytical Components & Methodologies

### A. Preprocessing & Quality Assurance
* **Timestamp Standardization:** Raw RFC 2822 GMT timestamps are parsed to UTC and converted to `America/Los_Angeles` local time, correctly capturing Daylight Saving Time transitions (PST UTC-8 / PDT UTC-7).
* **Missing Value Transparency:** Explicit flags (`is_charging_completed`, `has_user_inputs`, `is_registered_user`) are created without silently dropping sessions.
* **Sensor Edge Cases Handled:**
  * 1 session with negative charging duration (-9s) floored to 0.0 with documentation flag.
  * 76 sessions with disconnect preceding completion flag captured; idle duration computed as $\max(0, \text{connection} - \text{charging})$.
  * 255 sessions with delivered energy exceeding requested energy flagged with `energy_error_kwh`.

### B. Time-Series Demand Forecasting (Strict Zero-Leakage)
* **Chronological Partitions:**
  * **Train Set:** Jan 21, 2020 – Apr 30, 2021 ($n=10,995$ clean hours post-$lag_{168}$).
  * **Validation Set:** May 01, 2021 – Jun 30, 2021 ($n=1,464$ hours, **used solely for model selection**).
  * **Test Set:** Jul 01, 2021 – Sep 13, 2021 ($n=1,795$ untouched holdout hours).
* **Predictor Feature Space:** 22 features including calendar cyclical encodings, pure autoregressive lags ($t-1, t-2, t-3, t-24, t-48, t-168$), and strictly shifted rolling statistics ($\text{shift}(1)$).
* **Benchmark Results (Table 6):**
  * **Selected Model:** **Ridge Regression** ($\alpha=10.0$) selected on Validation RMSE (**13.168 kWh** vs 13.267 kWh for XGBoost, 17.156 kWh for Naive 168h).
  * **Test Performance:** Test MAE = **9.120 kWh**, Test RMSE = **15.713 kWh**, Test $R^2$ = **0.1158**, Test sMAPE = **152.89%**.
  * **XGBoost Regressor:** Test MAE = **9.331 kWh**, Test RMSE = **15.633 kWh**, Test $R^2$ = **0.1248**, Test sMAPE = **153.22%**.
  * Both ML models reduce RMSE by **23%–25%** over naive persistence baselines ($R^2 < 0$).

### C. Unsupervised Anomaly Detection
* **Feature Space:** 12 session variables (`kWhDelivered`, `connection_duration_hr`, `charging_duration_hr`, `idle_duration_hr`, `average_charging_rate_kw`, `energy_error_kwh`, `delivery_ratio`, `idle_to_connection_ratio`, `conn_hour`, `minutesAvailable`, `milesRequested`, `WhPerMile`). Identifiers are strictly excluded.
* **Preconditioning:** Median imputation + `RobustScaler` (median & IQR normalization).
* **Algorithms:**
  * **Isolation Forest (iForest):** 150 trees, contamination = 0.03 (150 outliers).
  * **Local Outlier Factor (LOF):** $k=25$ neighbors, contamination = 0.03 (150 outliers).
* **Consensus Agreement:**
  * 33 consensus anomalies flagged by both methods (0.66% of network).
  * 95.32% overall binary agreement across all 5,000 sessions.
  * Consensus anomalies exhibit **4.87$\times$ higher median energy** ($30.7\text{ kWh}$ vs $6.3\text{ kWh}$) and **7.23$\times$ higher median idle stall blockage** ($9.26\text{ hr}$ vs $1.28\text{ hr}$).

---

## 5. Streamlit Dashboard Structure

Run interactively from the project root:
```bash
streamlit run dashboard/app.py
```

### Dashboard Sections
1. **Overview & Dataset Health:** High-level operational KPIs, ground-truth temporal scope, and data-quality audit tables.
2. **Charging Behavior (RQ1):** Interactive distributions of energy, connection vs active power duration, arrival hour histograms, and requested-vs-delivered energy.
3. **Demand & Peak Analysis (RQ2):** Continuous aggregated hourly and daily demand timelines, diurnal weekday/weekend profiles, peak demand heatmaps, and COVID regime comparisons.
4. **Demand Forecasting (RQ3):** Actual vs forecast test horizon timelines, model benchmark comparison tables, residual error distributions, and stratified performance by demand level.
5. **Anomaly Detection (RQ4):** Score distributions, iForest vs LOF agreement scatter, consensus feature profiles, and top ranked anomalous sessions with domain explanations.
6. **EV Charging Demand and Potential Smart-Grid Implications (RQ5):** Grounded discussion of morning EV charging demand concentration, quantified idle dwell-time flexibility buffers (median 1.30 idle hours), and demand management potential without claims of unmeasured grid/transformer loading.

---

## 6. Installation & Execution Instructions

### Prerequisites
* Python 3.10 to 3.13
* Virtual environment (recommended)

### Installation
```bash
# Clone or navigate to the repository
cd EV_Charging_Analytics

# Install required dependencies
pip install -r requirements.txt
```

### Pipeline Execution via CLI
```bash
# Verify system architecture and raw data integrity
python main.py --phase verify

# Execute data preprocessing and build hourly demand dataset
python main.py --phase preprocess

# Generate all 12 EDA publication figures and 5 descriptive tables
python main.py --phase eda

# Run demand forecasting pipeline (train, validate, test, residuals, figures)
python main.py --phase forecast

# Run unsupervised anomaly detection pipeline (iForest, LOF, consensus, profiles)
python main.py --phase anomaly
```

### Launch Interactive Research Dashboard
```bash
streamlit run dashboard/app.py
```

### Run Complete Test Suite
```bash
pytest tests/ -v
```
* **Test Suite Status:** 34 unit and integration tests passing (100% success rate across structure, preprocessing, forecasting, anomaly detection, energy conservation, and dashboard integration).

---

## 7. Reproducibility & Research Integrity

* **Random Seed:** Fixed seed (`random_state=42`) configured across train/val splitting, Ridge Regression, Random Forest, XGBoost, and Isolation Forest.
* **No Fabricated Data:** Every figure, table, metric, and percentage is computed directly from `acn_caltech_5000.json`.
* **Zero Target Leakage:** Lag features and rolling statistics strictly use information available prior to prediction timestamp $t$.
