"""Forecasting Pipeline Module.

Implements chronological dataset splitting, feature alignment, model training,
validation selection, testing, and residual evaluation:
1. Seasonal Naive 24-hour baseline
2. Seasonal Naive 168-hour baseline
3. Ridge Regression
4. Random Forest Regressor
5. XGBoost Regressor

Adheres strictly to temporal ordering to prevent data leakage.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from src.evaluation import calculate_regression_metrics

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "hour",
    "dayofweek",
    "is_weekend",
    "month",
    "sin_hour",
    "cos_hour",
    "sin_dow",
    "cos_dow",
    "sin_month",
    "cos_month",
    "is_covid_lockdown",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_24",
    "lag_48",
    "lag_168",
    "rolling_mean_24",
    "rolling_std_24",
    "rolling_mean_168",
    "lag_count_1",
    "lag_count_24",
]

TARGET_COLUMN = "total_kwh_delivered"


class SeasonalNaiveBaseline:
    """Predicts target using seasonal lag (default: lag_24 or lag_168)."""
    
    def __init__(self, seasonal_period: int = 24):
        self.seasonal_period = seasonal_period
        self.feature_name = f"lag_{seasonal_period}"
        
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "SeasonalNaiveBaseline":
        return self
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.feature_name in X.columns:
            preds = X[self.feature_name].fillna(0.0).values
            return np.clip(preds, a_min=0.0, a_max=None)
        return np.zeros(len(X))


def split_chronological_data_by_dates(
    hourly_df: pd.DataFrame,
    train_end_date: str = "2021-05-01 00:00:00",
    val_end_date: str = "2021-07-01 00:00:00",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split time series strictly by date ranges without shuffling or leakage.
    
    Training: January 2020 – April 2021 (drops initial 168h due to lag_168)
    Validation: May 2021 – June 2021
    Testing: July 2021 – September 2021
    
    Args:
        hourly_df: Continuous hourly feature DataFrame.
        train_end_date: Cutoff between training and validation.
        val_end_date: Cutoff between validation and test.
        
    Returns:
        Tuple of (train_df, val_df, test_df).
    """
    df = hourly_df.copy()
    ts = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    df["ts_local"] = ts
    df = df.sort_values("ts_local").reset_index(drop=True)
    
    train_cutoff = pd.Timestamp(train_end_date, tz="America/Los_Angeles")
    val_cutoff = pd.Timestamp(val_end_date, tz="America/Los_Angeles")
    
    # Raw partitions
    train_raw = df[df["ts_local"] < train_cutoff].copy()
    val_raw = df[(df["ts_local"] >= train_cutoff) & (df["ts_local"] < val_cutoff)].copy()
    test_raw = df[df["ts_local"] >= val_cutoff].copy()
    
    # Drop rows in training where lag_168 is NaN (first 168 hours of dataset)
    train_clean = train_raw.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy().reset_index(drop=True)
    val_clean = val_raw.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy().reset_index(drop=True)
    test_clean = test_raw.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy().reset_index(drop=True)
    
    logger.info(
        f"Chronological Date Split: Train={len(train_clean)}, Val={len(val_clean)}, Test={len(test_clean)}"
    )
    return train_clean, val_clean, test_clean


