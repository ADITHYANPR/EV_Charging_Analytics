"""Anomaly Detection Pipeline Module.

Implements unsupervised session-level anomaly detection using:
1. Isolation Forest (Isolation tree path depth)
2. Local Outlier Factor (LOF; Local density deviation)

Constructs the approved 12-feature matrix with median imputation and RobustScaler,
generates normalized anomaly scores [0, 1], ranks, consensus flags, domain profiles,
feature-based explanations, and cross-validates against known data-quality flags.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler, MinMaxScaler

logger = logging.getLogger(__name__)

# The 12 approved analytical features (identifiers strictly excluded)
ANOMALY_FEATURE_COLS = [
    "kWhDelivered",
    "connection_duration_hr",
    "charging_duration_hr",
    "idle_duration_hr",
    "average_charging_rate_kw",
    "energy_error_kwh",
    "delivery_ratio",
    "idle_to_connection_ratio",
    "conn_hour",
    "minutesAvailable",
    "milesRequested",
    "WhPerMile",
]


def prepare_anomaly_feature_matrix(
    session_df: pd.DataFrame
) -> Tuple[np.ndarray, pd.DataFrame, RobustScaler, Dict[str, float]]:
    """Preprocess the 12 session-level variables using median imputation and RobustScaler.
    
    Preserves all 5,000 sessions without dropping rows.
    Identifiers (sessionID, stationID, userID, _id) are strictly excluded from predictors.
    
    Args:
        session_df: Cleaned sessions DataFrame (n=5,000).
        
    Returns:
        Tuple of (scaled_matrix, imputed_features_df, scaler_instance, medians_dict).
    """
    df = session_df.copy()
    
    # Extract only the 12 analytical features
    feat_df = df[ANOMALY_FEATURE_COLS].copy()
    
    # Calculate medians for imputation and profile comparison
    medians = {}
    for col in ANOMALY_FEATURE_COLS:
        col_median = float(feat_df[col].median(skipna=True))
        medians[col] = col_median
        # Impute missing values with median
        feat_df[col] = feat_df[col].fillna(col_median)
        
    # Scale using RobustScaler (median and IQR based) to withstand heavy skewness
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(feat_df)
    
    logger.info(f"Prepared anomaly feature matrix: shape={X_scaled.shape}, features={ANOMALY_FEATURE_COLS}")
    return X_scaled, feat_df, scaler, medians


# Backwards compatibility alias
prepare_anomaly_features = prepare_anomaly_feature_matrix


def run_isolation_forest(
    X_scaled: np.ndarray,
    contamination: float = 0.03,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, IsolationForest]:
    """Train Isolation Forest and generate flags, decision scores, and ranks.
    
    Args:
        X_scaled: Robustly scaled feature matrix.
        contamination: Contamination parameter (default: 0.03 = 3% of sessions).
        random_state: Fixed seed for reproducibility.
        
    Returns:
        Tuple of (binary_flags [1=outlier, 0=normal], raw_scores, normalized_scores, model).
    """
    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=150,
        n_jobs=-1
    )
    raw_preds = model.fit_predict(X_scaled)  # -1 for outlier, 1 for inlier
    flags = (raw_preds == -1).astype(int)
    
    # Invert decision function: higher value = more anomalous
    raw_scores = -model.decision_function(X_scaled)
    
    # Min-Max normalize score to [0, 1]
    norm_scores = MinMaxScaler().fit_transform(raw_scores.reshape(-1, 1)).flatten()
    
    return flags, raw_scores, norm_scores, model


def run_local_outlier_factor(
    X_scaled: np.ndarray,
    contamination: float = 0.03,
    n_neighbors: int = 25,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, LocalOutlierFactor]:
    """Train Local Outlier Factor (LOF) and generate flags, density scores, and ranks.
    
    Args:
        X_scaled: Robustly scaled feature matrix.
        contamination: Contamination fraction (default: 0.03).
        n_neighbors: Number of local nearest neighbors.
        
    Returns:
        Tuple of (binary_flags [1=outlier, 0=normal], raw_scores, normalized_scores, model).
    """
    model = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination,
        n_jobs=-1
    )
    raw_preds = model.fit_predict(X_scaled)  # -1 for outlier, 1 for inlier
    flags = (raw_preds == -1).astype(int)
    
    # Negative outlier factor: large negative values = more anomalous. Invert so higher = more anomalous.
    raw_scores = -model.negative_outlier_factor_
    
    # Min-Max normalize score to [0, 1]
    norm_scores = MinMaxScaler().fit_transform(raw_scores.reshape(-1, 1)).flatten()
    
    return flags, raw_scores, norm_scores, model


def generate_session_explanation(
    row: pd.Series,
    medians: pd.Series,
    iqrs: pd.Series
) -> str:
    """Generate domain-grounded feature explanation for unusual charging behavior.
    
    Uses neutral academic terminology without assuming fraud or hardware defect.
    """
    reasons = []
    
    # High energy
    if row["kWhDelivered"] > medians["kWhDelivered"] + 2.5 * iqrs["kWhDelivered"]:
        reasons.append(f"High energy consumption ({row['kWhDelivered']:.1f} kWh vs typical median {medians['kWhDelivered']:.1f} kWh)")
    elif row["kWhDelivered"] < 1.0:
        reasons.append(f"Near-zero energy consumption ({row['kWhDelivered']:.2f} kWh)")
        
    # Long parking connection
    if row["connection_duration_hr"] > medians["connection_duration_hr"] + 2.5 * iqrs["connection_duration_hr"]:
        reasons.append(f"Prolonged stall occupancy ({row['connection_duration_hr']:.1f} hr vs typical {medians['connection_duration_hr']:.1f} hr)")
        
    # High charging rate
    if row["average_charging_rate_kw"] > medians["average_charging_rate_kw"] + 2.5 * iqrs["average_charging_rate_kw"]:
        reasons.append(f"Elevated effective power draw ({row['average_charging_rate_kw']:.1f} kW)")
        
    # Prolonged idle duration
    if pd.notnull(row["idle_duration_hr"]) and row["idle_duration_hr"] > medians["idle_duration_hr"] + 2.5 * iqrs["idle_duration_hr"]:
        reasons.append(f"Extended idle post-charge connection ({row['idle_duration_hr']:.1f} hr)")
        
    # Discrepancy between requested and delivered
    if pd.notnull(row["energy_error_kwh"]) and abs(row["energy_error_kwh"]) > 40.0:
        if row["energy_error_kwh"] > 0:
            reasons.append(f"Unfulfilled energy request (shortfall of {row['energy_error_kwh']:.1f} kWh)")
        else:
            reasons.append(f"Substantial over-delivery ({abs(row['energy_error_kwh']):.1f} kWh beyond request)")
            
    # Off-peak arrival
    if int(row["conn_hour"]) in [1, 2, 3, 4]:
        reasons.append(f"Unusual late-night arrival ({int(row['conn_hour']):02d}:00)")
        
    if not reasons:
        reasons.append("Multi-dimensional multivariate feature outlier combination")
        
    return "; ".join(reasons)


def execute_anomaly_detection_pipeline(
    session_df: pd.DataFrame,
    contamination: float = 0.03,
    models_dir: Union[str, Path] = "models",
    results_dir: Union[str, Path] = "outputs/results",
    tables_dir: Union[str, Path] = "outputs/tables",
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute end-to-end unsupervised anomaly detection pipeline.
    
    Returns:
        Tuple of (results_df, summary_report).
    """
    models_path = Path(models_dir)
    results_path = Path(results_dir)
    tables_path = Path(tables_dir)
    
    models_path.mkdir(parents=True, exist_ok=True)
    results_path.mkdir(parents=True, exist_ok=True)
    tables_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Prepare feature matrix
    X_scaled, feat_df, scaler, medians = prepare_anomaly_feature_matrix(session_df)
    joblib.dump(scaler, models_path / "scaler_anomaly_robust.joblib")
    
    # 2. Run Isolation Forest
    flags_if, raw_if, norm_if, model_if = run_isolation_forest(
        X_scaled, contamination=contamination, random_state=random_state
    )
    joblib.dump(model_if, models_path / "model_isolation_forest.joblib")
    
    # 3. Run Local Outlier Factor
    flags_lof, raw_lof, norm_lof, model_lof = run_local_outlier_factor(
        X_scaled, contamination=contamination, n_neighbors=25
    )
    joblib.dump(model_lof, models_path / "model_local_outlier_factor.joblib")
    
    # 4. Compute Ranks (1 = highest anomaly score)
    ranks_if = pd.Series(norm_if).rank(ascending=False, method="min").astype(int).values
    ranks_lof = pd.Series(norm_lof).rank(ascending=False, method="min").astype(int).values
    
    # 5. Consensus Anomaly Flag (flagged by BOTH methods)
    consensus_flags = ((flags_if == 1) & (flags_lof == 1)).astype(int)
    
    # 6. Combined normalized ensemble score
    ensemble_score = (norm_if + norm_lof) / 2.0
    ensemble_rank = pd.Series(ensemble_score).rank(ascending=False, method="min").astype(int).values
    
    # Compute medians and IQRs for explanation generation
    feat_medians = feat_df.median()
    feat_iqrs = feat_df.quantile(0.75) - feat_df.quantile(0.25)
    
    # 7. Assemble Complete Results DataFrame
    results_df = session_df.copy()
    results_df["score_isolation_forest"] = np.round(norm_if, 4)
    results_df["flag_isolation_forest"] = flags_if
    results_df["rank_isolation_forest"] = ranks_if
    
    results_df["score_lof"] = np.round(norm_lof, 4)
    results_df["flag_lof"] = flags_lof
    results_df["rank_lof"] = ranks_lof
    
    results_df["is_consensus_anomaly"] = consensus_flags
    results_df["score_ensemble"] = np.round(ensemble_score, 4)
    results_df["rank_ensemble"] = ensemble_rank
    
    # Generate explanations
    explanations = []
    for idx, row in results_df.iterrows():
        if results_df.loc[idx, "is_consensus_anomaly"] == 1 or results_df.loc[idx, "flag_isolation_forest"] == 1:
            explanations.append(generate_session_explanation(row, feat_medians, feat_iqrs))
        else:
            explanations.append("Typical charging session profile")
    results_df["anomaly_explanation"] = explanations
    
    # Save complete session-level predictions
    pred_path = results_path / "session_anomaly_predictions.csv"
    results_df.to_csv(pred_path, index=False)
    logger.info(f"Saved complete session anomaly predictions to {pred_path}")
    
    # 8. Agreement & Consensus Metrics
    count_if = int(flags_if.sum())
    count_lof = int(flags_lof.sum())
    overlap_count = int(consensus_flags.sum())
    union_count = int(((flags_if == 1) | (flags_lof == 1)).sum())
    jaccard = float(round(overlap_count / union_count, 4)) if union_count > 0 else 0.0
    pct_agreement = float(round((flags_if == flags_lof).mean() * 100, 2))
    
    # 9. Generate Tables
    
    # Table 9: Anomaly Summary
    t9_df = pd.DataFrame([
        {"Method": "Isolation Forest", "Sessions_Flagged": count_if, "Flagged_Pct": float(round(count_if / len(session_df) * 100, 2)), "Contamination_Setting": contamination, "Score_Metric": "Path Isolation Depth"},
        {"Method": "Local Outlier Factor (LOF)", "Sessions_Flagged": count_lof, "Flagged_Pct": float(round(count_lof / len(session_df) * 100, 2)), "Contamination_Setting": contamination, "Score_Metric": "Local Reachability Density"},
        {"Method": "Consensus (Both Flagged)", "Sessions_Flagged": overlap_count, "Flagged_Pct": float(round(overlap_count / len(session_df) * 100, 2)), "Contamination_Setting": "Intersection", "Score_Metric": "Dual-Method Agreement"},
        {"Method": "Union (Either Flagged)", "Sessions_Flagged": union_count, "Flagged_Pct": float(round(union_count / len(session_df) * 100, 2)), "Contamination_Setting": "Union", "Score_Metric": "Ensemble Boundary"}
    ])
    t9_df.to_csv(tables_path / "table9_anomaly_summary.csv", index=False)
    
    # Table 10: Algorithm Comparison & Agreement
    t10_df = pd.DataFrame([
        {"Metric": "Isolation Forest Outliers Count", "Value": str(count_if)},
        {"Metric": "Local Outlier Factor Outliers Count", "Value": str(count_lof)},
        {"Metric": "Consensus Overlap Count", "Value": str(overlap_count)},
        {"Metric": "Union Outliers Count", "Value": str(union_count)},
        {"Metric": "Jaccard Similarity Index", "Value": f"{jaccard:.4f}"},
        {"Metric": "Overall Binary Agreement Pct", "Value": f"{pct_agreement:.2f}%"},
    ])
    t10_df.to_csv(tables_path / "table10_algorithm_comparison.csv", index=False)
    
    # Table 11: Top 15 Anomalous Sessions
    top15 = results_df.sort_values("score_ensemble", ascending=False).head(15)
    cols_top15 = [
        "sessionID", "rank_ensemble", "score_ensemble", "is_consensus_anomaly",
        "kWhDelivered", "connection_duration_hr", "average_charging_rate_kw",
        "idle_duration_hr", "conn_hour", "anomaly_explanation"
    ]
    top15[cols_top15].to_csv(tables_path / "table11_top_anomalous_sessions.csv", index=False)
    
    # Table 12: Anomaly Feature Profile (Consensus Anomalies vs Normal Sessions)
    norm_mask = results_df["is_consensus_anomaly"] == 0
    anom_mask = results_df["is_consensus_anomaly"] == 1
    
    t12_list = []
    for col in ANOMALY_FEATURE_COLS:
        s_norm = results_df.loc[norm_mask, col].dropna()
        s_anom = results_df.loc[anom_mask, col].dropna()
        t12_list.append({
            "Feature": col,
            "Normal_Median": float(round(s_norm.median(), 2)),
            "Normal_IQR": float(round(s_norm.quantile(0.75) - s_norm.quantile(0.25), 2)),
            "Anomaly_Median": float(round(s_anom.median(), 2)),
            "Anomaly_IQR": float(round(s_anom.quantile(0.75) - s_anom.quantile(0.25), 2)),
            "Ratio_Anomaly_to_Normal": float(round(s_anom.median() / (s_norm.median() + 1e-4), 2)),
        })
    pd.DataFrame(t12_list).to_csv(tables_path / "table12_anomaly_feature_profile.csv", index=False)
    
    # Table 13: Algorithm Consensus Confusion Matrix
    confusion_mat = pd.crosstab(
        results_df["flag_isolation_forest"],
        results_df["flag_lof"],
        rownames=["Isolation_Forest"],
        colnames=["Local_Outlier_Factor"],
        margins=True
    )
    confusion_mat.to_csv(tables_path / "table13_algorithm_consensus.csv")
    
    # Table 14: Anomaly vs Data-Quality Flags Cross-Validation
    dq_flags = [
        ("negative_charging_duration_flag", results_df["negative_charging_duration_flag"]),
        ("done_after_disconnect_flag", results_df["done_after_disconnect_flag"]),
        ("over_delivery_flag", results_df["over_delivery_flag"]),
        ("missing_done_charging_flag", (results_df["is_charging_completed"] == 0).astype(int)),
        ("anonymous_user_flag", (results_df["is_registered_user"] == 0).astype(int)),
    ]
    t14_list = []
    for flag_name, flag_series in dq_flags:
        total_flagged = int(flag_series.sum())
        in_if = int(((flag_series == 1) & (results_df["flag_isolation_forest"] == 1)).sum())
        in_lof = int(((flag_series == 1) & (results_df["flag_lof"] == 1)).sum())
        in_consensus = int(((flag_series == 1) & (results_df["is_consensus_anomaly"] == 1)).sum())
        t14_list.append({
            "Data_Quality_Flag": flag_name,
            "Total_Occurrences": total_flagged,
            "Flagged_by_Isolation_Forest": in_if,
            "Flagged_by_LOF": in_lof,
            "Flagged_by_Consensus": in_consensus,
            "Consensus_Overlap_Pct": float(round(in_consensus / max(1, total_flagged) * 100, 2)),
        })
    pd.DataFrame(t14_list).to_csv(tables_path / "table14_anomaly_vs_data_quality_flags.csv", index=False)
    
    report = {
        "total_sessions": len(results_df),
        "iforest_anomalies": count_if,
        "lof_anomalies": count_lof,
        "consensus_anomalies": overlap_count,
        "union_anomalies": union_count,
        "jaccard_similarity": jaccard,
        "pct_agreement": pct_agreement,
    }
    
    return results_df, report


