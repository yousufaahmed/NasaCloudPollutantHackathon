import math
import requests
import pandas as pd
import numpy as np
import geopandas as gpd
from datetime import datetime, timedelta, timezone
from pathlib import Path

# -----------------------------
# Helper: square bbox in miles
# -----------------------------
def bbox_square_miles(lat, lon, side_miles=50.0):
    half = side_miles / 2.0
    miles_per_deg_lat = 69.0
    miles_per_deg_lon = 69.172 * math.cos(math.radians(lat))
    dlat = half / miles_per_deg_lat
    dlon = half / miles_per_deg_lon
    return (lon - dlon, lat - dlat + 2, lon + dlon + 2, lat + dlat)

# -----------------------------
# Config
# -----------------------------
URL = "https://www.airnowapi.org/aq/data/"
API_KEY = "530E92B3-B8C7-44A9-9726-D27E66CF0AE8"
POLLUTANTS = ["NO2","OZONE","CO","SO2","PM25","PM10"]

# Get current time and calculate the most recent completed full hour window
now = datetime.now(timezone.utc)
current_hour = now.replace(minute=0, second=0, microsecond=0)

# If we're past the hour mark, use the current hour as end time
# Otherwise, use the previous hour
if now.minute == 0 and now.second < 5:  # Account for edge cases
    end_dt = current_hour - timedelta(hours=1)
else:
    end_dt = current_hour

start_dt = end_dt - timedelta(hours=1)

start_str = start_dt.strftime("%Y-%m-%dT%H")
end_str   = end_dt.strftime("%Y-%m-%dT%H")

print(f"⏰ Fetching data for: {start_str} to {end_str} (1-hour window)")

DATA_TYPE = "B"
user_lat, user_lon = 36.7783, -119.4179

def fetch_pollutant(p, bbox_str):
    params = {
        "BBOX": bbox_str,
        "dataType": DATA_TYPE,
        "format": "application/json",
        "API_KEY": API_KEY,
        "parameters": p,
        "startDate": start_str,
        "endDate": end_str,
    }
    r = requests.get(URL, params=params, timeout=30)
    if r.status_code != 200:
        print(f"[{p}] HTTP {r.status_code}")
        return pd.DataFrame()
    try:
        data = r.json()
    except Exception as e:
        print(f"[{p}] JSON error: {e}")
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)

    # Normalize time
    if "UTC" in df.columns:
        df["UTC"] = pd.to_datetime(df["UTC"], utc=True, errors="coerce")
    elif {"DateObserved","HourObserved"}.issubset(df.columns):
        df["UTC"] = pd.to_datetime(
            df["DateObserved"].astype(str) + " " + df["HourObserved"].astype(str) + ":00",
            utc=True, errors="coerce"
        )
    else:
        df["UTC"] = pd.NaT

    keep = [c for c in ["UTC","Parameter","Unit","Value","AQI","Latitude","Longitude"] if c in df.columns]
    df = df[keep]
    df["Parameter"] = p
    
    # Filter to time window
    df = df[(df["UTC"] >= pd.to_datetime(start_str).tz_localize("UTC")) &
            (df["UTC"] <= pd.to_datetime(end_str).tz_localize("UTC"))]
    return df

# -----------------------------------------
# Fetch data
# -----------------------------------------
all_frames = []
for side_miles in [25.0,]:
    lon_min, lat_min, lon_max, lat_max = bbox_square_miles(user_lat, user_lon, side_miles)
    bbox_str = f"{lon_min:.6f},{lat_min:.6f},{lon_max:.6f},{lat_max:.6f}"
    print(f"🔎 Trying box {side_miles} mi → {bbox_str}")

    frames = [fetch_pollutant(p, bbox_str) for p in POLLUTANTS]
    raw = pd.concat([f for f in frames if not f.empty], ignore_index=True) if any(len(f) for f in frames) else pd.DataFrame()

    if not raw.empty:
        print(f"✅ Got {len(raw)} rows")
        all_frames = [raw]
        break

