import os
import glob
import pandas as pd

# Folder with your daily files
FOLDER = r"C:\Users\yousu\Documents\Coding\NASA HACKATHON\data_test\airnow_SO2_new"

# Find all matching files
files = sorted(glob.glob(os.path.join(FOLDER, "airnow_SO2_*.xlsx")))
print(f"Found {len(files)} files")

dfs = []
for f in files:
    try:
        df = pd.read_excel(f, engine="openpyxl")
        df["source_file"] = os.path.basename(f)  # keep provenance (optional)
        dfs.append(df)
    except Exception as e:
        print(f"Skipping {f}: {e}")

if not dfs:
    raise SystemExit("No files loaded")

# Concatenate
all_df = pd.concat(dfs, ignore_index=True)

# Drop duplicate rows
all_df = all_df.drop_duplicates()

# Save one final Excel
out_path = os.path.join(FOLDER, "airnow_SO2_final.xlsx")
with pd.ExcelWriter(out_path, engine="openpyxl") as xw:
    all_df.to_excel(xw, index=False, sheet_name="NO2")

print(f"✅ Saved {len(all_df):,} rows → {out_path}")