def generate_anomaly_figures(
    results_df: pd.DataFrame,
    figures_dir: Union[str, Path] = "outputs/figures"
) -> Dict[str, Path]:
    """Generate 8 publication-quality figures diagnosing detected anomalies."""
    out_dir = Path(figures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    
    # Fig T: Isolation Forest Score Distribution
    out_t = out_dir / "fig_t_iforest_score_distribution.png"
    plt.figure(figsize=(9, 5))
    sns.histplot(results_df["score_isolation_forest"], bins=50, kde=True, color="#2b5c8f", edgecolor="black")
    thresh_if = results_df.loc[results_df["flag_isolation_forest"] == 1, "score_isolation_forest"].min()
    plt.axvline(thresh_if, color="crimson", linestyle="--", linewidth=1.5, label=f"Contamination Threshold (Top 3%, score >= {thresh_if:.3f})")
    plt.title("Isolation Forest Normalized Anomaly Score Distribution (n=5,000)")
    plt.xlabel("Normalized Isolation Forest Score")
    plt.ylabel("Number of Sessions")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_t, dpi=300)
    plt.close()
    paths["fig_t"] = out_t
    
    # Fig U: LOF Score Distribution
    out_u = out_dir / "fig_u_lof_score_distribution.png"
    plt.figure(figsize=(9, 5))
    sns.histplot(results_df["score_lof"], bins=50, kde=True, color="#238b45", edgecolor="black")
    thresh_lof = results_df.loc[results_df["flag_lof"] == 1, "score_lof"].min()
    plt.axvline(thresh_lof, color="crimson", linestyle="--", linewidth=1.5, label=f"Contamination Threshold (Top 3%, score >= {thresh_lof:.3f})")
    plt.title("Local Outlier Factor (LOF) Normalized Anomaly Score Distribution (n=5,000)")
    plt.xlabel("Normalized LOF Score")
    plt.ylabel("Number of Sessions")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_u, dpi=300)
    plt.close()
    paths["fig_u"] = out_u
    
    # Fig V: Normal vs Anomalous Energy Distribution
    out_v = out_dir / "fig_v_normal_vs_anomalous_energy.png"
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    norm_energy = results_df.loc[results_df["is_consensus_anomaly"] == 0, "kWhDelivered"]
    anom_energy = results_df.loc[results_df["is_consensus_anomaly"] == 1, "kWhDelivered"]
    
    sns.histplot(norm_energy, bins=40, kde=True, ax=axes[0], color="#3182bd", label=f"Typical Sessions (n={len(norm_energy)})")
    axes[0].set_title("Energy Distribution: Typical Charging Sessions")
    axes[0].set_xlabel("Energy Delivered (kWh)")
    axes[0].set_ylabel("Count")
    axes[0].legend()
    
    sns.histplot(anom_energy, bins=25, kde=True, ax=axes[1], color="#de2d26", label=f"Consensus Anomalies (n={len(anom_energy)})")
    axes[1].set_title("Energy Distribution: Consensus Anomalies")
    axes[1].set_xlabel("Energy Delivered (kWh)")
    axes[1].set_ylabel("Count")
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(out_v, dpi=300)
    plt.close()
    paths["fig_v"] = out_v
    
    # Fig W: Connection Duration vs Energy Scatter with Anomalies Highlighted
    out_w = out_dir / "fig_w_duration_vs_energy_anomalies.png"
    plt.figure(figsize=(10, 6))
    
    normal = results_df[results_df["is_consensus_anomaly"] == 0]
    consensus = results_df[results_df["is_consensus_anomaly"] == 1]
    
    plt.scatter(normal["connection_duration_hr"], normal["kWhDelivered"], color="#9ecae1", alpha=0.5, s=25, label=f"Typical Sessions ({len(normal)})")
    plt.scatter(consensus["connection_duration_hr"], consensus["kWhDelivered"], color="#cb181d", edgecolors="black", s=55, label=f"Consensus Anomalies ({len(consensus)})")
    
    plt.title("Connection Duration vs Energy Delivered (Consensus Anomalies Highlighted)")
    plt.xlabel("Connection Duration (Hours)")
    plt.ylabel("Energy Delivered (kWh)")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_w, dpi=300)
    plt.close()
    paths["fig_w"] = out_w
    
    # Fig X: Charging Rate vs Energy Scatter with Anomalies Highlighted
    out_x = out_dir / "fig_x_charging_rate_vs_energy.png"
    plt.figure(figsize=(10, 6))
    
    # Limit visualization axis for clarity (rate up to 50 kW)
    rate_cap = 45.0
    plt.scatter(normal["average_charging_rate_kw"].clip(upper=rate_cap), normal["kWhDelivered"], color="#a1d99b", alpha=0.5, s=25, label=f"Typical Sessions ({len(normal)})")
    plt.scatter(consensus["average_charging_rate_kw"].clip(upper=rate_cap), consensus["kWhDelivered"], color="#e6550d", edgecolors="black", s=55, label=f"Consensus Anomalies ({len(consensus)})")
    
    plt.title("Effective Charging Rate (kW) vs Energy Delivered")
    plt.xlabel("Effective Charging Rate (kW, Visualized up to 45 kW)")
    plt.ylabel("Energy Delivered (kWh)")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_x, dpi=300)
    plt.close()
    paths["fig_x"] = out_x
    
    # Fig Y: Anomaly Counts by Hour of Day
    out_y = out_dir / "fig_y_anomaly_counts_by_hour.png"
    plt.figure(figsize=(10, 5))
    
    hourly_anom = results_df.groupby(["conn_hour", "is_consensus_anomaly"]).size().unstack(fill_value=0)
    if 1 in hourly_anom.columns:
        plt.bar(hourly_anom.index, hourly_anom[1], color="#d73027", edgecolor="black", alpha=0.85)
    plt.title("Consensus Anomaly Occurrences by Connection Arrival Hour")
    plt.xlabel("Arrival Hour (Local Time America/Los_Angeles)")
    plt.ylabel("Count of Anomalous Sessions")
    plt.xticks(range(0, 24))
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(out_y, dpi=300)
    plt.close()
    paths["fig_y"] = out_y
    
    # Fig Z: Top Anomalous Sessions Profile (Boxplot comparison on key metrics)
    out_z = out_dir / "fig_z_anomaly_feature_comparison.png"
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    metrics = ["kWhDelivered", "connection_duration_hr", "average_charging_rate_kw"]
    titles = ["Energy Delivered (kWh)", "Connection Duration (Hours)", "Charging Rate (kW)"]
    
    for i, col in enumerate(metrics):
        results_df["group_label"] = np.where(results_df["is_consensus_anomaly"] == 1, "Anomaly", "Typical")
        sns.boxplot(x="group_label", y=col, data=results_df, ax=axes[i], palette=["#3182bd", "#de2d26"], showfliers=False, showmeans=True)
        axes[i].set_title(titles[i])
        axes[i].set_xlabel("Session Class")
        axes[i].set_ylabel(col)
        
    plt.tight_layout()
    plt.savefig(out_z, dpi=300)
    plt.close()
    paths["fig_z"] = out_z
    
    # Fig Z2: Isolation Forest vs LOF Agreement Visualization
    out_z2 = out_dir / "fig_z2_algorithm_agreement.png"
    plt.figure(figsize=(9, 6))
    
    # Scatter of normalized scores
    colors = np.where(
        results_df["is_consensus_anomaly"] == 1, "#d73027",  # Consensus in red
        np.where((results_df["flag_isolation_forest"] == 1) | (results_df["flag_lof"] == 1), "#fdae61", "#4575b4")
    )
    plt.scatter(results_df["score_isolation_forest"], results_df["score_lof"], c=colors, alpha=0.6, s=25)
    plt.axvline(thresh_if, color="gray", linestyle="--", linewidth=1.0, label="Isolation Forest Threshold")
    plt.axhline(thresh_lof, color="gray", linestyle=":", linewidth=1.0, label="LOF Threshold")
    
    plt.title("Algorithm Agreement: Isolation Forest vs LOF Scores (n=5,000)")
    plt.xlabel("Normalized Isolation Forest Score")
    plt.ylabel("Normalized LOF Score")
    plt.legend(loc="upper left", frameon=True)
    plt.tight_layout()
    plt.savefig(out_z2, dpi=300)
    plt.close()
    paths["fig_z2"] = out_z2
    
    return paths
