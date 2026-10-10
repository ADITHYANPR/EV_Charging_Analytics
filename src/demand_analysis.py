"""Demand Analysis Module.

Quantifies aggregated EV charging energy demand, identifies peak-demand periods,
analyzes station-level utilization, and provides smart-grid flexibility metrics.
"""

import logging
from pathlib import Path
from typing import Dict, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def analyze_peak_demand_periods(hourly_df: pd.DataFrame) -> Dict[str, Union[float, pd.DataFrame]]:
    """Identify peak aggregated charging demand hours and calculate grid metrics.
    
    Args:
        hourly_df: Continuous hourly demand series.
        
    Returns:
        Dictionary of peak demand metrics and hourly profiles.
    """
    df = hourly_df.copy()
    ts = pd.to_datetime(df["timestamp"])
    df["hour"] = ts.dt.hour
    df["dayofweek"] = ts.dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    
    # Profile by hour of day
    hourly_profile = df.groupby("hour")["total_kwh_delivered"].agg(
        mean_kwh="mean",
        std_kwh="std",
        median_kwh="median",
        p95_kwh=lambda x: np.percentile(x, 95),
        max_kwh="max"
    ).reset_index()
    
    # Peak hour identification
    peak_hour = int(hourly_profile.loc[hourly_profile["mean_kwh"].idxmax(), "hour"])
    peak_mean_kwh = float(hourly_profile["mean_kwh"].max())
    
    # Weekday vs Weekend profile
    dow_profile = df.groupby(["is_weekend", "hour"])["total_kwh_delivered"].mean().unstack(level=0)
    dow_profile.columns = ["Weekday_Mean_kWh", "Weekend_Mean_kWh"]
    
    # System peak demand hour overall
    overall_peak_idx = df["total_kwh_delivered"].idxmax()
    overall_peak_row = df.loc[overall_peak_idx]
    
    metrics = {
        "peak_hour_of_day": peak_hour,
        "peak_hour_mean_kwh": peak_mean_kwh,
        "historical_max_hourly_kwh": float(overall_peak_row["total_kwh_delivered"]),
        "historical_max_timestamp": str(overall_peak_row["timestamp"]),
        "total_energy_delivered_mwh": float(df["total_kwh_delivered"].sum() / 1000.0),
        "hourly_profile": hourly_profile,
        "weekday_weekend_profile": dow_profile,
    }
    
    return metrics


def analyze_station_utilization(session_df: pd.DataFrame) -> pd.DataFrame:
    """Evaluate charger hardware utilization and total throughput across stations.
    
    Args:
        session_df: Processed sessions DataFrame.
        
    Returns:
        DataFrame ranking stations by throughput, session count, and idle time.
    """
    station_stats = session_df.groupby("stationID").agg(
        total_sessions=("sessionID", "count"),
        total_kwh_delivered=("kWhDelivered", "sum"),
        avg_kwh_per_session=("kWhDelivered", "mean"),
        total_connection_hours=("connection_duration_hr", "sum"),
        avg_connection_hours=("connection_duration_hr", "mean"),
        total_idle_hours=("idle_duration_hr", "sum"),
    ).reset_index()
    
    station_stats["kwh_rank"] = station_stats["total_kwh_delivered"].rank(ascending=False).astype(int)
    station_stats = station_stats.sort_values("total_kwh_delivered", ascending=False).reset_index(drop=True)
    return station_stats
