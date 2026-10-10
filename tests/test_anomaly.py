"""Test Suite for Phase 6: Unsupervised Anomaly Detection Pipeline.

Validates:
1. Feature matrix correctness (12 approved features)
2. No identifier leakage (sessionID, stationID, userID, _id strictly excluded from predictors)
3. Preprocessing consistency (RobustScaler handles skewness, zero NaNs post-imputation)
4. Anomaly-score generation (normalized scores bounded in [0, 1])
5. Threshold correctness (exact 3.0% contamination / 150 sessions per algorithm)
6. Score alignment with session IDs (1-to-1 match with input session IDs)
7. Isolation Forest execution (successful fit and scoring)
8. LOF execution (successful fit and scoring)
9. Consensus calculation (consensus flag is logical AND of iForest and LOF flags)
10. No row loss (5,000 output records match 5,000 input sessions)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.anomaly_detection import (
    ANOMALY_FEATURE_COLS,
    prepare_anomaly_feature_matrix,
    run_isolation_forest,
    run_local_outlier_factor,
    execute_anomaly_detection_pipeline,
)


@pytest.fixture(scope="module")
def session_df():
    path = Path("data/processed/cleaned_sessions.csv")
    assert path.exists(), "cleaned_sessions.csv does not exist"
    return pd.read_csv(path)


@pytest.fixture(scope="module")
def anomaly_results(session_df):
    pred_path = Path("outputs/results/session_anomaly_predictions.csv")
    if pred_path.exists():
        return pd.read_csv(pred_path)
    results_df, _ = execute_anomaly_detection_pipeline(session_df)
    return results_df


def test_feature_matrix_correctness(session_df):
    """Verify that feature matrix contains exactly the 12 approved features."""
    X_scaled, feat_df, scaler, medians = prepare_anomaly_feature_matrix(session_df)
    
    assert X_scaled.shape == (5000, 12), f"Expected shape (5000, 12), got {X_scaled.shape}"
    assert list(feat_df.columns) == ANOMALY_FEATURE_COLS
    assert not np.isnan(X_scaled).any(), "Scaled feature matrix contains NaNs"


def test_no_identifier_leakage(session_df):
    """Verify that identifiers are strictly absent from anomaly predictors."""
    disallowed_identifiers = ["sessionID", "stationID", "spaceID", "userID", "user_id_clean", "_id", "siteID", "clusterID"]
    
    for identifier in disallowed_identifiers:
        assert identifier not in ANOMALY_FEATURE_COLS, f"Identifier {identifier} found in ANOMALY_FEATURE_COLS"


def test_preprocessing_consistency(session_df):
    """Verify RobustScaler and median imputation produce finite, valid matrices."""
    X_scaled, feat_df, scaler, medians = prepare_anomaly_feature_matrix(session_df)
    
    assert np.isfinite(X_scaled).all(), "Feature matrix contains infinite values"
    assert len(medians) == 12
    # Check that medians match pandas medians
    for col in ANOMALY_FEATURE_COLS:
        assert pytest.approx(medians[col], rel=1e-4) == session_df[col].median()


def test_anomaly_score_generation(anomaly_results):
    """Verify normalized anomaly scores are bounded in [0, 1]."""
    for score_col in ["score_isolation_forest", "score_lof", "score_ensemble"]:
        scores = anomaly_results[score_col].values
        assert (scores >= 0.0).all(), f"{score_col} contains values < 0"
        assert (scores <= 1.0).all(), f"{score_col} contains values > 1"


def test_threshold_correctness(anomaly_results):
    """Verify contamination threshold yields exactly 150 sessions (3%) for each algorithm."""
    count_if = anomaly_results["flag_isolation_forest"].sum()
    count_lof = anomaly_results["flag_lof"].sum()
    
    assert count_if == 150, f"Expected 150 iForest anomalies (3% of 5,000), got {count_if}"
    assert count_lof == 150, f"Expected 150 LOF anomalies (3% of 5,000), got {count_lof}"


def test_score_alignment_with_session_ids(session_df, anomaly_results):
    """Verify sessionID alignment between input and output datasets."""
    assert (session_df["sessionID"] == anomaly_results["sessionID"]).all(), "sessionID order mismatch"


def test_isolation_forest_execution(session_df):
    """Verify Isolation Forest model execution and decision score inverted direction."""
    X_scaled, _, _, _ = prepare_anomaly_feature_matrix(session_df)
    flags, raw_scores, norm_scores, model = run_isolation_forest(X_scaled, contamination=0.03, random_state=42)
    
    assert len(flags) == 5000
    assert flags.sum() == 150
    # Outlier sessions should have higher normalized scores than inliers
    outlier_mean_score = norm_scores[flags == 1].mean()
    inlier_mean_score = norm_scores[flags == 0].mean()
    assert outlier_mean_score > inlier_mean_score


def test_lof_execution(session_df):
    """Verify LOF model execution and normalized score ranking."""
    X_scaled, _, _, _ = prepare_anomaly_feature_matrix(session_df)
    flags, raw_scores, norm_scores, model = run_local_outlier_factor(X_scaled, contamination=0.03, n_neighbors=25)
    
    assert len(flags) == 5000
    assert flags.sum() == 150
    assert norm_scores[flags == 1].mean() > norm_scores[flags == 0].mean()


def test_consensus_calculation(anomaly_results):
    """Verify that consensus flag strictly equals iForest flag AND LOF flag."""
    expected_consensus = (anomaly_results["flag_isolation_forest"] == 1) & (anomaly_results["flag_lof"] == 1)
    actual_consensus = anomaly_results["is_consensus_anomaly"] == 1
    
    assert (expected_consensus == actual_consensus).all(), "Consensus flag does not match bitwise AND"
    assert actual_consensus.sum() == 33, f"Expected 33 consensus anomalies, got {actual_consensus.sum()}"


def test_no_row_loss(session_df, anomaly_results):
    """Verify 100% row preservation across anomaly pipeline."""
    assert len(anomaly_results) == 5000, f"Expected 5,000 output rows, got {len(anomaly_results)}"
    assert len(anomaly_results) == len(session_df)
