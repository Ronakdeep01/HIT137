import os
import glob
import pandas as pd
import numpy as np
from collections import OrderedDict

# --- Configuration / constants ---
TEMPERATURES_FOLDER = "temperatures"
OUTPUT_SEASON_FILE = "average_temp.txt"
OUTPUT_RANGE_FILE = "largest_temp_range_station.txt"
OUTPUT_STABILITY_FILE = "temperature_stability_stations.txt"


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Map months to Australian seasons
SEASON_MAP = {
    "December": "Summer", "January": "Summer", "February": "Summer",
    "March": "Autumn", "April": "Autumn", "May": "Autumn",
    "June": "Winter", "July": "Winter", "August": "Winter",
    "September": "Spring", "October": "Spring", "November": "Spring"
}


SEASON_ORDER = ["Summer", "Autumn", "Winter", "Spring"]


def find_csv_files(folder):
    """Return list of .csv file paths under folder."""
    pattern = os.path.join(folder, "*.csv")
    return sorted(glob.glob(pattern))


def safe_read_csv(path):
    """
    Read a CSV.
    Return None on failure.
    """
    try:
        df = pd.read_csv(path, sep=None, engine="python")
        return df
    except Exception as e:
        print(f"Warning: failed to read '{path}': {e}")
        return None


def normalize_month_columns(df):
    """
    Ensure month columns exist in the dataframe and convert them to numeric.
    """
    present = []
    col_map = {c.lower(): c for c in df.columns}
    for m in MONTHS:
        key = m.lower()
        if key in col_map:
            colname = col_map[key]
            
            df[colname] = pd.to_numeric(df[colname], errors="coerce")
            # standardize the column name to canonical month name
            if colname != m:
                df = df.rename(columns={colname: m})
            present.append(m)
    return df, present


def gather_all_data(files):
    """
    Read and concatenate all CSV files into one DataFrame.
    Returns (all_df, months_present).
    """
    pieces = []
    months_found = set()

    for f in files:
        df = safe_read_csv(f)
        if df is None:
            continue

       
        cols_lower = {c.lower(): c for c in df.columns}

        if "stn_id" in cols_lower:
            df = df.rename(columns={cols_lower["stn_id"]: "STN_ID"})
        if "station_name" in cols_lower:
            df = df.rename(columns={cols_lower["station_name"]: "STATION_NAME"})
        # Normalize month columns and convert to numeric
        df, present = normalize_month_columns(df)
        months_found.update(present)


        if "STN_ID" not in df.columns and "STATION_NAME" in df.columns:
            df["STN_ID"] = df["STATION_NAME"].astype(str)


        if "STATION_NAME" not in df.columns and "STN_ID" in df.columns:
            df["STATION_NAME"] = df["STN_ID"].astype(str)

        pieces.append(df)

    if not pieces:
        return pd.DataFrame(), []

    all_df = pd.concat(pieces, ignore_index=True, sort=False)

    if "STN_ID" not in all_df.columns:
        all_df["STN_ID"] = all_df.index.astype(str)
    if "STATION_NAME" not in all_df.columns:
        all_df["STATION_NAME"] = all_df["STN_ID"].astype(str)

    # List months present in canonical order
    months_present = [m for m in MONTHS if m in months_found]
    return all_df, months_present


# --- Analysis functions ---


def compute_seasonal_averages(melted_df):
    """
    melted_df must have columns: STN_ID, STATION_NAME, Month, Temp
    Returns OrderedDict season -> mean_temp (float, NaN if no data)
    """
    # Map month -> season
    melted_df = melted_df.copy()
    melted_df["Season"] = melted_df["Month"].map(SEASON_MAP)
    # compute mean across all stations & years, ignoring NaN
    season_means = melted_df.groupby("Season", observed=True)["Temp"].mean()
    # return in the desired order
    result = OrderedDict()
    for s in SEASON_ORDER:
        val = season_means.get(s, np.nan)
        result[s] = float(val) if not pd.isna(val) else np.nan
    return result


def compute_station_stats(melted_df):
    """
    For each station (identified by STN_ID and STATION_NAME) compute:
      - max_temp
      - min_temp
      - range = max - min
      - stddev (population std, ddof=0)
    Stations with no numeric temp values are dropped.
    """
  
    melted_df["Temp"] = pd.to_numeric(melted_df["Temp"], errors="coerce")
    # drop rows where Temp is NaN
    valid = melted_df.dropna(subset=["Temp"]).copy()
    if valid.empty:
        return pd.DataFrame()

    def agg_func(g):
        vals = g["Temp"].values.astype(float)
        return pd.Series({
            "STATION_NAME": g["STATION_NAME"].iloc[0],
            "max_temp": np.nanmax(vals),
            "min_temp": np.nanmin(vals),
            "temp_range": np.nanmax(vals) - np.nanmin(vals),
            "stddev": float(np.std(vals, ddof=0)),
            "count_values": len(vals)
        })

    grouped = valid.groupby("STN_ID", sort=False).apply(agg_func)
    return grouped


def write_season_file(season_avgs, filename):
    """
    Writes seasonal averages in format:
     Summer: 28.5°C
    Order: Summer, Autumn, Winter, Spring
    """
    with open(filename, "w", encoding="utf-8") as f:
        for s in SEASON_ORDER:
            val = season_avgs.get(s, np.nan)
            if pd.isna(val):
                line = f"{s}: No data\n"
            else:
                line = f"{s}: {round(val, 1)}°C\n"
            f.write(line)
    print(f"Wrote seasonal averages to {filename}")


