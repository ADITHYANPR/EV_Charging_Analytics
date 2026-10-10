"""Feature Engineering Module.

Generates session-level behavioral features and continuous hourly time-series
forecasting features with strict leakage prevention and COVID regime handling.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def engineer_session_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate session-level temporal, behavioral, and electrical features.
    
    All temporal features are derived from local California time (America/Los_Angeles).
    
    Args:
        df: Cleaned sessions DataFrame.
        
    Returns:
        DataFrame augmented with engineered session features.
    """
    df = df.copy()
    
    # Ensure local datetime format
    conn_dt = pd.to_datetime(df["connectionTime_local"])
    disc_dt = pd.to_datetime(df["disconnectTime_local"])
    
    # Local temporal features
    df["conn_hour"] = conn_dt.dt.hour
    df["conn_minute"] = conn_dt.dt.minute
    df["conn_dayofweek"] = conn_dt.dt.dayofweek  # 0=Monday, 6=Sunday
    df["conn_day_name"] = conn_dt.dt.day_name()
    df["is_weekend"] = conn_dt.dt.dayofweek.isin([5, 6]).astype(int)
    df["conn_month"] = conn_dt.dt.month
    df["conn_year"] = conn_dt.dt.year
    df["disc_hour"] = disc_dt.dt.hour
    
    # Cyclical hour encoding
    df["sin_conn_hour"] = np.sin(2 * np.pi * df["conn_hour"] / 24.0)
    df["cos_conn_hour"] = np.cos(2 * np.pi * df["conn_hour"] / 24.0)
    df["sin_dayofweek"] = np.sin(2 * np.pi * df["conn_dayofweek"] / 7.0)
    df["cos_dayofweek"] = np.cos(2 * np.pi * df["conn_dayofweek"] / 7.0)
    
    # Power & rate metrics (effective delivered kW)
    effective_charge_hr = np.where(
        df["is_charging_completed"] == 1,
        np.maximum(0.05, df["charging_duration_hr"]),
        np.maximum(0.05, df["connection_duration_hr"])
    )
    df["effective_charging_power_kw"] = df["kWhDelivered"] / effective_charge_hr
    
    # Grid flexibility metrics: idle ratio
    df["idle_ratio"] = np.where(
        df["is_charging_completed"] == 1,
        (df["idle_duration_hr"] / np.maximum(0.05, df["connection_duration_hr"])).clip(0.0, 1.0),
        np.nan
    )
    
    # Delivery fulfillment ratio
    df["delivery_ratio"] = np.where(
        df["kWhRequested"].notnull() & (df["kWhRequested"] > 0),
        df["kWhDelivered"] / df["kWhRequested"],
        np.nan
    )
    
    return df


