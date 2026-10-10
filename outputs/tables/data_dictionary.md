# Data Dictionary: Processed EV Charging Datasets

**Project:** Data-Driven Analytics for EV Charging Demand Forecasting and Anomaly Detection in Smart Grids  
**Dataset Source:** Caltech ACN-Data (5,000 Charging Sessions)  
**Timezone:** Original stored in UTC; Local analysis in `America/Los_Angeles` (PST/PDT)

---

## 1. Session-Level Dataset (`data/processed/cleaned_sessions.csv`)

| Variable Name | Data Type | Units / Range | Description & Derivation | Missing Values Handling |
| :--- | :--- | :--- | :--- | :--- |
| `_id` | String | MongoDB ObjectId | Unique record identifier from raw ACN database. | 0 missing (100% complete) |
| `sessionID` | String | ACN unique session string | Unique session identifier `{site}_{cluster}_{station}_{space}_{timestamp}`. | 0 missing (100% complete) |
| `stationID` | String | 54 unique categories | Identifier for EVSE charging station hardware. | 0 missing (100% complete) |
| `spaceID` | String | 54 unique categories | Identifier for physical parking stall (1:1 mapped to stationID). | 0 missing (100% complete) |
| `siteID` | String | `"0002"` | Site identifier (Caltech Campus). | 0 missing (100% complete) |
| `clusterID` | String | `"0039"` | Station cluster identifier within Caltech garage. | 0 missing (100% complete) |
| `userID` | String / Null | 9-digit padded string | Raw user ID string (null for unregistered drivers). | 590 missing |
| `user_id_clean` | String | String / `"ANONYMOUS"` | Clean user identifier; nulls explicitly replaced with `"ANONYMOUS"`. | 0 missing |
| `is_registered_user` | Integer | `0` or `1` | Binary flag: `1` if user authenticated via app; `0` if guest session. | 0 missing |
| `connectionTime_raw` | String | RFC 2822 (GMT) | Original raw connection timestamp string. | 0 missing |
| `disconnectTime_raw` | String | RFC 2822 (GMT) | Original raw disconnect timestamp string. | 0 missing |
| `doneChargingTime_raw`| String / Null | RFC 2822 (GMT) | Original raw power completion timestamp string. | 1,573 missing |
| `connectionTime_utc` | Datetime | UTC Timestamp | Standardized UTC connection datetime. | 0 missing |
| `disconnectTime_utc` | Datetime | UTC Timestamp | Standardized UTC disconnection datetime. | 0 missing |
| `doneChargingTime_utc`| Datetime / Null| UTC Timestamp | Standardized UTC charge-completion datetime. | 1,573 missing |
| `connectionTime_local`| Datetime | PST/PDT Timestamp | Connection datetime in `America/Los_Angeles`. | 0 missing |
| `disconnectTime_local`| Datetime | PST/PDT Timestamp | Disconnection datetime in `America/Los_Angeles`. | 0 missing |
| `doneChargingTime_local`| Datetime / Null| PST/PDT Timestamp | Completion datetime in `America/Los_Angeles`. | 1,573 missing |
| `kWhDelivered` | Float | 0.501 to 77.70 kWh | Total electrical energy delivered during the session. | 0 missing |
| `kWhRequested` | Float / NaN | 0.0 to 215.32 kWh | Energy requested by driver in ACN app (final submission). | 590 missing (NaN) |
| `milesRequested` | Float / NaN | 0 to 775 miles | Driver-requested vehicle range. | 590 missing (NaN) |
| `WhPerMile` | Float / NaN | 200 to 2000 Wh/mi | Rated vehicle energy consumption efficiency. | 590 missing (NaN) |
| `minutesAvailable` | Float / NaN | 21 to 1448 min | Estimated parking duration declared by user upon arrival. | 590 missing (NaN) |
| `has_user_inputs` | Integer | `0` or `1` | Binary flag: `1` if session contains app inputs; `0` if empty. | 0 missing |
| `user_inputs_count` | Integer | 0 to 10 | Count of driver preference submissions/amendments during session. | 0 missing |
| `paymentRequired` | Boolean / NaN| `True` | Payment transaction requirement. | 590 missing |
| `connection_duration_min`| Float | 2.07 to 4988.3 min | Total parked duration: `(disconnect - connection)` in minutes. | 0 missing |
| `connection_duration_hr` | Float | 0.034 to 83.14 hr | Total parked duration in hours. | 0 missing |
| `is_charging_completed` | Integer | `0` or `1` | Binary flag: `1` if doneChargingTime recorded; `0` if unrecorded. | 0 missing |
| `charging_duration_min` | Float / NaN | 0.0 to 2569.5 min | Power draw duration: `(doneCharging - connection)` in minutes. | 1,573 missing (NaN) |
| `charging_duration_hr` | Float / NaN | 0.0 to 42.83 hr | Power draw duration in hours. | 1,573 missing (NaN) |
| `negative_charging_duration_flag`| Integer | `0` or `1` | Flag: `1` if sensor recorded doneCharging < connection (floored to 0.0). | 0 missing (1 occurrence) |
| `done_after_disconnect_flag`| Integer | `0` or `1` | Flag: `1` if doneCharging recorded after disconnect event. | 0 missing (76 occurrences) |
| `done_after_disconnect_excess_min`| Float | 0.0 to 59.87 min | Excess minutes between doneCharging and disconnect. | 0 missing |
| `idle_duration_min` | Float / NaN | 0.0 to 4978.7 min | Stall occupancy without active power draw (`conn - charge`). | 1,573 missing (NaN) |
| `idle_duration_hr` | Float / NaN | 0.0 to 82.98 hr | Idle connection duration in hours (smart grid flexibility indicator). | 1,573 missing (NaN) |
| `idle_to_connection_ratio`| Float / NaN | 0.0 to 1.0 | Ratio of idle duration to total connection duration. | 1,573 missing (NaN) |
| `energy_error_kwh` | Float / NaN | -53.48 to 198.8 kWh| Discrepancy between requested and delivered (`requested - delivered`). | 590 missing (NaN) |
| `delivery_ratio` | Float / NaN | 0.005 to 10.42 | Ratio of delivered energy to requested energy. | 591 missing (NaN) |
| `over_delivery_flag` | Integer | `0` or `1` | Flag: `1` if delivered energy exceeded requested energy. | 0 missing (294 occurrences) |
| `average_charging_rate_kw`| Float | 0.07 to 37.6 kW | Effective average charging power rate during session. | 0 missing |
| `conn_hour` | Integer | 0 to 23 | Local arrival hour (0 = midnight, 23 = 11 PM). | 0 missing |
| `conn_minute` | Integer | 0 to 59 | Local arrival minute. | 0 missing |
| `conn_dayofweek` | Integer | 0 to 6 | Local day of week (0 = Monday, 6 = Sunday). | 0 missing |
| `conn_day_name` | String | Monday to Sunday | English day of week name. | 0 missing |
| `is_weekend` | Integer | `0` or `1` | Binary flag: `1` if Saturday or Sunday; `0` otherwise. | 0 missing |
| `conn_month` | Integer | 1 to 12 | Month of arrival. | 0 missing |
| `conn_year` | Integer | 2020 or 2021 | Year of arrival. | 0 missing |
| `conn_date` | String | YYYY-MM-DD | Local connection calendar date. | 0 missing |
| `disc_hour` | Integer | 0 to 23 | Local departure hour. | 0 missing |
| `sin_conn_hour` | Float | -1.0 to 1.0 | Cyclical sine transformation of arrival hour. | 0 missing |
| `cos_conn_hour` | Float | -1.0 to 1.0 | Cyclical cosine transformation of arrival hour. | 0 missing |
| `sin_dayofweek` | Float | -1.0 to 1.0 | Cyclical sine transformation of day of week. | 0 missing |
| `cos_dayofweek` | Float | -1.0 to 1.0 | Cyclical cosine transformation of day of week. | 0 missing |
| `covid_period` | String | 3 categories | `"Pre-Lockdown"`, `"Lockdown"`, or `"Post-Lockdown-Recovery"`. | 0 missing |
| `is_covid_lockdown` | Integer | `0` or `1` | Binary flag: `1` if arrival occurred during lockdown period. | 0 missing |

