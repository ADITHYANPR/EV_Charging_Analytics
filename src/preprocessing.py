"""Preprocessing Module.

Flattens nested userInputs, standardizes timezone (preserving UTC and converting to
America/Los_Angeles), validates ranges, preserves missing-value indicators, and
creates clean, analysis-ready session and hourly demand datasets.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def flatten_raw_sessions(raw_sessions: List[Dict[str, Any]]) -> pd.DataFrame:
    """Flatten list of raw session dictionaries into a tabular DataFrame.
    
    Preserves missing values through explicit indicators.
    For multi-input sessions, extracts the final driver submission while tracking
    the total count of amendments. Preserves all 5,000 records without loss.
    
    Args:
        raw_sessions: List of raw dictionary objects.
        
    Returns:
        Flattened pandas DataFrame with 5,000 rows.
    """
    flattened_rows = []
    
    for item in raw_sessions:
        row: Dict[str, Any] = {
            "_id": item.get("_id"),
            "sessionID": item.get("sessionID"),
            "stationID": str(item.get("stationID")),
            "spaceID": str(item.get("spaceID")),
            "siteID": str(item.get("siteID")),
            "clusterID": str(item.get("clusterID")),
            "userID": item.get("userID"),
            "connectionTime_raw": item.get("connectionTime"),
            "disconnectTime_raw": item.get("disconnectTime"),
            "doneChargingTime_raw": item.get("doneChargingTime"),
            "kWhDelivered": float(item.get("kWhDelivered", 0.0)),
            "timezone_str": item.get("timezone", "America/Los_Angeles"),
        }
        
        user_inputs = item.get("userInputs")
        if isinstance(user_inputs, list) and len(user_inputs) > 0:
            row["has_user_inputs"] = 1
            row["user_inputs_count"] = len(user_inputs)
            # Use final submitted input as driver's last updated request
            final_ui = user_inputs[-1]
            row["milesRequested"] = final_ui.get("milesRequested")
            row["WhPerMile"] = final_ui.get("WhPerMile")
            row["kWhRequested"] = final_ui.get("kWhRequested")
            row["minutesAvailable"] = final_ui.get("minutesAvailable")
            row["requestedDeparture_raw"] = final_ui.get("requestedDeparture")
            row["modifiedAt_raw"] = final_ui.get("modifiedAt")
            row["paymentRequired"] = final_ui.get("paymentRequired", True)
        else:
            row["has_user_inputs"] = 0
            row["user_inputs_count"] = 0
            row["milesRequested"] = np.nan
            row["WhPerMile"] = np.nan
            row["kWhRequested"] = np.nan
            row["minutesAvailable"] = np.nan
            row["requestedDeparture_raw"] = None
            row["modifiedAt_raw"] = None
            row["paymentRequired"] = np.nan
            
        flattened_rows.append(row)
        
    df = pd.DataFrame(flattened_rows)
    return df


def standardize_timestamps(
    df: pd.DataFrame, 
    target_timezone: str = "America/Los_Angeles"
) -> pd.DataFrame:
    """Parse timestamps to UTC and convert to local target timezone.
    
    Preserves original UTC timestamps and creates local datetime fields.
    Computes duration metrics with explicit handling of sensor anomalies.
    
    Args:
        df: Flattened sessions DataFrame.
        target_timezone: Local timezone string (default: 'America/Los_Angeles').
        
    Returns:
        DataFrame with standardized datetime columns and duration metrics.
    """
    df = df.copy()
    
    # Parse RFC 2822 timestamps to UTC and convert to target local timezone
    for col in ["connectionTime", "disconnectTime", "doneChargingTime", "requestedDeparture", "modifiedAt"]:
        raw_col = f"{col}_raw"
        if raw_col in df.columns:
            df[f"{col}_utc"] = pd.to_datetime(df[raw_col], utc=True, errors="coerce")
            df[f"{col}_local"] = df[f"{col}_utc"].dt.tz_convert(target_timezone)
            
    # Connection duration in minutes and hours
    df["connection_duration_min"] = (
        df["disconnectTime_utc"] - df["connectionTime_utc"]
    ).dt.total_seconds() / 60.0
    df["connection_duration_hr"] = df["connection_duration_min"] / 60.0
    
    # Charging completion indicator
    df["is_charging_completed"] = df["doneChargingTime_utc"].notnull().astype(int)
    
    # Calculate raw charging duration
    charging_duration_raw = (
        df["doneChargingTime_utc"] - df["connectionTime_utc"]
    ).dt.total_seconds() / 60.0
    
    # Flag known anomaly: negative duration (clipped to 0.0 with documentation flag)
    df["negative_charging_duration_flag"] = (charging_duration_raw < 0).fillna(False).astype(int)
    df["charging_duration_min"] = charging_duration_raw.clip(lower=0.0)
    df["charging_duration_hr"] = df["charging_duration_min"] / 60.0
    
    # Flag where doneChargingTime exceeds disconnectTime
    excess_sec = (df["doneChargingTime_utc"] - df["disconnectTime_utc"]).dt.total_seconds()
    df["done_after_disconnect_flag"] = (excess_sec > 0).fillna(False).astype(int)
    df["done_after_disconnect_excess_min"] = np.where(
        df["done_after_disconnect_flag"] == 1,
        excess_sec / 60.0,
        0.0
    )
    
    # Idle connection duration (time vehicle occupies charger after charging finishes)
    idle_raw = df["connection_duration_min"] - df["charging_duration_min"]
    df["idle_duration_min"] = np.where(
        df["is_charging_completed"] == 1,
        np.maximum(0.0, idle_raw),
        np.nan
    )
    df["idle_duration_hr"] = df["idle_duration_min"] / 60.0
    
    # Idle to connection ratio (flexibility indicator)
    df["idle_to_connection_ratio"] = np.where(
        df["is_charging_completed"] == 1,
        (df["idle_duration_min"] / np.maximum(1.0, df["connection_duration_min"])).clip(0.0, 1.0),
        np.nan
    )
    
    return df


def clean_and_impute_sessions(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean records, flag edge cases, and add explicit missing indicators.
    
    Args:
        df: Sessions DataFrame with standardized timestamps.
        
    Returns:
        Tuple of (cleaned DataFrame, summary report dictionary).
    """
    df = df.copy()
    
    # Flag registered vs anonymous users
    df["is_registered_user"] = df["userID"].notnull().astype(int)
    df["user_id_clean"] = df["userID"].fillna("ANONYMOUS")
    
    # Energy error: requested - delivered
    df["energy_error_kwh"] = df["kWhRequested"] - df["kWhDelivered"]
    
    # Delivery fulfillment ratio: delivered / requested
    df["delivery_ratio"] = np.where(
        df["kWhRequested"].notnull() & (df["kWhRequested"] > 0),
        df["kWhDelivered"] / df["kWhRequested"],
        np.nan
    )
    
    # Over-delivery flag: delivered > requested
    df["over_delivery_flag"] = (
        (df["kWhDelivered"] > df["kWhRequested"]) & df["kWhRequested"].notnull()
    ).astype(int)
    
    # Average charging rate (kW)
    # Uses actual charging duration where available, otherwise connection duration
    active_charge_hr = np.where(
        df["is_charging_completed"] == 1,
        np.maximum(0.05, df["charging_duration_hr"]),
        np.maximum(0.05, df["connection_duration_hr"])
    )
    df["average_charging_rate_kw"] = df["kWhDelivered"] / active_charge_hr
    
    # Local temporal features
    conn_local = pd.to_datetime(df["connectionTime_local"])
    disc_local = pd.to_datetime(df["disconnectTime_local"])
    
    df["conn_hour"] = conn_local.dt.hour
    df["conn_minute"] = conn_local.dt.minute
    df["conn_dayofweek"] = conn_local.dt.dayofweek  # 0=Monday, 6=Sunday
    df["conn_day_name"] = conn_local.dt.day_name()
    df["is_weekend"] = conn_local.dt.dayofweek.isin([5, 6]).astype(int)
    df["conn_month"] = conn_local.dt.month
    df["conn_year"] = conn_local.dt.year
    df["conn_date"] = conn_local.dt.date.astype(str)
    df["disc_hour"] = disc_local.dt.hour
    
    # Cyclical encodings
    df["sin_conn_hour"] = np.sin(2 * np.pi * df["conn_hour"] / 24.0)
    df["cos_conn_hour"] = np.cos(2 * np.pi * df["conn_hour"] / 24.0)
    df["sin_dayofweek"] = np.sin(2 * np.pi * df["conn_dayofweek"] / 7.0)
    df["cos_dayofweek"] = np.cos(2 * np.pi * df["conn_dayofweek"] / 7.0)
    
    # COVID-19 Period Categorization
    # Pre-Lockdown: before Mar 19, 2020
    # Lockdown: Mar 19, 2020 to Oct 31, 2020
    # Post-Lockdown Recovery: Nov 1, 2020 onwards
    conn_tz = conn_local.dt.tz
    lockdown_start = pd.Timestamp("2020-03-19", tz=conn_tz)
    lockdown_end = pd.Timestamp("2020-10-31", tz=conn_tz)
    
    conditions = [
        conn_local < lockdown_start,
        (conn_local >= lockdown_start) & (conn_local <= lockdown_end),
        conn_local > lockdown_end
    ]
    choices = ["Pre-Lockdown", "Lockdown", "Post-Lockdown-Recovery"]
    df["covid_period"] = np.select(conditions, choices, default="Post-Lockdown-Recovery")
    df["is_covid_lockdown"] = (df["covid_period"] == "Lockdown").astype(int)
    
    report = {
        "total_sessions_processed": len(df),
        "registered_sessions": int(df["is_registered_user"].sum()),
        "anonymous_sessions": int((df["is_registered_user"] == 0).sum()),
        "completed_charging_count": int(df["is_charging_completed"].sum()),
        "missing_done_charging_count": int((df["is_charging_completed"] == 0).sum()),
        "negative_charging_duration_count": int(df["negative_charging_duration_flag"].sum()),
        "done_after_disconnect_count": int(df["done_after_disconnect_flag"].sum()),
        "over_delivery_count": int(df["over_delivery_flag"].sum()),
        "covid_period_counts": df["covid_period"].value_counts().to_dict(),
        "kwh_delivered_min": float(df["kWhDelivered"].min()),
        "kwh_delivered_max": float(df["kWhDelivered"].max()),
        "kwh_delivered_mean": float(df["kWhDelivered"].mean()),
        "connection_duration_hr_median": float(df["connection_duration_hr"].median()),
    }
    
    logger.info(f"Preprocessing completed: {report}")
    return df, report


