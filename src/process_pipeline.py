import pandas as pd
import numpy as np
import os
import glob
from tqdm import tqdm


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

RAW_OPENF1 = os.path.join(PROJECT_ROOT, "data", "raw", "openf1")
RAW_OPENMETEO = os.path.join(PROJECT_ROOT, "data", "raw", "openmeteo")
REFERENCE = os.path.join(PROJECT_ROOT, "data", "reference")
PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")

tqdm.pandas()


def load_all_csvs(pattern):
    files = glob.glob(pattern)

    if not files:
        return pd.DataFrame()

    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def build_star_schema():
    print("Starting Star Schema Transformation...")

    os.makedirs(PROCESSED, exist_ok=True)

    pipeline_steps = tqdm(total=10, desc="Pipeline stages")

    print("Loading raw files...")

    sessions_raw = pd.read_csv(os.path.join(RAW_OPENF1, "sessions_2023_2025.csv"))
    meetings_raw = pd.read_csv(os.path.join(RAW_OPENF1, "meetings_2023_2025.csv"))
    drivers_raw = pd.read_csv(os.path.join(RAW_OPENF1, "drivers_2023_2025.csv"))
    laps_raw = pd.read_csv(os.path.join(RAW_OPENF1, "laps_2023_2025.csv"))
    stints_raw = pd.read_csv(os.path.join(RAW_OPENF1, "stints_2023_2025.csv"))
    weather_f1_raw = pd.read_csv(os.path.join(RAW_OPENF1, "weather_2023_2025.csv"))
    pit_raw = pd.read_csv(os.path.join(RAW_OPENF1, "pit_2023_2025.csv"))
    weather_om_raw = pd.read_csv(os.path.join(RAW_OPENMETEO, "openmeteo_2023_2025.csv"))
    circuit_ref = pd.read_csv(os.path.join(REFERENCE, "circuit_coordinates.csv"))

    sessions_raw["session_key"] = sessions_raw["session_key"].astype(int)
    meetings_raw["meeting_key"] = meetings_raw["meeting_key"].astype(int)
    drivers_raw["session_key"] = drivers_raw["session_key"].astype(int)
    laps_raw["session_key"] = laps_raw["session_key"].astype(int)
    stints_raw["session_key"] = stints_raw["session_key"].astype(int)
    weather_f1_raw["session_key"] = weather_f1_raw["session_key"].astype(int)
    pit_raw["session_key"] = pit_raw["session_key"].astype(int)
    weather_om_raw["session_key"] = weather_om_raw["session_key"].astype(int)

    if "driver_number" in drivers_raw.columns:
        drivers_raw["driver_number"] = pd.to_numeric(drivers_raw["driver_number"], errors="coerce")

    if "driver_number" in laps_raw.columns:
        laps_raw["driver_number"] = pd.to_numeric(laps_raw["driver_number"], errors="coerce")

    if "driver_number" in stints_raw.columns:
        stints_raw["driver_number"] = pd.to_numeric(stints_raw["driver_number"], errors="coerce")

    if "driver_number" in pit_raw.columns:
        pit_raw["driver_number"] = pd.to_numeric(pit_raw["driver_number"], errors="coerce")

    pipeline_steps.update(1)

    print("Building dim_driver...")

    dim_driver = drivers_raw[
        ["driver_number", "full_name", "name_acronym", "first_name", "last_name", "country_code"]
    ].dropna(subset=["driver_number"]).drop_duplicates()

    dim_driver["driver_number"] = dim_driver["driver_number"].astype(int)
    dim_driver = dim_driver.sort_values(["driver_number", "full_name"])
    dim_driver = dim_driver.drop_duplicates(subset=["driver_number"], keep="last")
    dim_driver["driver_id"] = dim_driver["driver_number"].astype(str)

    dim_driver.to_csv(os.path.join(PROCESSED, "dim_driver.csv"), index=False)
    pipeline_steps.update(1)

    print("Building dim_team...")

    dim_team = drivers_raw[
        ["team_name", "team_colour"]
    ].dropna(subset=["team_name"]).drop_duplicates()

    dim_team = dim_team.sort_values(["team_name", "team_colour"])
    dim_team = dim_team.drop_duplicates(subset=["team_name"], keep="last")
    dim_team["team_id"] = range(1, len(dim_team) + 1)

    dim_team.to_csv(os.path.join(PROCESSED, "dim_team.csv"), index=False)
    pipeline_steps.update(1)

    print("Building dim_circuit...")

    dim_circuit = circuit_ref.copy()
    dim_circuit = dim_circuit.dropna(subset=["circuit_key", "latitude", "longitude"]).copy()

    dim_circuit["circuit_key"] = dim_circuit["circuit_key"].astype(str)
    dim_circuit["circuit_id"] = dim_circuit["circuit_key"]

    dim_circuit.rename(columns={
        "source_note": "coordinate_source_note"
    }, inplace=True)

    dim_circuit = dim_circuit.drop_duplicates(subset=["circuit_id"])

    dim_circuit.to_csv(os.path.join(PROCESSED, "dim_circuit.csv"), index=False)
    pipeline_steps.update(1)

    print("Building dim_race...")

    dim_race = pd.merge(
        sessions_raw,
        meetings_raw[["meeting_key", "meeting_name", "country_name", "location", "year"]],
        on="meeting_key",
        how="left",
        suffixes=("", "_meeting")
    )

    dim_race["race_id"] = dim_race["session_key"].astype(str)

    if "season" in dim_race.columns:
        dim_race["season"] = dim_race["season"]
    elif "year" in dim_race.columns:
        dim_race["season"] = dim_race["year"]
    elif "year_meeting" in dim_race.columns:
        dim_race["season"] = dim_race["year_meeting"]

    dim_race.rename(columns={
        "date_start": "date_start_utc",
        "date_end": "date_end_utc"
    }, inplace=True)

    dim_race = dim_race.drop_duplicates(subset=["race_id"])

    dim_race.to_csv(os.path.join(PROCESSED, "dim_race.csv"), index=False)
    pipeline_steps.update(1)

    print("Building dim_date...")

    all_dates = pd.to_datetime(
        sessions_raw["date_start"],
        errors="coerce",
        utc=True
    ).dt.date.dropna().unique()

    dim_date = pd.DataFrame({"date": all_dates})
    dim_date["date"] = pd.to_datetime(dim_date["date"])

    dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d")
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["day"] = dim_date["date"].dt.day
    dim_date["season"] = dim_date["year"]
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["month_name"] = dim_date["date"].dt.strftime("%B")
    dim_date["round_month_label"] = dim_date["date"].dt.strftime("%B %Y")

    dim_date = dim_date.sort_values("date")

    dim_date.to_csv(os.path.join(PROCESSED, "dim_date.csv"), index=False)
    pipeline_steps.update(1)

    print("Building dim_tyre_stint...")

    dim_stint = stints_raw.copy()

    dim_stint = dim_stint.dropna(
        subset=["session_key", "driver_number", "stint_number", "lap_start", "lap_end"]
    ).copy()

    dim_stint["session_key"] = dim_stint["session_key"].astype(int)
    dim_stint["driver_number"] = dim_stint["driver_number"].astype(int)
    dim_stint["stint_number"] = dim_stint["stint_number"].astype(int)
    dim_stint["lap_start"] = dim_stint["lap_start"].astype(int)
    dim_stint["lap_end"] = dim_stint["lap_end"].astype(int)

    dim_stint["stint_id"] = (
        dim_stint["session_key"].astype(str)
        + "_"
        + dim_stint["driver_number"].astype(str)
        + "_"
        + dim_stint["stint_number"].astype(str)
    )

    dim_stint["stint_length_laps"] = dim_stint["lap_end"] - dim_stint["lap_start"] + 1

    dim_stint = dim_stint.drop_duplicates(subset=["stint_id"])

    dim_stint.to_csv(os.path.join(PROCESSED, "dim_tyre_stint.csv"), index=False)
    pipeline_steps.update(1)

    print("Building dim_weather_context...")

    weather_om_agg = weather_om_raw.groupby("session_key").agg({
        "temperature_2m": "mean",
        "relative_humidity_2m": "mean",
        "precipitation": "sum",
        "rain": "sum",
        "cloud_cover": "mean",
        "wind_speed_10m": "mean",
        "wind_gusts_10m": "max"
    }).reset_index()

    weather_om_agg.rename(columns={
        "temperature_2m": "avg_openmeteo_temperature_2m_c",
        "relative_humidity_2m": "avg_openmeteo_relative_humidity_2m_pct",
        "precipitation": "total_openmeteo_precipitation_mm",
        "rain": "total_openmeteo_rain_mm",
        "cloud_cover": "avg_openmeteo_cloud_cover_pct",
        "wind_speed_10m": "avg_openmeteo_wind_speed_10m_kmh",
        "wind_gusts_10m": "max_openmeteo_wind_gusts_10m_kmh"
    }, inplace=True)

    weather_f1_agg = weather_f1_raw.groupby("session_key").agg({
        "track_temperature": "mean",
        "air_temperature": "mean",
        "humidity": "mean",
        "rainfall": "max",
        "wind_speed": "mean"
    }).reset_index()

    weather_f1_agg.rename(columns={
        "track_temperature": "avg_openf1_track_temperature_c",
        "air_temperature": "avg_openf1_air_temperature_c",
        "humidity": "avg_openf1_humidity_pct",
        "rainfall": "openf1_rainfall_flag",
        "wind_speed": "avg_openf1_wind_speed"
    }, inplace=True)

    dim_weather = pd.merge(
        weather_om_agg,
        weather_f1_agg,
        on="session_key",
        how="outer"
    )

    dim_weather["openmeteo_rain_flag"] = dim_weather["total_openmeteo_rain_mm"].fillna(0) > 0
    dim_weather["weather_context_id"] = dim_weather["session_key"].astype(str)

    dim_weather["openf1_track_temp_bin"] = pd.cut(
        dim_weather["avg_openf1_track_temperature_c"],
        bins=[-np.inf, 25, 35, 45, np.inf],
        labels=["Cool", "Moderate", "Hot", "Very hot"]
    ).astype("object")

    dim_weather["openf1_track_temp_bin"] = dim_weather["openf1_track_temp_bin"].fillna("Unknown")

    dim_weather["openf1_weather_category"] = np.where(
        (dim_weather["openf1_rainfall_flag"].fillna(0) > 0)
        | (dim_weather["openmeteo_rain_flag"] == True),
        "Rain",
        "Dry"
    )

    dim_weather.to_csv(os.path.join(PROCESSED, "dim_weather_context.csv"), index=False)
    pipeline_steps.update(1)

    print("Building fact_driver_lap_performance...")

    fact_lap = laps_raw.copy()

    fact_lap = fact_lap.dropna(
        subset=["session_key", "driver_number", "lap_number", "lap_duration"]
    ).copy()

    fact_lap["session_key"] = fact_lap["session_key"].astype(int)
    fact_lap["driver_number"] = fact_lap["driver_number"].astype(int)
    fact_lap["lap_number"] = fact_lap["lap_number"].astype(int)

    session_fact_metadata = sessions_raw[
        ["session_key", "circuit_key", "date_start"]
    ].copy()

    session_fact_metadata.rename(columns={
        "circuit_key": "session_circuit_key",
        "date_start": "session_date_start"
    }, inplace=True)

    fact_lap = pd.merge(
        fact_lap,
        session_fact_metadata,
        on="session_key",
        how="left"
    )

    driver_team_map = drivers_raw[
        ["session_key", "driver_number", "team_name"]
    ].dropna(subset=["session_key", "driver_number"]).copy()

    driver_team_map["session_key"] = driver_team_map["session_key"].astype(int)
    driver_team_map["driver_number"] = driver_team_map["driver_number"].astype(int)

    driver_team_map = driver_team_map.drop_duplicates(
        subset=["session_key", "driver_number"],
        keep="last"
    )

    fact_lap = pd.merge(
        fact_lap,
        driver_team_map,
        on=["session_key", "driver_number"],
        how="left"
    )

    fact_lap = pd.merge(
        fact_lap,
        dim_team[["team_name", "team_id"]],
        on="team_name",
        how="left"
    )

    print("Matching laps to tyre stints...")

    stint_lookup = stints_raw.copy()

    stint_lookup = stint_lookup.dropna(
        subset=["session_key", "driver_number", "stint_number", "lap_start", "lap_end"]
    ).copy()

    stint_lookup["session_key"] = stint_lookup["session_key"].astype(int)
    stint_lookup["driver_number"] = stint_lookup["driver_number"].astype(int)
    stint_lookup["stint_number"] = stint_lookup["stint_number"].astype(int)
    stint_lookup["lap_start"] = stint_lookup["lap_start"].astype(int)
    stint_lookup["lap_end"] = stint_lookup["lap_end"].astype(int)

    stint_cols = [
        "session_key",
        "driver_number",
        "stint_number",
        "compound",
        "lap_start",
        "lap_end"
    ]

    if "tyre_age_at_start" in stint_lookup.columns:
        stint_cols.append("tyre_age_at_start")

    fact_lap = pd.merge(
        fact_lap,
        stint_lookup[stint_cols],
        on=["session_key", "driver_number"],
        how="left"
    )

    fact_lap = fact_lap[
        (fact_lap["lap_number"] >= fact_lap["lap_start"])
        & (fact_lap["lap_number"] <= fact_lap["lap_end"])
        ].copy()

    print(f"Rows after stint range matching: {len(fact_lap)}")

    print("Resolving duplicate stint matches...")

    natural_lap_key = ["session_key", "driver_number", "lap_number"]

    # Some OpenF1 stint ranges overlap at boundary laps
    # To keep the declared fact grain, each driver-lap must belong to only one stint
    # If a lap is both the end of one stint and the start of the next
    # we keep the stint that ends on that lap This avoids double-counting boundary laps
    fact_lap["stint_match_priority"] = np.select(
        [
            fact_lap["lap_number"] == fact_lap["lap_end"],
            fact_lap["lap_number"] == fact_lap["lap_start"]
        ],
        [
            0,  # prefer stint ending on this lap
            1  # then stint starting on this lap
        ],
        default=2
    )

    duplicate_lap_matches = fact_lap.duplicated(subset=natural_lap_key).sum()

    if duplicate_lap_matches > 0:
        print(
            f"Found {duplicate_lap_matches} duplicate driver-lap matches. Keeping one stint assignment per driver-lap.")

    fact_lap = (
        fact_lap
        .sort_values(
            natural_lap_key + ["stint_match_priority", "stint_number"]
        )
        .drop_duplicates(
            subset=natural_lap_key,
            keep="first"
        )
        .drop(columns=["stint_match_priority"])
    )

    print(f"Rows after duplicate stint resolution: {len(fact_lap)}")

    fact_lap["stint_id"] = (
        fact_lap["session_key"].astype(str)
        + "_"
        + fact_lap["driver_number"].astype(str)
        + "_"
        + fact_lap["stint_number"].fillna(0).astype(int).astype(str)
    )

    if "tyre_age_at_start" not in fact_lap.columns:
        fact_lap["tyre_age_at_start"] = np.nan

    fact_lap["tyre_age_lap"] = np.where(
        fact_lap["tyre_age_at_start"].notna(),
        fact_lap["tyre_age_at_start"] + (fact_lap["lap_number"] - fact_lap["lap_start"]),
        fact_lap["lap_number"] - fact_lap["lap_start"] + 1
    )

    weather_f1_agg_for_fact = weather_f1_raw.groupby("session_key").agg({
        "track_temperature": "mean",
        "air_temperature": "mean",
        "rainfall": "max"
    }).reset_index()

    weather_f1_agg_for_fact.rename(columns={
        "track_temperature": "track_temperature_c",
        "air_temperature": "air_temperature_c",
        "rainfall": "rainfall_flag"
    }, inplace=True)

    fact_lap = pd.merge(
        fact_lap,
        weather_f1_agg_for_fact,
        on="session_key",
        how="left"
    )

    fact_lap["fact_lap_id"] = range(1, len(fact_lap) + 1)

    fact_lap["date_id"] = pd.to_datetime(
        fact_lap["session_date_start"],
        errors="coerce",
        utc=True
    ).dt.strftime("%Y%m%d")

    fact_lap["race_id"] = fact_lap["session_key"].astype(str)
    fact_lap["circuit_id"] = fact_lap["session_circuit_key"].astype(str)
    fact_lap["driver_id"] = fact_lap["driver_number"].astype(str)
    fact_lap["weather_context_id"] = fact_lap["session_key"].astype(str)

    fact_lap.rename(columns={
        "lap_duration": "lap_duration_sec",
        "duration_sector_1": "sector_1_duration_sec",
        "duration_sector_2": "sector_2_duration_sec",
        "duration_sector_3": "sector_3_duration_sec"
    }, inplace=True)

    fact_lap["valid_racing_lap_flag"] = True

    if "is_pit_out_lap" in fact_lap.columns:
        fact_lap["valid_racing_lap_flag"] = (
            fact_lap["valid_racing_lap_flag"]
            & (fact_lap["is_pit_out_lap"].fillna(False) == False)
        )

    fact_lap["valid_racing_lap_flag"] = (
        fact_lap["valid_racing_lap_flag"]
        & fact_lap["lap_duration_sec"].notna()
        & (fact_lap["lap_duration_sec"] > 0)
    )

    pit_laps = pit_raw[
        ["session_key", "driver_number", "lap_number"]
    ].dropna().drop_duplicates().copy()

    pit_laps["session_key"] = pit_laps["session_key"].astype(int)
    pit_laps["driver_number"] = pit_laps["driver_number"].astype(int)
    pit_laps["lap_number"] = pit_laps["lap_number"].astype(int)

    pit_lap_keys = set(
        zip(
            pit_laps["session_key"],
            pit_laps["driver_number"],
            pit_laps["lap_number"]
        )
    )

    print("Marking pit laps...")

    fact_lap["is_pit_lap"] = fact_lap.progress_apply(
        lambda row: (
            int(row["session_key"]),
            int(row["driver_number"]),
            int(row["lap_number"])
        ) in pit_lap_keys,
        axis=1
    )

    pit_window_lookup = {}

    for _, pit_row in pit_laps.iterrows():
        session_key = int(pit_row["session_key"])
        driver_number = int(pit_row["driver_number"])
        pit_lap_number = int(pit_row["lap_number"])

        for relative_lap in [-1, 0, 1, 2]:
            lookup_key = (session_key, driver_number, pit_lap_number + relative_lap)
            pit_window_lookup[lookup_key] = relative_lap

    print("Marking pit-window relative laps...")

    fact_lap["pit_window_relative_lap"] = fact_lap.progress_apply(
        lambda row: pit_window_lookup.get(
            (
                int(row["session_key"]),
                int(row["driver_number"]),
                int(row["lap_number"])
            ),
            np.nan
        ),
        axis=1
    )

    print("Marking pit-window flags...")

    fact_lap["pit_window_flag"] = fact_lap.progress_apply(
        lambda row: (
            int(row["session_key"]),
            int(row["driver_number"]),
            int(row["lap_number"])
        ) in pit_window_lookup,
        axis=1
    )

    fact_lap["pit_window_phase"] = np.select(
        [
            fact_lap["pit_window_relative_lap"] == -1,
            fact_lap["pit_window_relative_lap"] == 0,
            fact_lap["pit_window_relative_lap"] == 1,
            fact_lap["pit_window_relative_lap"] == 2
        ],
        [
            "Lap before pit",
            "Pit lap",
            "Pit-out lap",
            "First normal lap after pit"
        ],
        default=None
    )

    fact_lap["valid_racing_lap_flag"] = (
        fact_lap["valid_racing_lap_flag"]
        & (fact_lap["is_pit_lap"] == False)
    )

    valid_for_stint = fact_lap[
        fact_lap["valid_racing_lap_flag"] == True
    ].copy()

    stint_best = valid_for_stint.groupby("stint_id")["lap_duration_sec"].min().reset_index()
    stint_best.rename(columns={
        "lap_duration_sec": "stint_best_lap_duration_sec"
    }, inplace=True)

    fact_lap = pd.merge(
        fact_lap,
        stint_best,
        on="stint_id",
        how="left"
    )

    fact_lap["lap_time_delta_to_stint_best_sec"] = (
        fact_lap["lap_duration_sec"] - fact_lap["stint_best_lap_duration_sec"]
    )

    driver_median = valid_for_stint.groupby(
        ["session_key", "driver_number"]
    )["lap_duration_sec"].median().reset_index()

    driver_median.rename(columns={
        "lap_duration_sec": "driver_median_lap_duration_sec"
    }, inplace=True)

    fact_lap = pd.merge(
        fact_lap,
        driver_median,
        on=["session_key", "driver_number"],
        how="left"
    )

    fact_lap["lap_time_delta_to_driver_median_sec"] = (
        fact_lap["lap_duration_sec"] - fact_lap["driver_median_lap_duration_sec"]
    )

    fact_lap["position_nearest"] = np.nan

    fact_lap_cols = [
        "fact_lap_id",
        "date_id",
        "race_id",
        "circuit_id",
        "driver_id",
        "team_id",
        "stint_id",
        "weather_context_id",
        "session_key",
        "meeting_key",
        "driver_number",
        "lap_number",
        "lap_duration_sec",
        "sector_1_duration_sec",
        "sector_2_duration_sec",
        "sector_3_duration_sec",
        "i1_speed",
        "i2_speed",
        "st_speed",
        "compound",
        "tyre_age_lap",
        "track_temperature_c",
        "air_temperature_c",
        "rainfall_flag",
        "lap_time_delta_to_stint_best_sec",
        "lap_time_delta_to_driver_median_sec",
        "valid_racing_lap_flag",
        "is_pit_lap",
        "pit_window_flag",
        "pit_window_relative_lap",
        "pit_window_phase",
        "position_nearest"
    ]

    for col in fact_lap_cols:
        if col not in fact_lap.columns:
            fact_lap[col] = np.nan

    fact_lap = fact_lap[fact_lap_cols]

    fact_lap.to_csv(
        os.path.join(PROCESSED, "fact_driver_lap_performance.csv"),
        index=False
    )

    print(f"Created fact_driver_lap_performance.csv with {len(fact_lap)} rows")
    pipeline_steps.update(1)

    print("Building fact_pit_stop...")

    fact_pit = pit_raw.copy()

    fact_pit = fact_pit.dropna(subset=["session_key", "driver_number", "lap_number"]).copy()

    fact_pit["session_key"] = fact_pit["session_key"].astype(int)
    fact_pit["driver_number"] = fact_pit["driver_number"].astype(int)
    fact_pit["lap_number"] = fact_pit["lap_number"].astype(int)

    fact_pit = pd.merge(
        fact_pit,
        driver_team_map,
        on=["session_key", "driver_number"],
        how="left"
    )

    fact_pit = pd.merge(
        fact_pit,
        dim_team[["team_name", "team_id"]],
        on="team_name",
        how="left"
    )

    session_pit_metadata = sessions_raw[
        ["session_key", "circuit_key", "date_start"]
    ].copy()

    session_pit_metadata.rename(columns={
        "circuit_key": "session_circuit_key",
        "date_start": "session_date_start"
    }, inplace=True)

    fact_pit = pd.merge(
        fact_pit,
        session_pit_metadata,
        on="session_key",
        how="left"
    )

    fact_pit["fact_pit_id"] = range(1, len(fact_pit) + 1)

    fact_pit["date_id"] = pd.to_datetime(
        fact_pit["session_date_start"],
        errors="coerce",
        utc=True
    ).dt.strftime("%Y%m%d")

    fact_pit["race_id"] = fact_pit["session_key"].astype(str)
    fact_pit["circuit_id"] = fact_pit["session_circuit_key"].astype(str)
    fact_pit["driver_id"] = fact_pit["driver_number"].astype(str)
    fact_pit["weather_context_id"] = fact_pit["session_key"].astype(str)

    fact_pit.rename(columns={
        "date": "pit_time_utc",
        "pit_duration": "pit_duration_sec",
        "lane_duration": "lane_duration_sec",
        "stop_duration": "stop_duration_sec"
    }, inplace=True)

    valid_lap_for_pit = fact_lap[
        fact_lap["valid_racing_lap_flag"] == True
    ][[
        "session_key",
        "driver_number",
        "lap_number",
        "lap_time_delta_to_driver_median_sec"
    ]].copy()

    def calculate_pit_window_gain_loss(row):
        session_key = row["session_key"]
        driver_number = row["driver_number"]
        pit_lap_number = row["lap_number"]

        driver_laps = valid_lap_for_pit[
            (valid_lap_for_pit["session_key"] == session_key)
            & (valid_lap_for_pit["driver_number"] == driver_number)
        ]

        pre_window = driver_laps[
            (driver_laps["lap_number"] >= pit_lap_number - 3)
            & (driver_laps["lap_number"] <= pit_lap_number - 1)
        ]

        post_window = driver_laps[
            (driver_laps["lap_number"] >= pit_lap_number + 1)
            & (driver_laps["lap_number"] <= pit_lap_number + 3)
        ]

        if pre_window.empty or post_window.empty:
            return np.nan

        pre_avg = pre_window["lap_time_delta_to_driver_median_sec"].mean()
        post_avg = post_window["lap_time_delta_to_driver_median_sec"].mean()

        return post_avg - pre_avg

    print("Calculating pit-window gain/loss...")

    fact_pit["pit_window_gain_loss_sec"] = fact_pit.progress_apply(
        calculate_pit_window_gain_loss,
        axis=1
    )

    pit_cols = [
        "fact_pit_id",
        "date_id",
        "race_id",
        "circuit_id",
        "driver_id",
        "team_id",
        "weather_context_id",
        "session_key",
        "meeting_key",
        "driver_number",
        "lap_number",
        "pit_time_utc",
        "pit_duration_sec",
        "lane_duration_sec",
        "stop_duration_sec",
        "pit_window_gain_loss_sec"
    ]

    for col in pit_cols:
        if col not in fact_pit.columns:
            fact_pit[col] = np.nan

    fact_pit = fact_pit[pit_cols]

    fact_pit.to_csv(
        os.path.join(PROCESSED, "fact_pit_stop.csv"),
        index=False
    )

    print(f"Created fact_pit_stop.csv with {len(fact_pit)} rows")
    pipeline_steps.update(1)

    pipeline_steps.close()


def main():
    if not os.path.exists(RAW_OPENF1):
        print("Raw OpenF1 data not found. Run fetch scripts first.")
        return

    if not os.path.exists(RAW_OPENMETEO):
        print("Raw Open-Meteo data not found. Run fetch scripts first.")
        return

    build_star_schema()

    print("Pipeline complete. All Star Schema columns are synchronized.")


if __name__ == "__main__":
    main()