"""Test Suite for Phase 3 Architecture and Module Functionality.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data_loader import load_raw_json, validate_raw_schema
from src.preprocessing import flatten_raw_sessions, standardize_timestamps, clean_and_impute_sessions
from src.feature_engineering import engineer_session_features, build_hourly_demand_series, engineer_forecasting_features
from src.forecasting import SeasonalNaiveBaseline, split_chronological_data
from src.anomaly_detection import prepare_anomaly_features
from src.evaluation import calculate_regression_metrics, calculate_anomaly_consensus


def test_raw_dataset_exists_and_loads():
    """Verify raw dataset is present in data/raw and parses properly."""
    raw_path = Path("data/raw/acn_caltech_5000.json")
    assert raw_path.exists(), "Raw dataset file missing in data/raw/"
    
    data = load_raw_json(raw_path)
    assert len(data) == 5000, f"Expected 5000 records, got {len(data)}"
    
    report = validate_raw_schema(data)
    assert report["is_valid"] is True, f"Schema validation failed: {report['missing_fields']}"


def test_preprocessing_and_timezone_conversion():
    """Verify flattening and timezone conversion to America/Los_Angeles on sample."""
    sample_records = [
        {
            "_id": "test_id_1",
            "sessionID": "test_session_1",
            "stationID": "2-39-81-4550",
            "spaceID": "11900388",
            "siteID": "0002",
            "clusterID": "0039",
            "userID": "000019055",
            "connectionTime": "Tue, 14 Sep 2021 01:52:37 GMT",
            "disconnectTime": "Tue, 14 Sep 2021 03:05:10 GMT",
            "kWhDelivered": 15.5,
            "doneChargingTime": "Tue, 14 Sep 2021 02:30:00 GMT",
            "timezone": "America/Los_Angeles",
            "userInputs": [
                {
                    "userID": 19055,
                    "milesRequested": 50,
                    "WhPerMile": 300,
                    "kWhRequested": 15.0,
                    "minutesAvailable": 120,
                    "paymentRequired": True
                }
            ]
        }
    ]
    
    df_flat = flatten_raw_sessions(sample_records)
    assert len(df_flat) == 1
    assert df_flat.loc[0, "has_user_inputs"] == 1
    assert df_flat.loc[0, "kWhRequested"] == 15.0
    
    df_timed = standardize_timestamps(df_flat, target_timezone="America/Los_Angeles")
    # Verify local timezone is America/Los_Angeles
    assert str(df_timed.loc[0, "connectionTime_local"].tz) == "America/Los_Angeles"
    assert df_timed.loc[0, "connection_duration_min"] > 0
    assert df_timed.loc[0, "is_charging_completed"] == 1


def test_chronological_splitting_no_leakage():
    """Verify chronological split respects time order and creates disjoint partitions."""
    # Synthesize mock hourly dataframe with enough periods for lag_168 (>= 168 steps)
    timestamps = pd.date_range("2021-01-01", periods=300, freq="h", tz="America/Los_Angeles")
    df_mock = pd.DataFrame({
        "timestamp": timestamps,
        "total_kwh_delivered": np.random.uniform(5, 50, size=300),
        "session_count": np.random.randint(1, 10, size=300),
    })
    
    # Engineer forecasting features
    df_feat = engineer_forecasting_features(df_mock)
    
    # Split
    train, val, test = split_chronological_data(df_feat, train_frac=0.6, val_frac=0.2)
    
    # Verify no overlaps and strict time ordering
    assert train["timestamp"].max() < val["timestamp"].min()
    assert val["timestamp"].max() < test["timestamp"].min()


def test_metric_calculation():
    """Verify regression and anomaly consensus evaluation metrics."""
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 19.0, 29.0])
    
    metrics = calculate_regression_metrics(y_true, y_pred)
    assert "MAE" in metrics
    assert "RMSE" in metrics
    assert "R2" in metrics
    assert metrics["MAE"] == pytest.approx(4.0 / 3.0)
    
    a = np.array([1, 0, 1, 0])
    b = np.array([1, 1, 0, 0])
    consensus = calculate_anomaly_consensus(a, b)
    assert consensus["consensus_anomalies"] == 1
    assert consensus["jaccard_similarity"] == pytest.approx(1.0 / 3.0)