---

## 2. Hourly Demand Dataset (`data/processed/hourly_demand.csv`)

| Variable Name | Data Type | Units / Range | Description & Derivation | Missing Values Handling |
| :--- | :--- | :--- | :--- | :--- |
| `timestamp` | Datetime | Continuous hourly | Timestamp floor in `America/Los_Angeles` (e.g. `2020-01-21 20:00:00-08:00`). | 0 missing (continuous grid) |
| `total_kwh_delivered` | Float | 0.0 to 226.7 kWh | Sum of EV energy delivered across all sessions connecting in this hour. | Zero-filled for inactive hours |
| `session_count` | Integer | 0 to 18 sessions | Count of EV sessions initiated in this hour. | Zero-filled for inactive hours |
| `avg_kwh_per_session` | Float | 0.0 to 60.5 kWh | Mean energy delivered per session in this hour. | Zero-filled for inactive hours |
| `max_kwh_session` | Float | 0.0 to 77.7 kWh | Maximum single-session energy delivered in this hour. | Zero-filled for inactive hours |
| `avg_connection_duration_hr` | Float | 0.0 to 38.5 hr | Mean parked duration for sessions connecting in this hour. | Zero-filled for inactive hours |
| `hour` | Integer | 0 to 23 | Hour of day (0 to 23). | 0 missing |
| `dayofweek` | Integer | 0 to 6 | Day of week (0 = Monday, 6 = Sunday). | 0 missing |
| `is_weekend` | Integer | `0` or `1` | Binary indicator for weekend hours. | 0 missing |
| `month` | Integer | 1 to 12 | Month of year. | 0 missing |
| `year` | Integer | 2020 or 2021 | Year. | 0 missing |
| `date` | String | YYYY-MM-DD | Calendar date string. | 0 missing |
| `sin_hour` / `cos_hour` | Float | -1.0 to 1.0 | Cyclical representations of hour of day. | 0 missing |
| `sin_dow` / `cos_dow` | Float | -1.0 to 1.0 | Cyclical representations of day of week. | 0 missing |
| `sin_month` / `cos_month` | Float | -1.0 to 1.0 | Cyclical representations of month of year. | 0 missing |
| `is_peak_hour_window` | Integer | `0` or `1` | Flag: `1` if weekday morning/midday window (08:00 - 13:00). | 0 missing |
| `is_system_peak_demand_hour` | Integer | `0` or `1` | Flag: `1` if total_kwh_delivered >= 95th percentile of active hours. | 0 missing |
| `is_covid_lockdown` | Integer | `0` or `1` | Flag: `1` if timestamp falls in Mar 19, 2020 – Oct 31, 2020. | 0 missing |
| `covid_period` | String | 3 categories | COVID restriction regime categorization. | 0 missing |
| `lag_1` | Float | Lagged kWh | Target energy demand at $t-1$ hour. | NaN for first hour |
| `lag_2` | Float | Lagged kWh | Target energy demand at $t-2$ hours. | NaN for first 2 hours |
| `lag_3` | Float | Lagged kWh | Target energy demand at $t-3$ hours. | NaN for first 3 hours |
| `lag_24` | Float | Lagged kWh | Target energy demand at $t-24$ hours (same hour yesterday). | NaN for first 24 hours |
| `lag_48` | Float | Lagged kWh | Target energy demand at $t-48$ hours. | NaN for first 48 hours |
| `lag_168` | Float | Lagged kWh | Target energy demand at $t-168$ hours (same hour last week). | NaN for first 168 hours |
| `rolling_mean_24` | Float | Rolling mean kWh | 24-hour rolling mean demand (strictly shifted by 1 hour). | 0 missing (min_periods=1) |
| `rolling_std_24` | Float | Rolling std kWh | 24-hour rolling demand standard deviation (shifted by 1 hour). | 0 missing |
| `rolling_mean_168` | Float | Rolling mean kWh | 168-hour (7-day) rolling mean demand (shifted by 1 hour). | 0 missing (min_periods=1) |
| `lag_count_1` | Float | Lagged count | Active session count at $t-1$ hour. | NaN for first hour |
| `lag_count_24` | Float | Lagged count | Active session count at $t-24$ hours. | NaN for first 24 hours |
