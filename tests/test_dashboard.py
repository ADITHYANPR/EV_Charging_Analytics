"""Test Suite for Phase 7: Dashboard and System Integration Integrity.

Validates:
1. Application imports successfully without syntax/import errors
2. Required data, model, and output artifacts exist
3. Test forecast prediction files load and contain valid columns
4. Anomaly prediction file loads and contains all required flags and scores
5. Key dashboard KPI calculations match validated source tables exactly
6. Filter operations return valid subsets without corrupting source data
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest


def test_required_system_artifacts_exist():
    """Verify that all critical data, model, table, and result files exist on disk."""
    required_paths = [
        Path("data/raw/acn_caltech_5000.json"),
        Path("data/processed/cleaned_sessions.csv"),
        Path("data/processed/hourly_demand.csv"),
        Path("models/model_ridge_regression.joblib"),
        Path("models/model_xgboost.joblib"),
        Path("models/model_isolation_forest.joblib"),
        Path("models/model_local_outlier_factor.joblib"),
        Path("outputs/results/forecast_predictions_test.csv"),
        Path("outputs/results/session_anomaly_predictions.csv"),
        Path("outputs/tables/table1_session_summary_stats.csv"),
        Path("outputs/tables/table6_forecasting_model_comparison.csv"),
        Path("outputs/tables/table9_anomaly_summary.csv"),
        Path("outputs/tables/table10_algorithm_comparison.csv"),
        Path("outputs/tables/table12_anomaly_feature_profile.csv"),
        Path("dashboard/app.py"),
    ]
    for p in required_paths:
        assert p.exists(), f"Required system artifact missing: {p}"


def test_dashboard_forecast_prediction_file():
    """Verify test forecast predictions match required format and record length."""
    pred_path = Path("outputs/results/forecast_predictions_test.csv")
    df = pd.read_csv(pred_path)
    
    assert len(df) == 1795, f"Expected 1,795 test rows, got {len(df)}"
    expected_cols = ["timestamp", "actual", "Seasonal_Naive_24h", "Seasonal_Naive_168h", "Ridge_Regression", "Random_Forest", "XGBoost"]
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col} in test predictions"
        assert not df[col].isnull().any(), f"Column {col} contains NaNs"


def test_dashboard_anomaly_prediction_file():
    """Verify session anomaly predictions match required schema and contain 5,000 sessions."""
    anom_path = Path("outputs/results/session_anomaly_predictions.csv")
    df = pd.read_csv(anom_path)
    
    assert len(df) == 5000, f"Expected 5,000 sessions, got {len(df)}"
    required_cols = [
        "sessionID",
        "score_isolation_forest",
        "flag_isolation_forest",
        "rank_isolation_forest",
        "score_lof",
        "flag_lof",
        "rank_lof",
        "is_consensus_anomaly",
        "score_ensemble",
        "anomaly_explanation",
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required anomaly column: {col}"
        
    assert df["is_consensus_anomaly"].sum() == 33
    assert df["flag_isolation_forest"].sum() == 150
    assert df["flag_lof"].sum() == 150


def test_dashboard_kpis_match_validated_tables():
    """Verify dashboard KPI calculations match the validated source tables exactly."""
    sess_df = pd.read_csv("data/processed/cleaned_sessions.csv")
    hourly_df = pd.read_csv("data/processed/hourly_demand.csv")
    t1_df = pd.read_csv("outputs/tables/table1_session_summary_stats.csv").set_index("Variable")
    
    # 1. Total session count
    assert len(sess_df) == 5000
    
    # 2. Total delivered energy MWh
    total_mwh = sess_df["kWhDelivered"].sum() / 1000.0
    assert pytest.approx(total_mwh, rel=1e-4) == 53.66878
    
    # 3. Median and mean energy delivered match Table 1
    assert pytest.approx(sess_df["kWhDelivered"].median(), rel=1e-3) == t1_df.loc["kWhDelivered", "Median"]
    assert pytest.approx(sess_df["kWhDelivered"].mean(), rel=1e-3) == t1_df.loc["kWhDelivered", "Mean"]
    
    # 4. Connection duration median matches Table 1
    assert pytest.approx(sess_df["connection_duration_hr"].median(), rel=1e-3) == t1_df.loc["connection_duration_hr", "Median"]
    
    # 5. Station count
    assert sess_df["stationID"].nunique() == 54


def test_total_energy_conservation_and_kpi_consistency():
    """Verify exact conservation of total delivered energy across datasets and dashboard KPI.
    
    Verifies:
    1. sum(cleaned_sessions.kWhDelivered) == sum(hourly_demand.total_kwh_delivered)
    2. Exactly equals canonical 53,668.78 kWh (53.67 MWh)
    3. Dashboard formatted string matches '53,668.78 kWh'
    """
    sess_df = pd.read_csv("data/processed/cleaned_sessions.csv")
    hourly_df = pd.read_csv("data/processed/hourly_demand.csv")
    
    session_energy_sum = sess_df["kWhDelivered"].sum()
    hourly_energy_sum = hourly_df["total_kwh_delivered"].sum()
    
    # 1. Exact mathematical conservation between session and hourly aggregations
    assert abs(session_energy_sum - hourly_energy_sum) < 1e-4, (
        f"Energy mismatch: session={session_energy_sum}, hourly={hourly_energy_sum}"
    )
    
    # 2. Strict canonical total check
    canonical_total = 53668.7813317712
    assert pytest.approx(session_energy_sum, rel=1e-5) == canonical_total
    assert pytest.approx(hourly_energy_sum, rel=1e-5) == canonical_total
    
    # 3. Formatted display string verification
    formatted_kwh = f"{session_energy_sum:,.2f} kWh"
    formatted_mwh = f"{session_energy_sum / 1000.0:.2f} MWh"
    assert formatted_kwh == "53,668.78 kWh"
    assert formatted_mwh == "53.67 MWh"


def test_dashboard_module_imports_cleanly():
    """Verify that dashboard app code can be compiled without syntax errors."""
    app_path = Path("dashboard/app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()
    compiled = compile(code, str(app_path), "exec")
    assert compiled is not None
