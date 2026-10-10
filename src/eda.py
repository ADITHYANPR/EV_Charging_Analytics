"""Exploratory Data Analysis Module.

Generates 12 publication-quality figures and 5 empirical summary tables:
- Fig A: Distribution of charging energy (kWh delivered)
- Fig B: Session connection and charging duration distributions
- Fig C: Aggregated hourly EV charging energy demand time series
- Fig D: Aggregated daily EV charging energy demand time series
- Fig E: Charging demand by hour of day (Weekday vs Weekend profile)
- Fig F: Charging demand by day of week
- Fig G: Monthly EV charging demand and active session trends
- Fig H: Session count over time
- Fig I: Station-level charging throughput and utilization
- Fig J: Requested vs delivered energy comparison
- Fig K: Charging behavior across COVID-19 restriction periods
- Fig L: Peak-demand temporal heatmap (Day of Week vs Hour of Day)
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

# Configure publication-grade styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.sans-serif": "Arial",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
})


def plot_fig_a_energy_distribution(df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig A: Distribution of session charging energy (kWh)."""
    out_path = out_dir / "fig_a_energy_distribution.png"
    plt.figure(figsize=(9, 5))
    
    kwh = df["kWhDelivered"]
    sns.histplot(kwh, bins=45, kde=True, color="#1f77b4", edgecolor="black", alpha=0.7)
    median_val = kwh.median()
    mean_val = kwh.mean()
    p95_val = kwh.quantile(0.95)
    
    plt.axvline(median_val, color="crimson", linestyle="--", linewidth=1.5, label=f"Median: {median_val:.2f} kWh")
    plt.axvline(mean_val, color="darkorange", linestyle="-", linewidth=1.5, label=f"Mean: {mean_val:.2f} kWh")
    plt.axvline(p95_val, color="purple", linestyle=":", linewidth=1.5, label=f"95th Pct: {p95_val:.2f} kWh")
    
    plt.title("Distribution of EV Charging Energy Delivered per Session (n=5,000)")
    plt.xlabel("Energy Delivered (kWh)")
    plt.ylabel("Number of Sessions")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_b_duration_distribution(df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig B: Distribution of connection and charging duration."""
    out_path = out_dir / "fig_b_duration_distribution.png"
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Connection duration (capped at 24h for visual clarity)
    conn_dur = df["connection_duration_hr"].clip(upper=24)
    sns.histplot(conn_dur, bins=40, kde=True, ax=axes[0], color="#2ca02c", edgecolor="black", alpha=0.7)
    axes[0].axvline(df["connection_duration_hr"].median(), color="crimson", linestyle="--",
                    label=f"Median: {df['connection_duration_hr'].median():.2f} h")
    axes[0].set_title("Connection Duration (Parked Time, Capped at 24h)")
    axes[0].set_xlabel("Duration (Hours)")
    axes[0].set_ylabel("Number of Sessions")
    axes[0].legend()
    
    # Active charging duration (for sessions with recorded doneChargingTime)
    completed = df.loc[df["is_charging_completed"] == 1, "charging_duration_hr"].clip(upper=12)
    sns.histplot(completed, bins=35, kde=True, ax=axes[1], color="#ff7f0e", edgecolor="black", alpha=0.7)
    axes[1].axvline(completed.median(), color="crimson", linestyle="--",
                    label=f"Median: {completed.median():.2f} h")
    axes[1].set_title("Active Charging Duration (Power Draw Time, n=3,427)")
    axes[1].set_xlabel("Duration (Hours)")
    axes[1].set_ylabel("Number of Sessions")
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_c_hourly_demand_series(hourly_df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig C: Aggregated continuous hourly EV charging energy demand."""
    out_path = out_dir / "fig_c_hourly_charging_demand.png"
    plt.figure(figsize=(15, 5))
    
    ts = pd.to_datetime(hourly_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    plt.plot(ts, hourly_df["total_kwh_delivered"], color="#3182bd", linewidth=0.7, alpha=0.85, label="Hourly Energy Demand (kWh)")
    
    # Highlight lockdown period
    lockdown_start = pd.Timestamp("2020-03-19", tz="America/Los_Angeles")
    lockdown_end = pd.Timestamp("2020-10-31", tz="America/Los_Angeles")
    plt.axvspan(lockdown_start, lockdown_end, color="gray", alpha=0.2, label="COVID-19 Campus Lockdown Period")
    
    plt.title("Aggregated Hourly EV Charging Energy Demand (Caltech Campus: Jan 2020 – Sep 2021)")
    plt.xlabel("Date (Local Time America/Los_Angeles)")
    plt.ylabel("Aggregated Energy Demand (kWh)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.legend(loc="upper right", frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_d_daily_demand_series(hourly_df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig D: Aggregated daily EV charging energy demand."""
    out_path = out_dir / "fig_d_daily_charging_demand.png"
    plt.figure(figsize=(15, 5))
    
    h_df = hourly_df.copy()
    h_df["date"] = pd.to_datetime(h_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles").dt.date
    daily = h_df.groupby("date")["total_kwh_delivered"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    
    # Rolling 7-day average
    daily["rolling_7d"] = daily["total_kwh_delivered"].rolling(7, min_periods=1).mean()
    
    plt.bar(daily["date"], daily["total_kwh_delivered"], color="#6baed6", width=1.0, alpha=0.6, label="Daily Total Demand (kWh)")
    plt.plot(daily["date"], daily["rolling_7d"], color="#08519c", linewidth=2.0, label="7-Day Moving Average")
    
    plt.title("Daily Aggregated EV Charging Energy Demand")
    plt.xlabel("Date")
    plt.ylabel("Daily Energy Demand (kWh)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_e_demand_by_hour(hourly_df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig E: Average charging demand across 24 hours of day (Weekday vs Weekend)."""
    out_path = out_dir / "fig_e_demand_by_hour_of_day.png"
    plt.figure(figsize=(10, 5))
    
    h_df = hourly_df.copy()
    ts = pd.to_datetime(h_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    h_df["hour"] = ts.dt.hour
    h_df["is_weekend"] = ts.dt.dayofweek.isin([5, 6]).astype(int)
    
    hourly_profiles = h_df.groupby(["hour", "is_weekend"])["total_kwh_delivered"].mean().unstack()
    
    plt.plot(hourly_profiles.index, hourly_profiles[0], marker="o", color="#08519c", linewidth=2.2, label="Weekdays (Mon–Fri)")
    plt.plot(hourly_profiles.index, hourly_profiles[1], marker="s", color="#e6550d", linewidth=2.2, linestyle="--", label="Weekends (Sat–Sun)")
    
    plt.title("Diurnal Aggregated EV Charging Demand Profile by Hour of Day")
    plt.xlabel("Hour of Day (Local Time America/Los_Angeles)")
    plt.ylabel("Mean Energy Demand (kWh)")
    plt.xticks(range(0, 24))
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_f_demand_by_day_of_week(hourly_df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig F: EV charging demand by day of week."""
    out_path = out_dir / "fig_f_demand_by_day_of_week.png"
    plt.figure(figsize=(9, 5))
    
    h_df = hourly_df.copy()
    ts = pd.to_datetime(h_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    h_df["dow"] = ts.dt.dayofweek
    dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    dow_agg = h_df.groupby("dow")["total_kwh_delivered"].agg(mean_hourly="mean", total_kwh="sum")
    dow_agg.index = dow_names
    
    colors = ["#2171b5" if i < 5 else "#cb181d" for i in range(7)]
    plt.bar(dow_agg.index, dow_agg["mean_hourly"], color=colors, edgecolor="black", alpha=0.8)
    
    plt.title("Average Hourly EV Energy Demand by Day of Week")
    plt.xlabel("Day of Week")
    plt.ylabel("Mean Hourly Energy Demand (kWh)")
    plt.tick_params(axis="x", rotation=25)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_g_monthly_demand_trend(df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig G: Monthly EV charging demand and active sessions."""
    out_path = out_dir / "fig_g_monthly_demand_trend.png"
    fig, ax1 = plt.subplots(figsize=(12, 5))
    
    conn_dt = pd.to_datetime(df["connectionTime_local"], utc=True).dt.tz_convert("America/Los_Angeles")
    df_temp = df.copy()
    df_temp["year_month"] = conn_dt.dt.to_period("M").astype(str)
    
    monthly = df_temp.groupby("year_month").agg(
        total_kwh=("kWhDelivered", "sum"),
        session_count=("sessionID", "count")
    ).reset_index()
    
    # Sort chronologically
    monthly = monthly.sort_values("year_month").reset_index(drop=True)
    
    x = np.arange(len(monthly))
    width = 0.4
    
    ax1.bar(x - width/2, monthly["total_kwh"], width, color="#1f77b4", label="Total Energy Delivered (kWh)")
    ax1.set_ylabel("Total Monthly Energy (kWh)", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1.set_xticks(x)
    ax1.set_xticklabels(monthly["year_month"], rotation=45, ha="right")
    
    ax2 = ax1.twinx()
    ax2.plot(x + width/2, monthly["session_count"], color="#d62728", marker="o", linewidth=2.0, label="Session Count")
    ax2.set_ylabel("Monthly Session Count", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax2.grid(False)
    
    plt.title("Monthly EV Charging Demand & Session Volume (Jan 2020 – Sep 2021)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_h_session_count_timeline(hourly_df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig H: Daily session count over time."""
    out_path = out_dir / "fig_h_session_count_timeline.png"
    plt.figure(figsize=(15, 5))
    
    h_df = hourly_df.copy()
    h_df["date"] = pd.to_datetime(h_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles").dt.date
    daily_sessions = h_df.groupby("date")["session_count"].sum().reset_index()
    daily_sessions["date"] = pd.to_datetime(daily_sessions["date"])
    
    plt.plot(daily_sessions["date"], daily_sessions["session_count"], color="#31a354", linewidth=1.2, alpha=0.85)
    plt.title("Daily Active Charging Session Volume (Jan 2020 – Sep 2021)")
    plt.xlabel("Date")
    plt.ylabel("Number of Sessions per Day")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_i_station_behavior(df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig I: Station-level charging behavior (Top 12 most active chargers)."""
    out_path = out_dir / "fig_i_station_charging_behavior.png"
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    top_stations = df.groupby("stationID").agg(
        total_kwh=("kWhDelivered", "sum"),
        sessions=("sessionID", "count")
    ).sort_values("total_kwh", ascending=False).head(12)
    
    # Total kWh delivered
    axes[0].barh(top_stations.index[::-1], top_stations["total_kwh"][::-1], color="#3182bd", edgecolor="black")
    axes[0].set_title("Top 12 Stations by Total Energy Delivered (kWh)")
    axes[0].set_xlabel("Total Energy Delivered (kWh)")
    
    # Session counts
    axes[1].barh(top_stations.index[::-1], top_stations["sessions"][::-1], color="#74c476", edgecolor="black")
    axes[1].set_title("Session Count for Top 12 Stations")
    axes[1].set_xlabel("Total Sessions")
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_j_requested_vs_delivered(df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig J: Requested vs Delivered energy with 1:1 parity line."""
    out_path = out_dir / "fig_j_requested_vs_delivered.png"
    plt.figure(figsize=(8, 7))
    
    valid = df.dropna(subset=["kWhRequested", "kWhDelivered"]).copy()
    
    over = valid[valid["over_delivery_flag"] == 1]
    normal = valid[valid["over_delivery_flag"] == 0]
    
    plt.scatter(normal["kWhRequested"], normal["kWhDelivered"], alpha=0.35, color="#2b5c8f", s=25, label=f"Delivered <= Requested ({len(normal)})")
    plt.scatter(over["kWhRequested"], over["kWhDelivered"], alpha=0.65, color="#e41a1c", s=30, label=f"Over-Delivered ({len(over)})")
    
    max_val = max(valid["kWhRequested"].max(), valid["kWhDelivered"].max())
    plt.plot([0, max_val], [0, max_val], color="black", linestyle="--", linewidth=1.5, label="1:1 Parity Line")
    
    plt.title("Driver Requested Energy vs Actual Delivered Energy (n=4,410)")
    plt.xlabel("Requested Energy (kWh)")
    plt.ylabel("Delivered Energy (kWh)")
    plt.xlim(0, 160)
    plt.ylim(0, 85)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_k_covid_period_comparison(df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig K: Charging session behavior during different COVID periods."""
    out_path = out_dir / "fig_k_covid_period_comparison.png"
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    period_order = ["Pre-Lockdown", "Lockdown", "Post-Lockdown-Recovery"]
    palette = {"Pre-Lockdown": "#377eb8", "Lockdown": "#e41a1c", "Post-Lockdown-Recovery": "#4daf4a"}
    
    # kWh delivered distribution
    sns.boxplot(x="covid_period", y="kWhDelivered", data=df, order=period_order, palette=palette, ax=axes[0], showmeans=True)
    axes[0].set_title("Energy Delivered per Session across COVID Periods")
    axes[0].set_xlabel("Period")
    axes[0].set_ylabel("Energy Delivered (kWh)")
    
    # Connection duration (capped at 24h)
    df_temp = df.copy()
    df_temp["conn_dur_cap"] = df_temp["connection_duration_hr"].clip(upper=24)
    sns.boxplot(x="covid_period", y="conn_dur_cap", data=df_temp, order=period_order, palette=palette, ax=axes[1], showmeans=True)
    axes[1].set_title("Connection Duration (Parked Hours, Capped at 24h)")
    axes[1].set_xlabel("Period")
    axes[1].set_ylabel("Duration (Hours)")
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_fig_l_peak_demand_heatmap(hourly_df: pd.DataFrame, out_dir: Path) -> Path:
    """Fig L: Peak-demand temporal heatmap (Day of Week vs Hour of Day)."""
    out_path = out_dir / "fig_l_peak_demand_heatmap.png"
    plt.figure(figsize=(11, 6))
    
    h_df = hourly_df.copy()
    ts = pd.to_datetime(h_df["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
    h_df["hour"] = ts.dt.hour
    h_df["dow"] = ts.dt.dayofweek
    dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    pivot = h_df.pivot_table(index="dow", columns="hour", values="total_kwh_delivered", aggfunc="mean")
    pivot.index = dow_names
    
    sns.heatmap(pivot, cmap="YlOrRd", cbar_kws={"label": "Mean Aggregated Energy Demand (kWh)"})
    plt.title("Aggregated EV Charging Demand Heatmap: Day of Week vs Hour of Day")
    plt.xlabel("Hour of Day (Local Time America/Los_Angeles)")
    plt.ylabel("Day of Week")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def generate_all_eda_figures(
    session_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    figures_dir: Union[str, Path] = "outputs/figures",
) -> Dict[str, Path]:
    """Generate all 12 publication-quality EDA figures."""
    out_dir = Path(figures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    fig_paths = {
        "fig_a": plot_fig_a_energy_distribution(session_df, out_dir),
        "fig_b": plot_fig_b_duration_distribution(session_df, out_dir),
        "fig_c": plot_fig_c_hourly_demand_series(hourly_df, out_dir),
        "fig_d": plot_fig_d_daily_demand_series(hourly_df, out_dir),
        "fig_e": plot_fig_e_demand_by_hour(hourly_df, out_dir),
        "fig_f": plot_fig_f_demand_by_day_of_week(hourly_df, out_dir),
        "fig_g": plot_fig_g_monthly_demand_trend(session_df, out_dir),
        "fig_h": plot_fig_h_session_count_timeline(hourly_df, out_dir),
        "fig_i": plot_fig_i_station_behavior(session_df, out_dir),
        "fig_j": plot_fig_j_requested_vs_delivered(session_df, out_dir),
        "fig_k": plot_fig_k_covid_period_comparison(session_df, out_dir),
        "fig_l": plot_fig_l_peak_demand_heatmap(hourly_df, out_dir),
    }
    
    for k, p in fig_paths.items():
        logger.info(f"Generated {k}: {p}")
        
    return fig_paths


def generate_summary_tables(
    session_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    tables_dir: Union[str, Path] = "outputs/tables",
) -> Dict[str, Path]:
    """Generate descriptive statistics and summary tables."""
    out_dir = Path(tables_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    paths = {}
    
    # Table 1: Session Numerical Variables Summary Statistics
    num_cols = [
        "kWhDelivered", "kWhRequested", "milesRequested", "WhPerMile",
        "minutesAvailable", "connection_duration_hr", "charging_duration_hr",
        "idle_duration_hr", "idle_to_connection_ratio", "average_charging_rate_kw"
    ]
    t1_list = []
    for col in num_cols:
        if col in session_df.columns:
            s = session_df[col].dropna()
            t1_list.append({
                "Variable": col,
                "Count": int(len(s)),
                "Missing": int(len(session_df) - len(s)),
                "Missing_Pct": float(round((len(session_df) - len(s)) / len(session_df) * 100, 2)),
                "Mean": float(round(s.mean(), 3)),
                "Std": float(round(s.std(), 3)),
                "Min": float(round(s.min(), 3)),
                "Q25": float(round(s.quantile(0.25), 3)),
                "Median": float(round(s.median(), 3)),
                "Q75": float(round(s.quantile(0.75), 3)),
                "Max": float(round(s.max(), 3)),
                "Skewness": float(round(s.skew(), 3)),
                "Kurtosis": float(round(s.kurtosis(), 3)),
            })
    t1_df = pd.DataFrame(t1_list)
    t1_path = out_dir / "table1_session_summary_stats.csv"
    t1_df.to_csv(t1_path, index=False)
    paths["table1"] = t1_path
    
    # Table 2: Hourly & Daily Temporal Demand Summary
    h_s = hourly_df["total_kwh_delivered"]
    h_active = hourly_df.loc[hourly_df["total_kwh_delivered"] > 0, "total_kwh_delivered"]
    
    # Daily aggregation
    h_temp = hourly_df.copy()
    h_temp["date"] = pd.to_datetime(h_temp["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles").dt.date
    daily_s = h_temp.groupby("date")["total_kwh_delivered"].sum()
    
    t2_df = pd.DataFrame([
        {
            "Metric_Level": "Hourly (All Continuous Hours, n=14400)",
            "Total_MWh": float(round(h_s.sum() / 1000.0, 3)),
            "Mean_kWh": float(round(h_s.mean(), 3)),
            "Std_kWh": float(round(h_s.std(), 3)),
            "Median_kWh": float(round(h_s.median(), 3)),
            "P95_kWh": float(round(h_s.quantile(0.95), 3)),
            "Max_kWh": float(round(h_s.max(), 3)),
            "Zero_Demand_Hours": int((h_s == 0).sum()),
            "Zero_Demand_Pct": float(round((h_s == 0).mean() * 100, 2)),
        },
        {
            "Metric_Level": "Hourly (Active Demand Hours Only)",
            "Total_MWh": float(round(h_active.sum() / 1000.0, 3)),
            "Mean_kWh": float(round(h_active.mean(), 3)),
            "Std_kWh": float(round(h_active.std(), 3)),
            "Median_kWh": float(round(h_active.median(), 3)),
            "P95_kWh": float(round(h_active.quantile(0.95), 3)),
            "Max_kWh": float(round(h_active.max(), 3)),
            "Zero_Demand_Hours": 0,
            "Zero_Demand_Pct": 0.0,
        },
        {
            "Metric_Level": "Daily Total Aggregation",
            "Total_MWh": float(round(daily_s.sum() / 1000.0, 3)),
            "Mean_kWh": float(round(daily_s.mean(), 3)),
            "Std_kWh": float(round(daily_s.std(), 3)),
            "Median_kWh": float(round(daily_s.median(), 3)),
            "P95_kWh": float(round(daily_s.quantile(0.95), 3)),
            "Max_kWh": float(round(daily_s.max(), 3)),
            "Zero_Demand_Hours": int((daily_s == 0).sum()),
            "Zero_Demand_Pct": float(round((daily_s == 0).mean() * 100, 2)),
        }
    ])
    t2_path = out_dir / "table2_temporal_demand_summary.csv"
    t2_df.to_csv(t2_path, index=False)
    paths["table2"] = t2_path
    
    # Table 3: Station Utilization Summary
    t3_df = session_df.groupby("stationID").agg(
        Total_Sessions=("sessionID", "count"),
        Total_kWh_Delivered=("kWhDelivered", "sum"),
        Mean_kWh_Per_Session=("kWhDelivered", "mean"),
        Total_Connection_Hours=("connection_duration_hr", "sum"),
        Mean_Connection_Hours=("connection_duration_hr", "mean"),
        Total_Idle_Hours=("idle_duration_hr", "sum"),
    ).reset_index()
    t3_df = t3_df.sort_values("Total_kWh_Delivered", ascending=False).reset_index(drop=True)
    t3_path = out_dir / "table3_station_utilization_summary.csv"
    t3_df.to_csv(t3_path, index=False)
    paths["table3"] = t3_path
    
    # Table 4: COVID Period Comparison
    t4_df = session_df.groupby("covid_period").agg(
        Session_Count=("sessionID", "count"),
        Total_kWh=("kWhDelivered", "sum"),
        Mean_kWh_Per_Session=("kWhDelivered", "mean"),
        Median_kWh_Per_Session=("kWhDelivered", "median"),
        Mean_Connection_Hours=("connection_duration_hr", "mean"),
        Median_Connection_Hours=("connection_duration_hr", "median"),
        Over_Delivery_Sessions=("over_delivery_flag", "sum"),
    ).reset_index()
    t4_path = out_dir / "table4_covid_period_comparison.csv"
    t4_df.to_csv(t4_path, index=False)
    paths["table4"] = t4_path
    
    # Table 5: Data Quality Flags Summary
    t5_df = pd.DataFrame([
        {"Flag_Name": "negative_charging_duration_flag", "Count": int(session_df["negative_charging_duration_flag"].sum()), "Treatment": "Floored charging duration to 0.0 with flag preserved"},
        {"Flag_Name": "done_after_disconnect_flag", "Count": int(session_df["done_after_disconnect_flag"].sum()), "Treatment": "Flag preserved; idle duration handled as max(0, conn - charge)"},
        {"Flag_Name": "over_delivery_flag", "Count": int(session_df["over_delivery_flag"].sum()), "Treatment": "Flag preserved; energy_error_kwh calculated"},
        {"Flag_Name": "is_charging_completed == 0", "Count": int((session_df["is_charging_completed"] == 0).sum()), "Treatment": "Flag preserved; charging_duration_hr set to NaN"},
        {"Flag_Name": "is_registered_user == 0", "Count": int((session_df["is_registered_user"] == 0).sum()), "Treatment": "Flag preserved; user_id_clean set to 'ANONYMOUS'"}
    ])
    t5_path = out_dir / "table5_data_quality_flags_summary.csv"
    t5_df.to_csv(t5_path, index=False)
    paths["table5"] = t5_path
    
    return paths
