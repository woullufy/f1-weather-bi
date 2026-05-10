import requests
import pandas as pd
import os
import time
from tqdm import tqdm

BASE_URL = "https://api.openf1.org/v1"
RAW_DIR = "data/raw/openf1"

def fetch_data(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    for attempt in range(5):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 429:
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == 4:
                raise e
            time.sleep(1)
    return None

def save_to_csv(data, filename):
    if not data:
        print(f"No data for {filename}")
        return
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(RAW_DIR, filename), index=False)
    print(f"Saved {filename}")

def main():
    print("Fetching sessions...")
    sessions = fetch_data("sessions", {"year": 2024, "session_name": "Race"})
    
    if not sessions:
        print("No sessions found for 2024.")
        return
    
    save_to_csv(sessions, "sessions_2024.csv")

    sample_session = sessions[0]
    session_key = sample_session['session_key']
    print(f"Selected session: {session_key}")
    
    print("Fetching meetings...")
    meetings = fetch_data("meetings", {"year": 2024})
    save_to_csv(meetings, "meetings_2024.csv")

    print(f"Fetching laps for session {session_key}...")
    laps = fetch_data("laps", {"session_key": session_key})
    save_to_csv(laps, f"laps_{session_key}.csv")

    print(f"Fetching stints for session {session_key}...")
    stints = fetch_data("stints", {"session_key": session_key})
    save_to_csv(stints, f"stints_{session_key}.csv")

    print(f"Fetching weather for session {session_key}...")
    weather = fetch_data("weather", {"session_key": session_key})
    save_to_csv(weather, f"weather_{session_key}.csv")

    print(f"Fetching drivers for session {session_key}...")
    drivers = fetch_data("drivers", {"session_key": session_key})
    save_to_csv(drivers, f"drivers_{session_key}.csv")

if __name__ == "__main__":
    main()