def build_hourly_demand_series(
    df: pd.DataFrame,
    start_time: Optional[pd.Timestamp] = None,
    end_time: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Transform session records into a continuous hourly aggregated time series.
    
    Uses connection local timestamp to allocate charging demand, with continuous
    hourly reindexing so zero-activity hours are explicitly preserved.
    
    Args:
        df: Processed sessions DataFrame.
        start_time: Optional starting timestamp (local).
        end_time: Optional ending timestamp (local).
        
    Returns:
        Continuous hourly DataFrame.
    """
    df = df.copy()
    conn_series = pd.to_datetime(df["connectionTime_local"])
    df["conn_local_floor"] = conn_series.dt.floor("h")
    
    # Hourly aggregations
    hourly_agg = df.groupby("conn_local_floor").agg(
        total_kwh_delivered=("kWhDelivered", "sum"),
        session_count=("sessionID", "count"),
        avg_kwh_per_session=("kWhDelivered", "mean"),
        max_kwh_session=("kWhDelivered", "max"),
        avg_connection_duration_hr=("connection_duration_hr", "mean"),
    ).reset_index()
    
    hourly_agg.rename(columns={"conn_local_floor": "timestamp"}, inplace=True)
    
    # Create complete continuous hourly range in local timezone
    if start_time is None:
        start_time = hourly_agg["timestamp"].min()
    if end_time is None:
        end_time = hourly_agg["timestamp"].max()
        
    # Build complete uninterrupted hourly grid
    tz = start_time.tz
    full_idx = pd.date_range(start=start_time, end=end_time, freq="h", name="timestamp", tz=tz)
    full_df = pd.DataFrame(index=full_idx).reset_index()
    
    # Merge with continuous index
    merged = pd.merge(full_df, hourly_agg, on="timestamp", how="left")
    
    # Zero-fill volume and count columns
    merged["total_kwh_delivered"] = merged["total_kwh_delivered"].fillna(0.0)
    merged["session_count"] = merged["session_count"].fillna(0).astype(int)
    merged["avg_kwh_per_session"] = merged["avg_kwh_per_session"].fillna(0.0)
    merged["max_kwh_session"] = merged["max_kwh_session"].fillna(0.0)
    merged["avg_connection_duration_hr"] = merged["avg_connection_duration_hr"].fillna(0.0)
    
    return merged


def engineer_forecasting_features(hourly_df: pd.DataFrame) -> pd.DataFrame:
    """Create leak-free temporal, calendar, lag, and rolling features for forecasting.
    
    Rolling statistics are strictly shifted by 1 hour to prevent lookahead bias.
    Includes explicit COVID regime flag and peak-demand indicators.
    
    Args:
        hourly_df: Continuous hourly demand DataFrame.
        
    Returns:
        DataFrame ready for supervised time-series forecasting.
    """
    df = hourly_df.copy().sort_values("timestamp").reset_index(drop=True)
    
    # Calendar features
    ts = pd.to_datetime(df["timestamp"])
    df["hour"] = ts.dt.hour
    df["dayofweek"] = ts.dt.dayofweek
    df["is_weekend"] = ts.dt.dayofweek.isin([5, 6]).astype(int)
    df["month"] = ts.dt.month
    df["year"] = ts.dt.year
    df["date"] = ts.dt.date.astype(str)
    
    # Cyclical calendar encodings
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24.0)
    df["sin_dow"] = np.sin(2 * np.pi * df["dayofweek"] / 7.0)
    df["cos_dow"] = np.cos(2 * np.pi * df["dayofweek"] / 7.0)
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)
    
    # Peak Demand Indicators
    # Peak window: Weekday morning commute & mid-day (08:00 - 13:00)
    df["is_peak_hour_window"] = (
        (df["is_weekend"] == 0) & (df["hour"] >= 8) & (df["hour"] <= 13)
    ).astype(int)
    
    # System 95th-percentile demand threshold (computed across non-zero active demand)
    active_kwh = df.loc[df["total_kwh_delivered"] > 0, "total_kwh_delivered"]
    p95_val = float(active_kwh.quantile(0.95)) if len(active_kwh) > 0 else 50.0
    df["is_system_peak_demand_hour"] = (df["total_kwh_delivered"] >= p95_val).astype(int)
    
    # COVID-19 structural break regime indicator (California lockdown: Mar 19, 2020 - Oct 31, 2020)
    conn_tz = ts.dt.tz
    lockdown_start = pd.Timestamp("2020-03-19", tz=conn_tz)
    lockdown_end = pd.Timestamp("2020-10-31", tz=conn_tz)
    
    df["is_covid_lockdown"] = (
        (ts >= lockdown_start) & (ts <= lockdown_end)
    ).astype(int)
    
    conditions = [
        ts < lockdown_start,
        (ts >= lockdown_start) & (ts <= lockdown_end),
        ts > lockdown_end
    ]
    choices = ["Pre-Lockdown", "Lockdown", "Post-Lockdown-Recovery"]
    df["covid_period"] = np.select(conditions, choices, default="Post-Lockdown-Recovery")
    
    # Pure autoregressive lag features (hours prior)
    target = "total_kwh_delivered"
    df["lag_1"] = df[target].shift(1)
    df["lag_2"] = df[target].shift(2)
    df["lag_3"] = df[target].shift(3)
    df["lag_24"] = df[target].shift(24)       # Same hour yesterday
    df["lag_48"] = df[target].shift(48)       # Same hour 2 days ago
    df["lag_168"] = df[target].shift(168)     # Same hour last week (seasonal baseline)
    
    # Rolling statistics (strictly lagged by 1 to prevent data leakage)
    df["rolling_mean_24"] = df[target].shift(1).rolling(window=24, min_periods=1).mean()
    df["rolling_std_24"] = df[target].shift(1).rolling(window=24, min_periods=1).std().fillna(0.0)
    df["rolling_mean_168"] = df[target].shift(1).rolling(window=168, min_periods=1).mean()
    
    # Active session count lag
    if "session_count" in df.columns:
        df["lag_count_1"] = df["session_count"].shift(1)
        df["lag_count_24"] = df["session_count"].shift(24)
    else:
        df["lag_count_1"] = 0.0
        df["lag_count_24"] = 0.0
    
    return df
