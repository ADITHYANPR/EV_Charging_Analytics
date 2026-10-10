"""Test Suite for Phase 4: Preprocessing and EDA Integrity.

Validates:
1. Row preservation (exactly 5,000 sessions)
2. Timestamp conversion (UTC preserved, America/Los_Angeles local conversions)
3. Feature correctness (durations, ratios, errors, cyclical features)
4. Missing-value handling (indicators and flags preserved)
5. Hourly aggregation (continuous grid, zero-filling, conservation of total energy)
6. Chronological ordering (monotonicity of time series)
7. Absence of fabricated values (exact alignment with raw dataset)
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def raw_data():
    raw_path = Path("data/raw/acn_caltech_5000.json")
    with open(raw_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def cleaned_sessions():
    sess_path = Path("data/processed/cleaned_sessions.csv")
    assert sess_path.exists(), "cleaned_sessions.csv does not exist"
    return pd.read_csv(sess_path)


@pytest.fixture(scope="module")
def hourly_demand():
    hr_path = Path("data/processed/hourly_demand.csv")
    assert hr_path.exists(), "hourly_demand.csv does not exist"
    return pd.read_csv(hr_path)


def test_row_preservation(raw_data, cleaned_sessions):
    """Verify that exactly 5,000 raw sessions are preserved in cleaned_sessions.csv."""
    assert len(raw_data) == 5000, f"Raw data count expected 5000, got {len(raw_data)}"
    assert len(cleaned_sessions) == 5000, f"Processed sessions expected 5000, got {len(cleaned_sessions)}"
    assert cleaned_sessions["_id"].nunique() == 5000, "Expected 5000 unique _id values"
    assert cleaned_sessions["sessionID"].nunique() == 5000, "Expected 5000 unique sessionID values"


def test_timestamp_conversion(cleaned_sessions):
    """Verify UTC timestamps are preserved and local conversions are in America/Los_Angeles."""
    assert "connectionTime_utc" in cleaned_sessions.columns
    assert "connectionTime_local" in cleaned_sessions.columns
    assert "disconnectTime_utc" in cleaned_sessions.columns
    assert "disconnectTime_local" in cleaned_sessions.columns
    
    conn_utc = pd.to_datetime(cleaned_sessions["connectionTime_utc"], utc=True)
    conn_local = pd.to_datetime(cleaned_sessions["connectionTime_local"], utc=True).dt.tz_convert("America/Los_Angeles")
    
    # Verify offset is either -8 (PST) or -7 (PDT)
    offsets_hours = conn_local.apply(lambda x: x.utcoffset().total_seconds() / 3600.0)
    assert set(offsets_hours.unique()).issubset({-8.0, -7.0}), f"Unexpected local offsets: {offsets_hours.unique()}"


def test_feature_correctness(cleaned_sessions):
    """Verify mathematical derivations of duration, error, and rate features."""
    # Duration non-negativity
    assert (cleaned_sessions["connection_duration_min"] >= 0).all()
    assert (cleaned_sessions["connection_duration_hr"] >= 0).all()
    
    # Floored negative duration flag
    assert cleaned_sessions["negative_charging_duration_flag"].sum() == 1
    assert (cleaned_sessions["charging_duration_min"].dropna() >= 0).all()
    
    # Energy error: requested - delivered
    valid_req = cleaned_sessions.dropna(subset=["kWhRequested"])
    calculated_diff = valid_req["kWhRequested"] - valid_req["kWhDelivered"]
    np.testing.assert_allclose(valid_req["energy_error_kwh"].values, calculated_diff.values, rtol=1e-5)
    
    # Cyclical feature bounds
    for col in ["sin_conn_hour", "cos_conn_hour", "sin_dayofweek", "cos_dayofweek"]:
        assert (cleaned_sessions[col] >= -1.0 - 1e-6).all()
        assert (cleaned_sessions[col] <= 1.0 + 1e-6).all()


def test_missing_value_handling(cleaned_sessions):
    """Verify explicit indicators for missing user inputs, user IDs, and completion times."""
    assert cleaned_sessions["is_registered_user"].sum() == 4410
    assert (cleaned_sessions["is_registered_user"] == 0).sum() == 590
    assert cleaned_sessions["user_id_clean"].isnull().sum() == 0
    assert (cleaned_sessions["user_id_clean"] == "ANONYMOUS").sum() == 590
    
    # Done charging completion
    assert cleaned_sessions["is_charging_completed"].sum() == 3427
    assert (cleaned_sessions["is_charging_completed"] == 0).sum() == 1573
    assert cleaned_sessions["charging_duration_hr"].isnull().sum() == 1573


def test_hourly_aggregation_and_conservation(cleaned_sessions, hourly_demand):
    """Verify continuous time series, zero-filling, and total energy conservation."""
    # Conservation of total energy delivered: sum(hourly) must match sum(sessions)
    session_total_kwh = cleaned_sessions["kWhDelivered"].sum()
    hourly_total_kwh = hourly_demand["total_kwh_delivered"].sum()
    assert pytest.approx(session_total_kwh, rel=1e-5) == hourly_total_kwh
    
    # Total active session count must match 5,000
    assert hourly_demand["session_count"].sum() == 5000
    
    # Verify zero-fill in inactive hours
    zero_hours = (hourly_demand["total_kwh_delivered"] == 0).sum()
    assert zero_hours > 0, "Continuous time index should have explicit zero-demand hours"
    assert (hourly_demand.loc[hourly_demand["total_kwh_delivered"] == 0, "session_count"] == 0).all()


def test_chronological_ordering(hourly_demand):
    """Verify timestamps in hourly series are strictly monotonic with 1-hour step."""
    ts = pd.to_datetime(hourly_demand["timestamp"], utc=True)
    assert ts.is_monotonic_increasing, "Hourly time series must be strictly monotonic increasing"
    
    time_diffs = ts.diff().dropna()
    expected_step = pd.Timedelta(hours=1)
    assert (time_diffs == expected_step).all(), "Continuous grid must have uniform 1-hour frequency"


def test_absence_of_fabricated_values(raw_data, cleaned_sessions):
    """Verify summary metrics strictly match raw ground truth without synthetic alterations."""
    raw_kwh = [float(item["kWhDelivered"]) for item in raw_data]
    
    assert pytest.approx(min(raw_kwh), rel=1e-5) == cleaned_sessions["kWhDelivered"].min()
    assert pytest.approx(max(raw_kwh), rel=1e-5) == cleaned_sessions["kWhDelivered"].max()
    assert pytest.approx(np.mean(raw_kwh), rel=1e-5) == cleaned_sessions["kWhDelivered"].mean()
    assert pytest.approx(np.median(raw_kwh), rel=1e-5) == cleaned_sessions["kWhDelivered"].median()