def write_range_file(station_stats_df, filename):
    """
    Writes station(s) with largest range in this format per station:
    Station ABC: Range 45.2°C (Max: 48.3°C, Min: 3.1°C)
    If multiple stations tie, list them all (one per line).
    """
    if station_stats_df.empty:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("No station temperature data available.\n")
        print(f"Wrote largest range results to {filename} (no data).")
        return

    max_range = station_stats_df["temp_range"].max()
    # treat floating point ties exactly (we used the same computation so equality is fine)
    tied = station_stats_df[station_stats_df["temp_range"] == max_range]

    with open(filename, "w", encoding="utf-8") as f:
        for stn_id, row in tied.iterrows():
            name = row["STATION_NAME"]
            rng = round(row["temp_range"], 1)
            mx = round(row["max_temp"], 1)
            mn = round(row["min_temp"], 1)
            f.write(f"Station {name}: Range {rng}°C (Max: {mx}°C, Min: {mn}°C)\n")
    print(f"Wrote largest range results to {filename}")


def write_stability_file(station_stats_df, filename):
    """
    Writes:
    Most Stable: Station XYZ: StdDev 2.3°C
    Most Variable: Station DEF: StdDev 12.8°C
    If ties occur, list all (one per line for each category).
    """
    if station_stats_df.empty:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("No station temperature data available.\n")
        print(f"Wrote stability results to {filename} (no data).")
        return

    min_std = station_stats_df["stddev"].min()
    max_std = station_stats_df["stddev"].max()

    most_stable = station_stats_df[station_stats_df["stddev"] == min_std]
    most_variable = station_stats_df[station_stats_df["stddev"] == max_std]

    with open(filename, "w", encoding="utf-8") as f:
        # Stable
        for stn_id, row in most_stable.iterrows():
            name = row["STATION_NAME"]
            stdv = round(row["stddev"], 1)
            f.write(f"Most Stable: Station {name}: StdDev {stdv}°C\n")
        # Variable
        for stn_id, row in most_variable.iterrows():
            name = row["STATION_NAME"]
            stdv = round(row["stddev"], 1)
            f.write(f"Most Variable: Station {name}: StdDev {stdv}°C\n")
    print(f"Wrote stability results to {filename}")





def main():

    files = find_csv_files(TEMPERATURES_FOLDER)
    if not files:
        print(f"No CSV files found in folder '{TEMPERATURES_FOLDER}'. Exiting.")
        return

    print(f"Found {len(files)} CSV file(s). Reading and processing...")

    all_df, months_present = gather_all_data(files)
    if all_df.empty or not months_present:
        print("No temperature columns found in the input files. Exiting.")
        return

    # Prepare melted long-form dataframe: one row per station-month reading
    value_vars = months_present
    melted = pd.melt(
        all_df,
        id_vars=["STN_ID", "STATION_NAME"],
        value_vars=value_vars,
        var_name="Month",
        value_name="Temp"
    )

    # Seasonal averages across all stations & years
    season_avgs = compute_seasonal_averages(melted)
    write_season_file(season_avgs, OUTPUT_SEASON_FILE)

    # Station-level stats
    station_stats = compute_station_stats(melted)
    if station_stats.empty:
        print("No valid temperature values found for any station.")
        
        with open(OUTPUT_RANGE_FILE, "w", encoding="utf-8") as f:
            f.write("No station temperature data available.\n")
        with open(OUTPUT_STABILITY_FILE, "w", encoding="utf-8") as f:
            f.write("No station temperature data available.\n")
        return

    # Temperature range
    write_range_file(station_stats, OUTPUT_RANGE_FILE)

    # Temperature stability
    write_stability_file(station_stats, OUTPUT_STABILITY_FILE)

    # Also print a short summary to stdout
    print("\nSummary (console):")
    print("Seasonal averages:")
    for s, v in season_avgs.items():
        if pd.isna(v):
            print(f"  {s}: No data")
        else:
            print(f"  {s}: {round(v,1)}°C")
    top_range = station_stats["temp_range"].max()
    top_range_stations = station_stats[station_stats["temp_range"] == top_range]
    print("\nStation(s) with largest range:")
    for idx, r in top_range_stations.iterrows():
        print(f"  {r['STATION_NAME']} : Range {round(r['temp_range'],1)}°C (Max {round(r['max_temp'],1)}°C, Min {round(r['min_temp'],1)}°C)")

    min_std = station_stats["stddev"].min()
    max_std = station_stats["stddev"].max()
    print("\nMost stable station(s):")
    for idx, r in station_stats[station_stats["stddev"] == min_std].iterrows():
        print(f"  {r['STATION_NAME']}: StdDev {round(r['stddev'],1)}°C")
    print("\nMost variable station(s):")
    for idx, r in station_stats[station_stats["stddev"] == max_std].iterrows():
        print(f"  {r['STATION_NAME']}: StdDev {round(r['stddev'],1)}°C")

    print("\nAll output files written:")
    print(f" - {OUTPUT_SEASON_FILE}")
    print(f" - {OUTPUT_RANGE_FILE}")
    print(f" - {OUTPUT_STABILITY_FILE}")


if __name__ == "__main__":
    main()
