import requests
import pandas as pd
import os
import time
from tqdm import tqdm

BASE_URL = "https://api.openf1.org/v1"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "openf1")

SEASONS = [2023, 2024, 2025]
SESSION_NAME = "Race"
OUTPUT_SUFFIX = "2023_2025"

REQUEST_PAUSE_SECONDS = 1.0
MAX_ATTEMPTS = 7

SESSION_ENDPOINTS = [
    "drivers",
    "laps",
    "stints",
    "weather",
    "pit",
]

def fetch_data(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = requests.get(url, params=params, timeout=60)

            if response.status_code == 429:
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            if response.status_code == 404:
                print(f"Endpoint/data not found: {endpoint} with params={params}")
                return []

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if attempt == MAX_ATTEMPTS - 1:
                print(f"Request failed after 5 attempts: {endpoint} with params={params}")
                raise e

            wait_time = 2 ** attempt
            print(f"Request failed. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

    return []

def save_dataframe(df, filename):
    if df.empty:
        print(f"No data for {filename}")
        return

    os.makedirs(RAW_DIR, exist_ok=True)
    output_path = os.path.join(RAW_DIR, filename)
    df.to_csv(output_path, index=False)
    print(f"Saved {filename} ({len(df)} rows, {len(df.columns)} columns)")

def fetch_completed_race_sessions():
    all_sessions = []

    for season in SEASONS:
        print(f"Fetching {season} {SESSION_NAME} sessions...")
        sessions = fetch_data("sessions", {"year": season, "session_name": SESSION_NAME})

        if not sessions:
            print(f"No race sessions found for {season}.")
            continue

        season_df = pd.DataFrame(sessions)
        season_df["season"] = season
        all_sessions.append(season_df)

    if not all_sessions:
        return pd.DataFrame()

    sessions_df = pd.concat(all_sessions, ignore_index=True)

    sessions_df = sessions_df.dropna(subset=["session_key"])
    sessions_df["date_end_parsed"] = pd.to_datetime(sessions_df["date_end"], errors="coerce", utc=True)

    now_utc = pd.Timestamp.utcnow()

    sessions_df = sessions_df[
        (sessions_df["session_name"] == SESSION_NAME)
        & (sessions_df["date_end_parsed"] <= now_utc)
        & (sessions_df["is_cancelled"] != True)
    ].copy()

    sessions_df = sessions_df.drop(columns=["date_end_parsed"])
    sessions_df = sessions_df.drop_duplicates(subset=["session_key"])
    sessions_df = sessions_df.sort_values(["year", "date_start", "session_key"])

    return sessions_df

def fetch_meetings_for_seasons():
    all_meetings = []

    for season in SEASONS:
        print(f"Fetching {season} meetings...")
        meetings = fetch_data("meetings", {"year": season})

        if not meetings:
            print(f"No meetings found for {season}.")
            continue

        meetings_df = pd.DataFrame(meetings)
        meetings_df["season"] = season
        all_meetings.append(meetings_df)

    if not all_meetings:
        return pd.DataFrame()

    meetings_df = pd.concat(all_meetings, ignore_index=True)
    meetings_df = meetings_df.drop_duplicates(subset=["meeting_key"])
    meetings_df = meetings_df.sort_values(["year", "date_start", "meeting_key"])

    return meetings_df

def safe_drop_duplicates(df):
    if df.empty:
        return df

    unhashable_columns = []

    for column in df.columns:
        has_unhashable_values = df[column].map(
            lambda value: isinstance(value, (list, dict))
        ).any()

        if has_unhashable_values:
            unhashable_columns.append(column)

    hashable_columns = [
        column for column in df.columns
        if column not in unhashable_columns
    ]

    if not hashable_columns:
        return df.reset_index(drop=True)

    return df.drop_duplicates(subset=hashable_columns).reset_index(drop=True)

def fetch_endpoint_for_sessions(endpoint, session_keys):
    frames = []

    print(f"Fetching endpoint: {endpoint}")

    for session_key in tqdm(session_keys, desc=f"{endpoint} sessions"):
        data = fetch_data(endpoint, {"session_key": int(session_key)})

        if not data:
            print(f"No {endpoint} data for session {session_key}")
            continue

        df = pd.DataFrame(data)

        if "session_key" not in df.columns:
            df["session_key"] = session_key

        frames.append(df)

        time.sleep(REQUEST_PAUSE_SECONDS)

    if not frames:
        return pd.DataFrame()

    combined_df = pd.concat(frames, ignore_index=True)
    combined_df = safe_drop_duplicates(combined_df)

    return combined_df

def main():
    print("Fetching completed race sessions for project scope...")
    sessions_df = fetch_completed_race_sessions()

    if sessions_df.empty:
        print("No completed race sessions found.")
        return

    save_dataframe(sessions_df, f"sessions_{OUTPUT_SUFFIX}.csv")

    session_keys = sessions_df["session_key"].astype(int).tolist()
    print(f"Found {len(session_keys)} completed race sessions in scope.")

    meetings_df = fetch_meetings_for_seasons()
    save_dataframe(meetings_df, f"meetings_{OUTPUT_SUFFIX}.csv")

    for endpoint in SESSION_ENDPOINTS:
        output_file = f"{endpoint}_{OUTPUT_SUFFIX}.csv"
        output_path = os.path.join(RAW_DIR, output_file)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"Skipping existing file: {output_file}")
            continue

        endpoint_df = fetch_endpoint_for_sessions(endpoint, session_keys)
        save_dataframe(endpoint_df, output_file)

    print("OpenF1 multi-season fetch complete.")

if __name__ == "__main__":
    main()