# Fallback: CONUS
if not all_frames:
    print("⚠️ Falling back to CONUS bbox")
    CONUS = "-130.964794,13.151361,-62.410107,50.455533"
    frames = [fetch_pollutant(p, CONUS) for p in POLLUTANTS]
    raw = pd.concat([f for f in frames if not f.empty], ignore_index=True) if any(len(f) for f in frames) else pd.DataFrame()
    if raw.empty:
        raise SystemExit("❌ No data returned")
else:
    raw = all_frames[0]

# -----------------------------------------
# GeoPandas state mapping (accurate spatial join)
# -----------------------------------------
print("🗺️ Loading US states shapefile...")
STATES_URL = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip"
us_states = gpd.read_file(STATES_URL).to_crs(epsg=4326)
us_states = us_states[~us_states['STUSPS'].isin(['PR','GU','VI','AS','MP'])]  # exclude territories

print("🗺️ Performing spatial join...")
# Convert lat/lon → geometry
gdf = gpd.GeoDataFrame(raw, geometry=gpd.points_from_xy(raw.Longitude, raw.Latitude), crs="EPSG:4326")

# Spatial join → get state names
joined = gpd.sjoin(gdf, us_states[['NAME','geometry']], how='left', predicate='within')
raw["State"] = joined["NAME"]
raw = raw.dropna(subset=["State"]).copy()

# -----------------------------------------
# Unit normalization & pivot
# -----------------------------------------
def to_ppm(value, unit):
    if pd.isna(value) or unit is None:
        return np.nan
    u = str(unit).upper()
    if u == "PPM": return value
    if u == "PPB": return value / 1000.0
    return np.nan

def canonical_value_row(row):
    p = str(row["Parameter"]).upper()
    val, unit = row.get("Value", np.nan), row.get("Unit", None)
    if p in ["NO2","OZONE","CO","SO2"]:
        return to_ppm(val, unit)
    elif p in ["PM25","PM10"]:
        return val
    return np.nan

if "AQI" not in raw.columns:
    raw["AQI"] = np.nan

for col in ["State","UTC","Parameter","Value","Unit","AQI"]:
    if col not in raw.columns:
        raw[col] = np.nan

raw["Parameter"] = raw["Parameter"].str.upper()
raw["canon_value"] = raw.apply(canonical_value_row, axis=1)

# Pivot
value_pivot = raw.pivot_table(
    index=["State","UTC"], columns="Parameter", values="canon_value", aggfunc="mean"
)
aqi_pivot = raw.pivot_table(
    index=["State","UTC"], columns="Parameter", values="AQI", aggfunc="max"
)

value_pivot.columns = [str(c).upper() for c in value_pivot.columns]
aqi_pivot.columns   = [f"AQI_{str(c).upper()}" for c in aqi_pivot.columns]

wide = pd.concat([value_pivot, aqi_pivot], axis=1).reset_index()

# Overall AQI
aqi_cols = [c for c in wide.columns if c.startswith("AQI_")]
wide["AQI"] = wide[aqi_cols].max(axis=1, skipna=True)

# Ensure columns exist
for col in ["NO2","OZONE","CO","SO2","PM25","PM10"]:
    if col not in wide.columns:
        wide[col] = np.nan

df_user = (wide[["State","UTC","NO2","OZONE","CO","SO2","PM25","PM10","AQI"]]
           .rename(columns={
               "NO2":"NO2_ppm","OZONE":"OZONE_ppm","CO":"CO_ppm","SO2":"SO2_ppm",
               "PM25":"PM25_ugm3","PM10":"PM10_ugm3"
           })
           .sort_values(["State","UTC"])
           .reset_index(drop=True))

print(df_user)
print(f"✅ Built table with shape {df_user.shape}")

# -----------------------------------------
# Save output
# -----------------------------------------
df_user["UTC"] = pd.to_datetime(df_user["UTC"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M")

OUT_DIR = Path(r"C:\Users\yousu\Documents\Coding\NASA HACKATHON\data_test\user_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
out_file = OUT_DIR / f"user_airnow_{timestamp}.xlsx"

df_user.to_excel(out_file, index=False)
print(f"💾 Saved → {out_file}")