import requests
import pandas as pd
import os
from datetime import datetime
import time
from tqdm import tqdm

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "openmeteo")
SESSIONS_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "openf1", "sessions_2023_2025.csv")
CIRCUITS_FILE = os.path.join(PROJECT_ROOT, "data", "reference", "circuit_coordinates.csv")

OUTPUT_FILE = "openmeteo_2023_2025.csv"

def fetch_weather(lat, lon, date_str):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,cloud_cover,wind_speed_10m,wind_gusts_10m"
    }

    for attempt in range(5):
        try:
            response = requests.get(BASE_URL, params=params, timeout=60)

            if response.status_code == 429:
                wait_time = 2 ** attempt
                print(f"Rate limited by Open-Meteo. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as error:
            if attempt == 4:
                print(f"Open-Meteo request failed for {lat}, {lon}, {date_str}: {error}")
                return None

            wait_time = 2 ** attempt
            print(f"Open-Meteo request failed. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

    return None

def main():
    if not os.path.exists(SESSIONS_FILE) or not os.path.exists(CIRCUITS_FILE):
        print("Required files missing. Run fetch_openf1.py first and ensure circuit_coordinates.csv exists.")
        return

    sessions_df = pd.read_csv(SESSIONS_FILE)
    circuits_df = pd.read_csv(CIRCUITS_FILE)

    os.makedirs(RAW_DIR, exist_ok=True)

    output_path = os.path.join(RAW_DIR, OUTPUT_FILE)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"Skipping existing file: {OUTPUT_FILE}")
        return

    all_weather_frames = []

    sessions_df = sessions_df.dropna(subset=["session_key", "circuit_key", "date_start"]).copy()
    circuits_df = circuits_df.dropna(subset=["circuit_key", "latitude", "longitude"]).copy()

    sessions_df["circuit_key"] = sessions_df["circuit_key"].astype(str)
    circuits_df["circuit_key"] = circuits_df["circuit_key"].astype(str)

    for _, session in tqdm(sessions_df.iterrows(), total=len(sessions_df), desc="Open-Meteo sessions"):
        session_key = session["session_key"]
        circuit_key = session["circuit_key"]
        date_start = str(session["date_start"]).split("T")[0]

        circuit_info = circuits_df[circuits_df["circuit_key"] == circuit_key]

        if circuit_info.empty:
            print(f"No coordinate data for circuit_key {circuit_key}, session {session_key}")
            continue

        lat = circuit_info.iloc[0]["latitude"]
        lon = circuit_info.iloc[0]["longitude"]

        print(f"Fetching Open-Meteo weather for session {session_key}, circuit {circuit_key}, date {date_start}...")

        weather_data = fetch_weather(lat, lon, date_start)

        if not weather_data or "hourly" not in weather_data:
            print(f"No Open-Meteo weather data for session {session_key}")
            continue

        hourly_df = pd.DataFrame(weather_data["hourly"])
        hourly_df["session_key"] = session_key
        hourly_df["circuit_key"] = circuit_key
        hourly_df["weather_date"] = date_start
        hourly_df["latitude"] = lat
        hourly_df["longitude"] = lon

        all_weather_frames.append(hourly_df)

        time.sleep(0.25)

    if not all_weather_frames:
        print("No Open-Meteo weather data collected.")
        return

    combined_weather = pd.concat(all_weather_frames, ignore_index=True)
    combined_weather = combined_weather.drop_duplicates()

    combined_weather.to_csv(output_path, index=False)
    print(f"Saved {OUTPUT_FILE} ({len(combined_weather)} rows, {len(combined_weather.columns)} columns)")

if __name__ == "__main__":
    main()
