import os
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point

from bbox_utils import bbox_from_center_miles, bbox_to_string


URL = "https://www.airnowapi.org/aq/data/"
API_KEY = "530E92B3-B8C7-44A9-9726-D27E66CF0AE8"
POLLUTANTS = ["NO2","OZONE","CO","SO2","PM25","PM10"]


def get_two_hour_window_utc():
    now = datetime.now(timezone.utc)
    # Use the most recently COMPLETED hour to avoid partial-hour gaps
    end_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    # Expand window to last 2 days (48 hours)
    start_hour = end_hour - timedelta(hours=24)
    return start_hour, end_hour


def fetch_pollutant(pollutant: str, bbox_str: str, start_hour: datetime, end_hour: datetime) -> pd.DataFrame:
    params = {
        "BBOX": bbox_str,
        "dataType": "B",
        "format": "application/json",
        "API_KEY": API_KEY,
        "parameters": pollutant,
        "startDate": start_hour.strftime("%Y-%m-%dT%H"),
        "endDate": end_hour.strftime("%Y-%m-%dT%H"),
    }
    r = requests.get(URL, params=params, timeout=30)
    if r.status_code != 200:
        return pd.DataFrame()
    try:
        data = r.json()
    except Exception:
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if not len(df):
        return pd.DataFrame()

    # Normalize time if provided
    if "UTC" in df.columns:
        df["UTC"] = pd.to_datetime(df["UTC"], utc=True, errors="coerce")
    elif {"DateObserved","HourObserved"}.issubset(df.columns):
        df["UTC"] = pd.to_datetime(
            df["DateObserved"].astype(str) + " " + df["HourObserved"].astype(str) + ":00",
            utc=True, errors="coerce"
        )
    else:
        df["UTC"] = pd.NaT

    # Keep only the needed columns
    keep_cols = [c for c in ["UTC","Value","AQI"] if c in df.columns]
    df = df[keep_cols]
    # Filter to the requested 2-hour window explicitly
    df = df[(df["UTC"] >= start_hour) & (df["UTC"] <= end_hour)]
    # Aggregate duplicates per hour: mean Value, max AQI
    if "UTC" in df.columns and len(df):
        df = (df
              .groupby("UTC", as_index=False)
              .agg({"Value": "mean", "AQI": "max"}))
    # Rename to pollutant-specific columns
    df.rename(columns={"Value": f"Value_{pollutant}", "AQI": f"AQI_{pollutant}"}, inplace=True)
    return df


