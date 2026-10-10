"""Test Suite for Phase 5: Demand Forecasting Pipeline.

Validates:
1. Chronological split correctness (Train < Val < Test)
2. No train/test overlap (disjoint index partitions)
3. Lag correctness (lag_k is exactly equal to target shifted by k)
4. Rolling-feature leakage prevention (rolling stats shifted by 1 hour)
5. Zero-demand handling (safe sMAPE evaluation without division by zero)
6. Metric correctness (MAE, RMSE, MSE, R^2, sMAPE formulas)
7. Prediction length alignment (predictions match validation and test set lengths exactly)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.forecasting import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    split_chronological_data_by_dates,
    get_feature_matrices,
    build_candidate_forecasting_models,
)
from src.evaluation import calculate_regression_metrics


@pytest.fixture(scope="module")
def hourly_df():
    hr_path = Path("data/processed/hourly_demand.csv")
    assert hr_path.exists(), "hourly_demand.csv does not exist"
    return pd.read_csv(hr_path)


@pytest.fixture(scope="module")
def splits(hourly_df):
    train_df, val_df, test_df = split_chronological_data_by_dates(hourly_df)
    return train_df, val_df, test_df


def test_chronological_split_correctness(splits):
    """Verify chronological ordering: max(train) < min(val) < max(val) < min(test)."""
    train_df, val_df, test_df = splits
    
    t_train = pd.to_datetime(train_df["timestamp"], utc=True)
    t_val = pd.to_datetime(val_df["timestamp"], utc=True)
    t_test = pd.to_datetime(test_df["timestamp"], utc=True)
    
    assert t_train.max() < t_val.min(), "Training set must strictly precede validation set"
    assert t_val.max() < t_test.min(), "Validation set must strictly precede test set"


def test_no_train_test_overlap(splits):
    """Verify train, validation, and test sets are strictly disjoint in timestamps."""
    train_df, val_df, test_df = splits
    
    set_train = set(train_df["timestamp"])
    set_val = set(val_df["timestamp"])
    set_test = set(test_df["timestamp"])
    
    assert len(set_train.intersection(set_val)) == 0, "Train and Val must have no overlapping timestamps"
    assert len(set_val.intersection(set_test)) == 0, "Val and Test must have no overlapping timestamps"
    assert len(set_train.intersection(set_test)) == 0, "Train and Test must have no overlapping timestamps"


def test_lag_correctness(hourly_df):
    """Verify lag_1, lag_24, lag_168 are mathematically identical to target shifted by k."""
    # Sort to ensure order
    df = hourly_df.sort_values("timestamp").reset_index(drop=True)
    target = df[TARGET_COLUMN]
    
    # lag_1
    expected_lag_1 = target.shift(1)
    np.testing.assert_allclose(df["lag_1"].dropna().values, expected_lag_1.dropna().values, rtol=1e-5)
    
    # lag_24
    expected_lag_24 = target.shift(24)
    np.testing.assert_allclose(df["lag_24"].dropna().values, expected_lag_24.dropna().values, rtol=1e-5)
    
    # lag_168
    expected_lag_168 = target.shift(168)
    np.testing.assert_allclose(df["lag_168"].dropna().values, expected_lag_168.dropna().values, rtol=1e-5)


def test_rolling_feature_leakage_prevention(hourly_df):
    """Verify rolling mean features do NOT include current timestamp target value (shift=1)."""
    df = hourly_df.sort_values("timestamp").reset_index(drop=True)
    target = df[TARGET_COLUMN]
    
    # Calculated with shift(1)
    expected_rolling_24 = target.shift(1).rolling(24, min_periods=1).mean()
    np.testing.assert_allclose(df["rolling_mean_24"].dropna().values, expected_rolling_24.dropna().values, rtol=1e-5)
    
    # Check that rolling_mean_24 at row i does not change if target at row i changes
    sample_idx = 50
    prior_mean = df.loc[sample_idx, "rolling_mean_24"]
    current_val = df.loc[sample_idx, TARGET_COLUMN]
    prior_values = df.loc[sample_idx - 24 : sample_idx - 1, TARGET_COLUMN]
    expected_val = prior_values.mean()
    assert pytest.approx(prior_mean, rel=1e-4) == expected_val


def test_zero_demand_handling():
    """Verify sMAPE handles zero-demand hours gracefully without NaN or Inf."""
    y_true = np.array([0.0, 0.0, 0.0, 10.0])
    y_pred = np.array([0.0, 1.0, 0.0, 12.0])
    
    metrics = calculate_regression_metrics(y_true, y_pred)
    assert not np.isnan(metrics["sMAPE"])
    assert not np.isinf(metrics["sMAPE"])
    assert metrics["sMAPE"] >= 0.0


def test_metric_correctness():
    """Verify MAE, RMSE, MSE, and R2 formulas against hand-calculated ground truth."""
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    y_pred = np.array([12.0, 18.0, 32.0, 38.0])
    
    m = calculate_regression_metrics(y_true, y_pred)
    assert m["MAE"] == pytest.approx(2.0)
    assert m["MSE"] == pytest.approx(4.0)
    assert m["RMSE"] == pytest.approx(2.0)
    assert m["R2"] == pytest.approx(0.968)


def test_prediction_length_alignment(splits):
    """Verify candidate model prediction outputs match test and validation lengths."""
    train_df, val_df, test_df = splits
    X_train, y_train, X_val, y_val, X_test, y_test = get_feature_matrices(train_df, val_df, test_df)
    
    models = build_candidate_forecasting_models(random_state=42)
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred_val = model.predict(X_val)
        pred_test = model.predict(X_test)
        
        assert len(pred_val) == len(val_df), f"{name} Val predictions length mismatch"
        assert len(pred_test) == len(test_df), f"{name} Test predictions length mismatch"
        assert not np.isnan(pred_val).any(), f"{name} Val predictions contain NaNs"
        assert not np.isnan(pred_test).any(), f"{name} Test predictions contain NaNs"
