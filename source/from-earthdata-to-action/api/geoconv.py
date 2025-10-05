import os
import glob
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# --- CONFIG ---
DATA_DIR = r"C:\Users\yousu\Documents\Coding\NASA HACKATHON\data_test\airnow_NO2"
PATTERN = os.path.join(DATA_DIR, "airnow_*.xlsx")

# --- Load US States polygon data ---
# Natural Earth dataset included with GeoPandas (contains US states as polygons)
world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
us = world[world["iso_a2"] == "US"].copy()

# Some GeoPandas datasets have "United States of America" as one shape.
# For state-level detail, we use a public Census TIGER shapefile instead:
try:
    us_states = gpd.read_file("https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip")
    us_states = us_states.to_crs(epsg=4326)
except Exception:
    print("⚠️ Could not load Census shapefile, fallback to country-level US shape.")
    us_states = us  # fallback

files = glob.glob(PATTERN)
print(f"Found {len(files)} Excel files.\n")

for file_path in files:
    print(f"Processing: {os.path.basename(file_path)}")

    df = pd.read_excel(file_path)
    if "Latitude" not in df.columns or "Longitude" not in df.columns:
        print("  ⚠️ No Latitude/Longitude columns found — skipped.")
        continue

    # Create GeoDataFrame from AirNow points
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326"
    )

    # Perform spatial join (each point gets matched to a state polygon)
    joined = gpd.sjoin(gdf, us_states, how="left", predicate="within")

    # Use 'NAME' or 'STUSPS' depending on shapefile fields
    if "STUSPS" in joined.columns:
        df["State"] = joined["STUSPS"]
    elif "NAME" in joined.columns:
        df["State"] = joined["NAME"]
    else:
        df["State"] = None

    # Optionally drop lat/lon (comment this line if you want to keep them)
    df = df.drop(columns=["Latitude", "Longitude"], errors="ignore")

    # Save result
    out_path = file_path.replace(".xlsx", "_state.xlsx")
    df.to_excel(out_path, index=False)
    print(f"  ✅ Saved {len(df)} rows → {os.path.basename(out_path)}")

print("\n🎉 Done! All files processed with accurate US state detection.")
