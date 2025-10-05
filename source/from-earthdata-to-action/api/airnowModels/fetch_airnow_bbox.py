import os
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd
from pathlib import Path

from bbox_utils import bbox_from_center_miles, bbox_to_string


URL = "https://www.airnowapi.org/aq/data/"
API_KEY = "530E92B3-B8C7-44A9-9726-D27E66CF0AE8"
POLLUTANTS = ["NO2","OZONE","CO","SO2","PM25","PM10"]


def get_two_hour_window_utc():
    now = datetime.now(timezone.utc)
    # Use the most recently COMPLETED hour to avoid partial-hour gaps
    end_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    start_hour = end_hour - timedelta(hours=1)
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

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = out_dir / f"airnow_bbox_{timestamp}.xlsx"
    # Format UTC for Excel readability
    if "UTC" in df.columns:
        df["UTC"] = pd.to_datetime(df["UTC"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M")
    df.to_excel(out_path, index=False)
    return out_path


if __name__ == "__main__":
    # Example: pass coordinates via environment or edit here
    lat = float(os.environ.get("AIRNOW_LAT", "36.7783"))
    lon = float(os.environ.get("AIRNOW_LON", "-119.4179"))
    path = fetch_and_save(lat, lon, 10.0)
    print(f"Saved to {path}")