def preprocess_dataset(
    raw_filepath: Union[str, Path] = "data/raw/acn_caltech_5000.json",
    output_session_path: Optional[Union[str, Path]] = "data/processed/cleaned_sessions.csv",
    output_hourly_path: Optional[Union[str, Path]] = "data/processed/hourly_demand.csv",
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Run full preprocessing pipeline from raw JSON to clean sessions and hourly demand.
    
    Args:
        raw_filepath: Path to raw JSON dataset.
        output_session_path: Path to save cleaned_sessions.csv.
        output_hourly_path: Path to save hourly_demand.csv.
        
    Returns:
        Tuple of (cleaned sessions DataFrame, continuous hourly demand DataFrame, report).
    """
    from src.data_loader import load_raw_dataset
    from src.feature_engineering import build_hourly_demand_series, engineer_forecasting_features
    
    raw_data = load_raw_dataset(raw_filepath)
    df_flat = flatten_raw_sessions(raw_data)
    df_timed = standardize_timestamps(df_flat)
    df_clean, report = clean_and_impute_sessions(df_timed)
    
    # Build continuous hourly demand series
    hourly_raw = build_hourly_demand_series(df_clean)
    hourly_features = engineer_forecasting_features(hourly_raw)
    
    if output_session_path:
        out_sess = Path(output_session_path)
        out_sess.parent.mkdir(parents=True, exist_ok=True)
        df_clean.to_csv(out_sess, index=False)
        logger.info(f"Saved cleaned sessions to {out_sess}")
        
    if output_hourly_path:
        out_hr = Path(output_hourly_path)
        out_hr.parent.mkdir(parents=True, exist_ok=True)
        hourly_features.to_csv(out_hr, index=False)
        logger.info(f"Saved hourly demand to {out_hr}")
        
    report["hourly_records"] = len(hourly_features)
    report["hourly_start"] = str(hourly_features["timestamp"].min())
    report["hourly_end"] = str(hourly_features["timestamp"].max())
    
    return df_clean, hourly_features, report