def split_chronological_data(
    df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split time series strictly in chronological order by fractions without shuffling.
    
    Args:
        df: Hourly feature DataFrame.
        train_frac: Fraction for training.
        val_frac: Fraction for validation.
        
    Returns:
        Tuple of (train_df, val_df, test_df).
    """
    clean_df = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy()
    clean_df = clean_df.sort_values("timestamp").reset_index(drop=True)
    
    n = len(clean_df)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))
    
    train_df = clean_df.iloc[:train_end].copy()
    val_df = clean_df.iloc[train_end:val_end].copy()
    test_df = clean_df.iloc[val_end:].copy()
    
    return train_df, val_df, test_df


def get_feature_matrices(
    train_df: pd.DataFrame, 
    val_df: pd.DataFrame, 
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Extract X and y matrices for train, val, and test splits."""
    X_train = train_df[FEATURE_COLUMNS].copy()
    y_train = train_df[TARGET_COLUMN].copy()
    
    X_val = val_df[FEATURE_COLUMNS].copy()
    y_val = val_df[TARGET_COLUMN].copy()
    
    X_test = test_df[FEATURE_COLUMNS].copy()
    y_test = test_df[TARGET_COLUMN].copy()
    
    return X_train, y_train, X_val, y_val, X_test, y_test


def build_candidate_forecasting_models(random_state: int = 42) -> Dict[str, Any]:
    """Instantiate reference baselines and candidate machine-learning models.
    
    Returns:
        Dictionary of initialized model instances with documented hyperparameters.
    """
    models = {
        "Seasonal_Naive_24h": SeasonalNaiveBaseline(seasonal_period=24),
        "Seasonal_Naive_168h": SeasonalNaiveBaseline(seasonal_period=168),
        "Ridge_Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=10.0, random_state=random_state))
        ]),
        "Random_Forest": RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1
        ),
        "XGBoost": XGBRegressor(
            n_estimators=120,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            n_jobs=-1
        )
    }
    return models