def _merge_frames_on_utc(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    df = frames[0]
    for f in frames[1:]:
        df = pd.merge(df, f, on="UTC", how="outer")
    if "UTC" in df.columns:
        df.sort_values("UTC", inplace=True)
    # Ensure all expected columns exist
    for p in POLLUTANTS:
        aqi_col = f"AQI_{p}"
        val_col = f"Value_{p}"
        if aqi_col not in df.columns:
            df[aqi_col] = pd.NA
        if val_col not in df.columns:
            df[val_col] = pd.NA
    # Reorder columns: UTC, then all Value_*, then all AQI_*
    value_cols = [f"Value_{p}" for p in POLLUTANTS]
    aqi_cols = [f"AQI_{p}" for p in POLLUTANTS]
    cols = (["UTC"] if "UTC" in df.columns else []) + value_cols + aqi_cols
    existing_cols = [c for c in cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in existing_cols]
    return df[existing_cols + other_cols]


def fetch_and_save(lat: float, lon: float, miles_to_edge: float = 10.0, out_dir: str | Path | None = None) -> Path:
    start_hour, end_hour = get_two_hour_window_utc()

    # Try 10-mile box; if empty, try a larger 25-mile box similar to currentData fallback
    candidate_miles = [miles_to_edge, 25.0]
    df = pd.DataFrame()
    for miles in candidate_miles:
        bbox = bbox_from_center_miles(lat, lon, miles)
        bbox_str = bbox_to_string(bbox)

        frames = []
        for p in POLLUTANTS:
            f = fetch_pollutant(p, bbox_str, start_hour, end_hour)
            if not f.empty:
                frames.append(f)
        df = _merge_frames_on_utc(frames)
        if len(df):
            break

    # If still empty, fallback to CONUS bbox
    if not len(df):
        conus_bbox = "-130.964794,13.151361,-62.410107,50.455533"
        frames = []
        for p in POLLUTANTS:
            f = fetch_pollutant(p, conus_bbox, start_hour, end_hour)
            if not f.empty:
                frames.append(f)
        df = _merge_frames_on_utc(frames)

    if out_dir is None:
        out_dir = Path(__file__).resolve().parent / "user_output"
    else:
        out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create overall AQI as row-wise max across AQI_{pollutant}, then drop individual AQI columns
    aqi_cols = [c for c in df.columns if c.startswith("AQI_")]
    if aqi_cols:
        df["AQI"] = df[aqi_cols].max(axis=1, skipna=True)
        df.drop(columns=aqi_cols, inplace=True)

    # Ensure UTC uniqueness (dedupe) and sort
    if "UTC" in df.columns:
        df = df.drop_duplicates(subset=["UTC"]).sort_values("UTC")

    # Add State column based on the center coordinate
    try:
        states_url = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip"
        us_states = gpd.read_file(states_url).to_crs(epsg=4326)
        us_states = us_states[~us_states['STUSPS'].isin(['PR','GU','VI','AS','MP'])]
        pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
        match = gpd.sjoin(gpd.GeoDataFrame(geometry=pt), us_states[['NAME','geometry']], how='left', predicate='within')
        state_name = match['NAME'].iloc[0] if len(match) else None
        if state_name is None or pd.isna(state_name):
            state_name = "Unknown"
        df["State"] = state_name
    except Exception:
        df["State"] = "Unknown"

    # Feature engineering similar to notebook examples
    # Ensure UTC is datetime for feature engineering
    if "UTC" in df.columns:
        df["UTC"] = pd.to_datetime(df["UTC"], utc=True, errors="coerce")

    # Derive calendar features
    if "UTC" in df.columns:
        df["Year"] = df["UTC"].dt.year
        df["Month"] = df["UTC"].dt.month
        df["Day"] = df["UTC"].dt.day
        df["Hour"] = df["UTC"].dt.hour

    # Prepare lag/rolling features per State
    target_cols = ["AQI", "Value_NO2", "Value_CO", "Value_OZONE", "Value_SO2"]
    lags = [6, 24]
    rolls = [3, 6, 12, 24]

    def add_lag_features(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values(["UTC"]).copy()
        for col in target_cols:
            if col not in group.columns:
                continue
            if col == "AQI":
                group[f"{col}_lag6"] = group[col].shift(6)
            else:
                for lag in lags:
                    group[f"{col}_lag{lag}"] = group[col].shift(lag)
                for win in rolls:
                    # Use min_periods=1 so values exist even if < win points available
                    group[f"{col}_rollmean{win}"] = group[col].rolling(win, min_periods=1).mean()
                    group[f"{col}_rollstd{win}"] = group[col].rolling(win, min_periods=1).std()
        return group

    if "State" in df.columns and "UTC" in df.columns:
        df_feat = df.sort_values(["State", "UTC"]).groupby("State", group_keys=False).apply(add_lag_features, include_groups=False)
        if "UTC" in df_feat.columns:
            df_feat = df_feat[~df_feat["UTC"].isna()].reset_index(drop=True)
    else:
        # Fallback: no state available, compute globally
        df_feat = add_lag_features(df)
        if "UTC" in df_feat.columns:
            df_feat = df_feat[~df_feat["UTC"].isna()].reset_index(drop=True)

    # Fill NaNs with medians (after State is added and features generated)
    if "State" in df_feat.columns:
        df_feat["State"] = df_feat["State"].fillna("Unknown").astype(str)
    # Compute median per numeric column and fill
    numeric_cols = df_feat.select_dtypes(include=["number"]).columns
    if len(numeric_cols):
        for c in numeric_cols:
            med = df_feat[c].median(skipna=True)
            df_feat[c] = df_feat[c].fillna(med)

    # Output path (transformed)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = out_dir / f"airnow_bbox_features_{timestamp}.xlsx"

    # Keep only the most recent row by UTC
    if "UTC" in df_feat.columns:
        df_out = df_feat.sort_values("UTC").tail(1)
    else:
        df_out = df_feat.tail(1)

    # Format UTC for Excel readability
    if "UTC" in df_out.columns:
        df_out["UTC"] = pd.to_datetime(df_out["UTC"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M")
    df_out.to_excel(out_path, index=False)
    return out_path


if __name__ == "__main__":
    # Example: pass coordinates via environment or edit here
    lat = float(os.environ.get("AIRNOW_LAT", "36.7783"))
    lon = float(os.environ.get("AIRNOW_LON", "-119.4179"))
    path = fetch_and_save(lat, lon, 10.0)
    print(f"Saved to {path}")


