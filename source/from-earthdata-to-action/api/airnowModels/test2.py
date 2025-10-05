import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

URL = "https://www.airnowapi.org/aq/data/"
API_KEY = "530E92B3-B8C7-44A9-9726-D27E66CF0AE8"

# Bounding box for continental US
BBOX = "-130.964794,13.151361,-62.410107,50.455533"

# Pollutants to fetch
POLLUTANTS = ['NO2']
# Date range (inclusive)
end_day = datetime(2025, 10, 4)
start_day = datetime(2025, 10, 3)

# Base parameters (shared)
PARAMS_BASE = {
    "BBOX": BBOX,
    "dataType": "B",  # 'C' = hourly/continuous, 'A' = aggregated daily, 'B' = both
    "format": "application/json",
    "API_KEY": API_KEY
}

# Output directory (change if needed)
BASE_DIR = r"C:\Users\yousu\Documents\Coding\NASA HACKATHON\data_test"

for pollutant in POLLUTANTS:
    pollutant_dir = os.path.join(BASE_DIR, f"airnow_{pollutant}_new1")
    os.makedirs(pollutant_dir, exist_ok=True)

    print(f"\n==============================")
    print(f"🌫️  Fetching data for: {pollutant}")
    print(f"==============================")

    d = end_day
    while d >= start_day:
        start_str = d.strftime("%Y-%m-%dT00")
        end_str = d.strftime("%Y-%m-%dT23")

        params = PARAMS_BASE | {
            "parameters": pollutant,
            "startDate": start_str,
            "endDate": end_str,
        }

        print(f"Fetching {pollutant}: {start_str} → {end_str}")
        try:
            r = requests.get(URL, params=params, timeout=60)
            if r.status_code != 200:
                print(f"  ⚠️ HTTP {r.status_code}: {r.text[:150]}")
                d -= timedelta(days=1)
                time.sleep(1)
                continue

            data = r.json()
            if not data:
                print("  No data returned for this day.")
                d -= timedelta(days=1)
                time.sleep(0.2)
                continue

            df = pd.DataFrame(data)

            # Save to pollutant folder
            filename = os.path.join(
                pollutant_dir, f"airnow_{pollutant}_{d.strftime('%Y-%m-%d')}.xlsx"
            )
            df.to_excel(filename, index=False)
            print(f"  ✅ Saved {len(df):,} rows → {filename}")

            time.sleep(0.3)  # be kind to API

        except Exception as e:
            print(f"  ⚠️ Error fetching {pollutant}: {e}")

        d -= timedelta(days=1)

print("\n🎉 Done! All pollutants processed and saved in separate folders.")