def train_and_evaluate_forecasting_models(
    hourly_df: pd.DataFrame,
    models_dir: Union[str, Path] = "models",
    results_dir: Union[str, Path] = "outputs/results",
    tables_dir: Union[str, Path] = "outputs/tables",
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """End-to-end forecasting pipeline: train on train set, tune/select on val set,
    and evaluate best model and benchmarks on untouched test set.
    
    Returns:
        Tuple of (comparison_table, model_artifacts, val_predictions_df, test_predictions_df).
    """
    models_path = Path(models_dir)
    results_path = Path(results_dir)
    tables_path = Path(tables_dir)
    
    models_path.mkdir(parents=True, exist_ok=True)
    results_path.mkdir(parents=True, exist_ok=True)
    tables_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Chronological splitting
    train_df, val_df, test_df = split_chronological_data_by_dates(hourly_df)
    X_train, y_train, X_val, y_val, X_test, y_test = get_feature_matrices(train_df, val_df, test_df)
    
    # 2. Instantiate models
    candidate_models = build_candidate_forecasting_models(random_state=random_state)
    
    val_preds = {"timestamp": val_df["timestamp"].values, "actual": y_val.values}
    test_preds = {"timestamp": test_df["timestamp"].values, "actual": y_test.values}
    
    trained_artifacts = {}
    comparison_rows = []
    
    # 3. Train models ONLY on training set
    for name, model in candidate_models.items():
        logger.info(f"Training forecasting model: {name}...")
        model.fit(X_train, y_train)
        trained_artifacts[name] = model
        
        # Save serialized model
        joblib.dump(model, models_path / f"model_{name.lower()}.joblib")
        
        # Predict on validation set
        y_val_pred_raw = model.predict(X_val)
        y_val_pred = np.clip(y_val_pred_raw, a_min=0.0, a_max=None)
        val_preds[name] = y_val_pred
        val_metrics = calculate_regression_metrics(y_val, y_val_pred)
        
        # Predict on test set
        y_test_pred_raw = model.predict(X_test)
        y_test_pred = np.clip(y_test_pred_raw, a_min=0.0, a_max=None)
        test_preds[name] = y_test_pred
        test_metrics = calculate_regression_metrics(y_test, y_test_pred)
        
        comparison_rows.append({
            "Model": name,
            "Val_MAE": float(round(val_metrics["MAE"], 3)),
            "Val_RMSE": float(round(val_metrics["RMSE"], 3)),
            "Val_MSE": float(round(val_metrics["MSE"], 3)),
            "Val_R2": float(round(val_metrics["R2"], 4)),
            "Val_sMAPE": float(round(val_metrics["sMAPE"], 2)),
            "Test_MAE": float(round(test_metrics["MAE"], 3)),
            "Test_RMSE": float(round(test_metrics["RMSE"], 3)),
            "Test_MSE": float(round(test_metrics["MSE"], 3)),
            "Test_R2": float(round(test_metrics["R2"], 4)),
            "Test_sMAPE": float(round(test_metrics["sMAPE"], 2)),
        })
        
    comp_df = pd.DataFrame(comparison_rows)
    # Sort strictly by Validation RMSE to reflect validation-driven selection
    comp_df = comp_df.sort_values("Val_RMSE", ascending=True).reset_index(drop=True)
    
    # Save comparison table
    comp_table_path = tables_path / "table6_forecasting_model_comparison.csv"
    comp_df.to_csv(comp_table_path, index=False)
    logger.info(f"Saved model comparison table to {comp_table_path}")
    
    # Save predictions
    val_pred_df = pd.DataFrame(val_preds)
    test_pred_df = pd.DataFrame(test_preds)
    val_pred_df.to_csv(results_path / "forecast_predictions_val.csv", index=False)
    test_pred_df.to_csv(results_path / "forecast_predictions_test.csv", index=False)
    logger.info("Saved validation and test predictions to outputs/results/")
    
    # Document hyperparameters and features used
    hyper_df = pd.DataFrame([
        {"Model": "Seasonal_Naive_24h", "Type": "Baseline", "Hyperparameters": "seasonal_period=24 (persistence: y(t)=y(t-24))", "Features_Used": "lag_24"},
        {"Model": "Seasonal_Naive_168h", "Type": "Baseline", "Hyperparameters": "seasonal_period=168 (persistence: y(t)=y(t-168))", "Features_Used": "lag_168"},
        {"Model": "Ridge_Regression", "Type": "Linear", "Hyperparameters": "alpha=10.0, StandardScaler, random_state=42", "Features_Used": f"All {len(FEATURE_COLUMNS)} features"},
        {"Model": "Random_Forest", "Type": "Ensemble", "Hyperparameters": "n_estimators=100, max_depth=12, min_samples_split=4, min_samples_leaf=2, random_state=42", "Features_Used": f"All {len(FEATURE_COLUMNS)} features"},
        {"Model": "XGBoost", "Type": "Gradient Boosted Trees", "Hyperparameters": "n_estimators=120, max_depth=5, learning_rate=0.08, subsample=0.8, colsample_bytree=0.8, random_state=42", "Features_Used": f"All {len(FEATURE_COLUMNS)} features"},
    ])
    hyper_df.to_csv(tables_path / "table7_hyperparameters_and_features.csv", index=False)
    
    return comp_df, trained_artifacts, val_pred_df, test_pred_df


def generate_forecasting_figures(
    test_pred_df: pd.DataFrame,
    comp_df: pd.DataFrame,
    figures_dir: Union[str, Path] = "outputs/figures",
    best_model_name: Optional[str] = None,
) -> Dict[str, Path]:
    """Generate publication-grade diagnostic and comparative forecasting figures.
    
    Args:
        test_pred_df: DataFrame containing timestamps, actuals, and model predictions on test set.
        comp_df: Model comparison performance table.
        figures_dir: Destination path for figures.
        best_model_name: Name of selected best model (by default top row of comp_df).
        
    Returns:
        Dictionary mapping figure keys to saved file paths.
    """
    out_dir = Path(figures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if best_model_name is None:
        best_model_name = str(comp_df.iloc[0]["Model"])
        
    ts = pd.to_datetime(test_pred_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    actual = test_pred_df["actual"].values
    best_pred = test_pred_df[best_model_name].values
    residuals = actual - best_pred
    
    paths = {}
    
    # Fig M: Actual vs Predicted Demand on the Test Period (2-week zoom + full test)
    out_m = out_dir / "fig_m_test_actual_vs_predicted.png"
    fig, axes = plt.subplots(2, 1, figsize=(15, 8), sharex=False)
    
    # Top: Full test set timeline
    axes[0].plot(ts, actual, label="Actual Hourly Demand", color="black", linewidth=1.0, alpha=0.8)
    axes[0].plot(ts, best_pred, label=f"Forecast ({best_model_name})", color="#e41a1c", linewidth=1.2, alpha=0.85)
    axes[0].set_title(f"Full Test Period Hourly Forecast vs Actual (July – September 2021, n={len(ts)} hours)")
    axes[0].set_ylabel("Demand (kWh)")
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes[0].legend(loc="upper right")
    
    # Bottom: 14-day detailed operational window
    zoom_n = min(336, len(ts))  # 14 days = 336 hours
    axes[1].plot(ts[:zoom_n], actual[:zoom_n], label="Actual Demand", color="black", marker="o", markersize=3, linewidth=1.2)
    axes[1].plot(ts[:zoom_n], best_pred[:zoom_n], label=f"Forecast ({best_model_name})", color="#e41a1c", linestyle="--", linewidth=1.8)
    if "Seasonal_Naive_24h" in test_pred_df.columns:
        axes[1].plot(ts[:zoom_n], test_pred_df["Seasonal_Naive_24h"][:zoom_n], label="Naive 24h Baseline", color="#377eb8", linestyle=":", linewidth=1.2, alpha=0.7)
    axes[1].set_title("Detailed 14-Day Operational Horizon Zoom (First 336 Test Hours)")
    axes[1].set_xlabel("Local Time (America/Los_Angeles)")
    axes[1].set_ylabel("Demand (kWh)")
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%a %m/%d"))
    axes[1].legend(loc="upper right")
    
    plt.tight_layout()
    plt.savefig(out_m, dpi=300)
    plt.close()
    paths["fig_m"] = out_m
    
    # Fig N: Model Comparison Bar Chart (Validation and Test RMSE & MAE)
    out_n = out_dir / "fig_n_model_comparison.png"
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    x = np.arange(len(comp_df))
    width = 0.35
    models_display = [m.replace("_", " ") for m in comp_df["Model"]]
    
    # RMSE Comparison
    axes[0].bar(x - width/2, comp_df["Val_RMSE"], width, label="Validation RMSE", color="#4575b4", edgecolor="black")
    axes[0].bar(x + width/2, comp_df["Test_RMSE"], width, label="Test RMSE", color="#d73027", edgecolor="black")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(models_display, rotation=25, ha="right")
    axes[0].set_title("Root Mean Squared Error (RMSE) Comparison")
    axes[0].set_ylabel("RMSE (kWh)")
    axes[0].legend()
    axes[0].grid(axis="y", linestyle="--", alpha=0.7)
    
    # MAE Comparison
    axes[1].bar(x - width/2, comp_df["Val_MAE"], width, label="Validation MAE", color="#74add1", edgecolor="black")
    axes[1].bar(x + width/2, comp_df["Test_MAE"], width, label="Test MAE", color="#f46d43", edgecolor="black")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(models_display, rotation=25, ha="right")
    axes[1].set_title("Mean Absolute Error (MAE) Comparison")
    axes[1].set_ylabel("MAE (kWh)")
    axes[1].legend()
    axes[1].grid(axis="y", linestyle="--", alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(out_n, dpi=300)
    plt.close()
    paths["fig_n"] = out_n
    
    # Fig O: Forecast Residual Distribution
    out_o = out_dir / "fig_o_forecast_residuals.png"
    plt.figure(figsize=(9, 5))
    sns.histplot(residuals, bins=45, kde=True, color="#2b5c8f", edgecolor="black", alpha=0.75)
    plt.axvline(0, color="black", linestyle="-", linewidth=1.2)
    plt.axvline(np.mean(residuals), color="crimson", linestyle="--", label=f"Mean Error: {np.mean(residuals):.2f} kWh")
    plt.axvline(np.median(residuals), color="darkorange", linestyle=":", label=f"Median Error: {np.median(residuals):.2f} kWh")
    plt.title(f"Forecast Residual Distribution ($y - \\hat{{y}}$) on Test Set ({best_model_name})")
    plt.xlabel("Residual Error (Actual - Forecast, kWh)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_o, dpi=300)
    plt.close()
    paths["fig_o"] = out_o
    
    # Fig P: Actual vs Predicted Scatter Plot
    out_p = out_dir / "fig_p_actual_vs_predicted_scatter.png"
    plt.figure(figsize=(8, 7))
    plt.scatter(best_pred, actual, alpha=0.45, color="#1f78b4", edgecolors="none", s=25)
    max_scatter = max(np.max(actual), np.max(best_pred)) + 5
    plt.plot([0, max_scatter], [0, max_scatter], color="crimson", linestyle="--", linewidth=1.5, label="1:1 Parity Line")
    plt.title(f"Actual vs Forecasted Energy Demand on Test Set ({best_model_name})")
    plt.xlabel(f"Forecasted Energy Demand (kWh, {best_model_name})")
    plt.ylabel("Actual Observed Energy Demand (kWh)")
    plt.xlim(0, max_scatter)
    plt.ylim(0, max_scatter)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_p, dpi=300)
    plt.close()
    paths["fig_p"] = out_p
    
    # Fig Q: Forecast Performance Across Hours of Day (0 to 23)
    out_q = out_dir / "fig_q_hourly_forecast_performance.png"
    plt.figure(figsize=(10, 5))
    test_eval = pd.DataFrame({
        "hour": ts.dt.hour,
        "actual": actual,
        "predicted": best_pred,
        "abs_error": np.abs(residuals)
    })
    hourly_mae = test_eval.groupby("hour")["abs_error"].mean()
    hourly_mean_actual = test_eval.groupby("hour")["actual"].mean()
    
    plt.plot(hourly_mae.index, hourly_mae.values, marker="o", color="#d73027", linewidth=2.0, label=f"Forecast MAE ({best_model_name})")
    plt.plot(hourly_mean_actual.index, hourly_mean_actual.values, marker="s", color="#3182bd", linewidth=1.5, linestyle="--", label="Mean Observed Demand (kWh)")
    plt.title("Forecast Error (MAE) and Observed Demand Profile by Hour of Day")
    plt.xlabel("Hour of Day (Local Time America/Los_Angeles)")
    plt.ylabel("Energy (kWh)")
    plt.xticks(range(0, 24))
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_q, dpi=300)
    plt.close()
    paths["fig_q"] = out_q
    
    # Fig R: Forecast Performance During Weekday vs Weekend
    out_r = out_dir / "fig_r_weekday_weekend_performance.png"
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    test_eval["is_weekend"] = ts.dt.dayofweek.isin([5, 6]).astype(int)
    day_types = ["Weekday (Mon–Fri)", "Weekend (Sat–Sun)"]
    
    dow_metrics = []
    for flag in [0, 1]:
        mask = test_eval["is_weekend"] == flag
        m = calculate_regression_metrics(test_eval.loc[mask, "actual"], test_eval.loc[mask, "predicted"])
        dow_metrics.append(m)
        
    mae_vals = [m["MAE"] for m in dow_metrics]
    rmse_vals = [m["RMSE"] for m in dow_metrics]
    r2_vals = [m["R2"] for m in dow_metrics]
    
    axes[0].bar(day_types, mae_vals, color=["#2171b5", "#cb181d"], edgecolor="black", alpha=0.8)
    axes[0].set_title(f"Forecast MAE: Weekday vs Weekend ({best_model_name})")
    axes[0].set_ylabel("MAE (kWh)")
    axes[0].grid(axis="y", linestyle="--", alpha=0.7)
    
    axes[1].bar(day_types, r2_vals, color=["#2171b5", "#cb181d"], edgecolor="black", alpha=0.8)
    axes[1].set_title(f"Forecast $R^2$: Weekday vs Weekend ({best_model_name})")
    axes[1].set_ylabel("$R^2$ Variance Explained")
    axes[1].grid(axis="y", linestyle="--", alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(out_r, dpi=300)
    plt.close()
    paths["fig_r"] = out_r
    
    # Fig S: Demand Regime Residual Analysis
    out_s = out_dir / "fig_s_demand_regime_residuals.png"
    plt.figure(figsize=(9, 5))
    
    p95_test = np.percentile(actual[actual > 0], 95) if (actual > 0).any() else 50.0
    regime = np.where(
        actual == 0, "Zero Demand (0 kWh)",
        np.where(actual >= p95_test, "Peak Demand (>= P95)", "Moderate Demand (0 - P95)")
    )
    test_eval["regime"] = regime
    order = ["Zero Demand (0 kWh)", "Moderate Demand (0 - P95)", "Peak Demand (>= P95)"]
    
    sns.boxplot(x="regime", y="abs_error", data=test_eval, order=order, palette="Set2", showmeans=True)
    plt.title(f"Absolute Forecast Error Distribution across Operational Demand Regimes")
    plt.xlabel("Demand Regime")
    plt.ylabel("Absolute Forecast Error |y - ŷ| (kWh)")
    plt.tight_layout()
    plt.savefig(out_s, dpi=300)
    plt.close()
    paths["fig_s"] = out_s
    
    return paths


def perform_residual_analysis(
    test_pred_df: pd.DataFrame,
    best_model_name: str,
    tables_dir: Union[str, Path] = "outputs/tables",
) -> pd.DataFrame:
    """Analyze forecast errors across temporal, operational, and demand regimes.
    
    Identifies error concentrations: peak periods, low/zero periods, weekdays/weekends,
    and diurnal arrival hours.
    
    Args:
        test_pred_df: DataFrame of test predictions.
        best_model_name: Name of selected model.
        tables_dir: Target path for residual analysis table.
        
    Returns:
        DataFrame containing stratified residual metrics.
    """
    out_dir = Path(tables_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    ts = pd.to_datetime(test_pred_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    actual = test_pred_df["actual"].values
    pred = test_pred_df[best_model_name].values
    residuals = actual - pred
    abs_errors = np.abs(residuals)
    
    df_eval = pd.DataFrame({
        "timestamp": ts,
        "hour": ts.dt.hour,
        "is_weekend": ts.dt.dayofweek.isin([5, 6]).astype(int),
        "actual": actual,
        "pred": pred,
        "residual": residuals,
        "abs_error": abs_errors,
    })
    
    active_actual = actual[actual > 0]
    p95_thresh = float(np.percentile(active_actual, 95)) if len(active_actual) > 0 else 50.0
    
    strata = []
    
    # 1. Overall Test
    overall_m = calculate_regression_metrics(actual, pred)
    strata.append({
        "Stratum_Category": "Overall Test Set",
        "Subgroup": "All Test Hours",
        "Hours_Count": len(df_eval),
        "Mean_Actual_kWh": float(round(np.mean(actual), 2)),
        "Mean_Forecast_kWh": float(round(np.mean(pred), 2)),
        "Mean_Bias_kWh": float(round(np.mean(residuals), 2)),
        "MAE": float(round(overall_m["MAE"], 2)),
        "RMSE": float(round(overall_m["RMSE"], 2)),
        "R2": float(round(overall_m["R2"], 4)),
    })
    
    # 2. Zero-Demand vs Active Demand
    zero_mask = df_eval["actual"] == 0
    m_zero = calculate_regression_metrics(df_eval.loc[zero_mask, "actual"], df_eval.loc[zero_mask, "pred"])
    m_active = calculate_regression_metrics(df_eval.loc[~zero_mask, "actual"], df_eval.loc[~zero_mask, "pred"])
    
    strata.append({
        "Stratum_Category": "Demand Level",
        "Subgroup": "Zero-Demand Hours (y = 0)",
        "Hours_Count": int(zero_mask.sum()),
        "Mean_Actual_kWh": 0.0,
        "Mean_Forecast_kWh": float(round(df_eval.loc[zero_mask, "pred"].mean(), 2)),
        "Mean_Bias_kWh": float(round(df_eval.loc[zero_mask, "residual"].mean(), 2)),
        "MAE": float(round(m_zero["MAE"], 2)),
        "RMSE": float(round(m_zero["RMSE"], 2)),
        "R2": float(round(m_zero["R2"], 4)),
    })
    strata.append({
        "Stratum_Category": "Demand Level",
        "Subgroup": "Active-Demand Hours (y > 0)",
        "Hours_Count": int((~zero_mask).sum()),
        "Mean_Actual_kWh": float(round(df_eval.loc[~zero_mask, "actual"].mean(), 2)),
        "Mean_Forecast_kWh": float(round(df_eval.loc[~zero_mask, "pred"].mean(), 2)),
        "Mean_Bias_kWh": float(round(df_eval.loc[~zero_mask, "residual"].mean(), 2)),
        "MAE": float(round(m_active["MAE"], 2)),
        "RMSE": float(round(m_active["RMSE"], 2)),
        "R2": float(round(m_active["R2"], 4)),
    })
    
    # 3. Peak Demand vs Moderate Demand
    peak_mask = df_eval["actual"] >= p95_thresh
    m_peak = calculate_regression_metrics(df_eval.loc[peak_mask, "actual"], df_eval.loc[peak_mask, "pred"])
    strata.append({
        "Stratum_Category": "Demand Level",
        "Subgroup": f"Peak Demand (>= {p95_thresh:.1f} kWh)",
        "Hours_Count": int(peak_mask.sum()),
        "Mean_Actual_kWh": float(round(df_eval.loc[peak_mask, "actual"].mean(), 2)),
        "Mean_Forecast_kWh": float(round(df_eval.loc[peak_mask, "pred"].mean(), 2)),
        "Mean_Bias_kWh": float(round(df_eval.loc[peak_mask, "residual"].mean(), 2)),
        "MAE": float(round(m_peak["MAE"], 2)),
        "RMSE": float(round(m_peak["RMSE"], 2)),
        "R2": float(round(m_peak["R2"], 4)),
    })
    
    # 4. Weekday vs Weekend
    for flag, label in [(0, "Weekdays (Mon–Fri)"), (1, "Weekends (Sat–Sun)")]:
        sub_mask = df_eval["is_weekend"] == flag
        m_sub = calculate_regression_metrics(df_eval.loc[sub_mask, "actual"], df_eval.loc[sub_mask, "pred"])
        strata.append({
            "Stratum_Category": "Day Type",
            "Subgroup": label,
            "Hours_Count": int(sub_mask.sum()),
            "Mean_Actual_kWh": float(round(df_eval.loc[sub_mask, "actual"].mean(), 2)),
            "Mean_Forecast_kWh": float(round(df_eval.loc[sub_mask, "pred"].mean(), 2)),
            "Mean_Bias_kWh": float(round(df_eval.loc[sub_mask, "residual"].mean(), 2)),
            "MAE": float(round(m_sub["MAE"], 2)),
            "RMSE": float(round(m_sub["RMSE"], 2)),
            "R2": float(round(m_sub["R2"], 4)),
        })
        
    # 5. Morning Peak Window (08:00 - 12:00)
    am_peak_mask = (df_eval["is_weekend"] == 0) & (df_eval["hour"].isin([8, 9, 10, 11]))
    m_am = calculate_regression_metrics(df_eval.loc[am_peak_mask, "actual"], df_eval.loc[am_peak_mask, "pred"])
    strata.append({
        "Stratum_Category": "Time Window",
        "Subgroup": "Weekday Morning Commute Peak (08:00–12:00)",
        "Hours_Count": int(am_peak_mask.sum()),
        "Mean_Actual_kWh": float(round(df_eval.loc[am_peak_mask, "actual"].mean(), 2)),
        "Mean_Forecast_kWh": float(round(df_eval.loc[am_peak_mask, "pred"].mean(), 2)),
        "Mean_Bias_kWh": float(round(df_eval.loc[am_peak_mask, "residual"].mean(), 2)),
        "MAE": float(round(m_am["MAE"], 2)),
        "RMSE": float(round(m_am["RMSE"], 2)),
        "R2": float(round(m_am["R2"], 4)),
    })
    
    res_df = pd.DataFrame(strata)
    out_table = out_dir / "table8_residual_analysis.csv"
    res_df.to_csv(out_table, index=False)
    logger.info(f"Saved residual analysis table to {out_table}")
    
    return res_df
