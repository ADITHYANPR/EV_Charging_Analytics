"""Evaluation Module.

Implements academic performance metrics for:
1. Time-series demand forecasting (MAE, RMSE, MSE, R^2, sMAPE)
2. Unsupervised anomaly detection (Jaccard consensus, distribution separation)
"""

import logging
from typing import Any, Dict, List, Union
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


def calculate_regression_metrics(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series]
) -> Dict[str, float]:
    """Calculate standard academic regression evaluation metrics.
    
    Args:
        y_true: Ground truth observed continuous values.
        y_pred: Forecasted values.
        
    Returns:
        Dictionary of computed metrics (MAE, RMSE, MSE, R2, sMAPE).
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    
    mae = float(mean_absolute_error(yt, yp))
    mse = float(mean_squared_error(yt, yp))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(yt, yp))
    
    # Symmetric MAPE to handle zero-load hours safely
    denominator = (np.abs(yt) + np.abs(yp)) / 2.0
    nonzero_mask = denominator > 1e-4
    if np.any(nonzero_mask):
        smape = float(np.mean(np.abs(yp[nonzero_mask] - yt[nonzero_mask]) / denominator[nonzero_mask]) * 100.0)
    else:
        smape = 0.0
        
    return {
        "MAE": mae,
        "RMSE": rmse,
        "MSE": mse,
        "R2": r2,
        "sMAPE": smape,
    }


def calculate_anomaly_consensus(
    labels_a: np.ndarray,
    labels_b: np.ndarray
) -> Dict[str, float]:
    """Calculate overlap and agreement metrics between two unsupervised anomaly detectors.
    
    Args:
        labels_a: Binary anomaly indicator array from Model A.
        labels_b: Binary anomaly indicator array from Model B.
        
    Returns:
        Dictionary with Jaccard index, mutual count, and individual counts.
    """
    set_a = set(np.where(labels_a == 1)[0])
    set_b = set(np.where(labels_b == 1)[0])
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    jaccard = float(intersection / union) if union > 0 else 0.0
    
    return {
        "model_a_anomalies": len(set_a),
        "model_b_anomalies": len(set_b),
        "consensus_anomalies": intersection,
        "union_anomalies": union,
        "jaccard_similarity": jaccard,
    }


def format_model_comparison_table(
    results_list: List[Dict[str, Any]]
) -> pd.DataFrame:
    """Format and sort comparative model evaluations into a standardized DataFrame."""
    df = pd.DataFrame(results_list)
    if "RMSE" in df.columns:
        df = df.sort_values("RMSE", ascending=True).reset_index(drop=True)
    return df
