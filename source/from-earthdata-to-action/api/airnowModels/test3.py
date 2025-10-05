import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import math

URL = "https://www.airnowapi.org/aq/data/"
API_KEY = "530E92B3-B8C7-44A9-9726-D27E66CF0AE8"

# Bounding box for the continental US
BBOX = "-130.964794,13.151361,-62.410107,50.455533"


def bbox_square_miles(lat, lon, side_miles=5.0):
    half = side_miles / 2.0
    miles_per_deg_lat = 69.0
    miles_per_deg_lon = 69.172 * math.cos(math.radians(lat))  # 69–69.4 at mid-latitudes

    dlat = half / miles_per_deg_lat
    dlon = half / miles_per_deg_lon

    min_lat = lat - dlat
    max_lat = lat + dlat
    min_lon = lon - dlon
    max_lon = lon + dlon

    # clamp to valid ranges
    min_lat = max(min_lat, -90.0)
    max_lat = min(max_lat,  90.0)
    min_lon = (min_lon + 180) % 360 - 180
    max_lon = (max_lon + 180) % 360 - 180

    return min_lon, min_lat, max_lon, max_lat  # (lon_min, lat_min, lon_max, lat_max)

UserBBOX = bbox_square_miles(39.8283, -98.5795, side_miles=5.0)  # center of continental US
print("User bounding box:", UserBBOX)

# List of pollutants to fetch
POLLUTANTS = ['PM25','OZONE']

# Base params shared between all queries
PARAMS_BASE = {
    "BBOX": BBOX,
    "dataType": "B",  # 'C' = hourly/continuous, 'A' = aggregated daily
    "format": "application/json",
    "API_KEY": API_KEY
}

# Date range (inclusive)
end_day = datetime(2025, 10, 4, 23, 59)
start_day = datetime(2025, 9, 17, 0, 0)

# Output directory
BASE_DIR = r"C:\Users\yousu\Documents\Coding\NASA HACKATHON\data_test"

# Loop through pollutants
for pollutant in POLLUTANTS:
    pollutant_dir = os.path.join(BASE_DIR, f"airnow_{pollutant}_new")
    os.makedirs(pollutant_dir, exist_ok=True)

    print(f"\n==============================")
    print(f"🌫️  Fetching 12-hour data for: {pollutant}")
    print(f"==============================")

    d = end_day
    while d >= start_day:
        # Define 12-hour window
        half_day_start = d - timedelta(hours=12)
        start_str = half_day_start.strftime("%Y-%m-%dT%H")
        end_str = d.strftime("%Y-%m-%dT%H")

        params = PARAMS_BASE | {
            "parameters": pollutant,
            "startDate": start_str,
            "endDate": end_str
        }

        print(f"Fetching {pollutant}: {start_str} → {end_str}")
        try:
            r = requests.get(URL, params=params, timeout=60)
            if r.status_code != 200:
                print(f"  ⚠️ HTTP {r.status_code}: {r.text[:200]}")
                d -= timedelta(hours=12)
                time.sleep(1)
                continue

            data = r.json()
            if not data:
                print("  No data returned for this 12-hour window.")
                d -= timedelta(hours=12)
                time.sleep(0.2)
                continue

            df = pd.DataFrame(data)

            # Save all columns
            filename = os.path.join(
                pollutant_dir,
                f"airnow_{pollutant}_{half_day_start.strftime('%Y-%m-%d_%H')}-{d.strftime('%H')}.xlsx"
            )
            df.to_excel(filename, index=False)
            print(f"  ✅ Saved {len(df):,} rows → {filename}")

            time.sleep(0.3)  # small delay for rate limiting

        except Exception as e:
            print(f"  ⚠️ Error fetching {pollutant}: {e}")

        # Move to previous 12-hour window
        d -= timedelta(hours=12)

print("\n🎉 Done! All pollutants processed in 12-hour intervals.")
