import requests
import pandas as pd
import os
from datetime import datetime

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
RAW_DIR = "data/raw/openmeteo"
SESSIONS_FILE = "data/raw/openf1/sessions_2024.csv"
CIRCUITS_FILE = "data/reference/circuit_coordinates.csv"

def fetch_weather(lat, lon, date_str):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,cloud_cover,wind_speed_10m,wind_gusts_10m"
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def main():
    if not os.path.exists(SESSIONS_FILE) or not os.path.exists(CIRCUITS_FILE):
        print("Required files missing. Run fetch_openf1.py first and ensure circuit_coordinates.csv exists.")
        return

    sessions_df = pd.read_csv(SESSIONS_FILE)
    circuits_df = pd.read_csv(CIRCUITS_FILE)

    sample_session = sessions_df.iloc[0]
    session_key = sample_session['session_key']
    circuit_key = sample_session['circuit_key']
    date_start = sample_session['date_start'].split('T')[0]

    circuit_info = circuits_df[circuits_df['circuit_key'] == circuit_key]
    if circuit_info.empty:
        print(f"No coordinate data for circuit_key {circuit_key}")
        return

    lat = circuit_info.iloc[0]['latitude']
    lon = circuit_info.iloc[0]['longitude']

    print(f"Fetching Open-Meteo weather for session {session_key} (Circuit: {circuit_key}, Date: {date_start})...")
    weather_data = fetch_weather(lat, lon, date_start)
    
    hourly_df = pd.DataFrame(weather_data['hourly'])
    hourly_df['session_key'] = session_key
    
    filename = f"openmeteo_{session_key}.csv"
    hourly_df.to_csv(os.path.join(RAW_DIR, filename), index=False)
    print(f"Saved {filename}")

if __name__ == "__main__":
    main()
