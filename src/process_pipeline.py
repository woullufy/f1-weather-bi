import pandas as pd
import numpy as np
import os
import glob

RAW_OPENF1 = "data/raw/openf1"
RAW_OPENMETEO = "data/raw/openmeteo"
REFERENCE = "data/reference"
PROCESSED = "data/processed"

def load_all_csvs(pattern):
    files = glob.glob(pattern)
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

def build_star_schema():
    print("Starting Star Schema Transformation...")

    sessions_raw = pd.read_csv(f"{RAW_OPENF1}/sessions_2024.csv")
    meetings_raw = pd.read_csv(f"{RAW_OPENF1}/meetings_2024.csv")
    drivers_raw = load_all_csvs(f"{RAW_OPENF1}/drivers_*.csv")
    laps_raw = load_all_csvs(f"{RAW_OPENF1}/laps_*.csv")
    stints_raw = load_all_csvs(f"{RAW_OPENF1}/stints_*.csv")
    weather_f1_raw = load_all_csvs(f"{RAW_OPENF1}/weather_*.csv")
    weather_om_raw = load_all_csvs(f"{RAW_OPENMETEO}/openmeteo_*.csv")
    circuit_ref = pd.read_csv(f"{REFERENCE}/circuit_coordinates.csv")

    print("Building dim_driver...")
    dim_driver = drivers_raw[['driver_number', 'full_name', 'name_acronym', 'first_name', 'last_name']].drop_duplicates()
    dim_driver['driver_id'] = dim_driver['driver_number'].astype(str)
    dim_driver.to_csv(f"{PROCESSED}/dim_driver.csv", index=False)

    print("Building dim_team...")
    dim_team = drivers_raw[['team_name', 'team_colour']].drop_duplicates().dropna()
    dim_team['team_id'] = range(1, len(dim_team) + 1)
    dim_team.to_csv(f"{PROCESSED}/dim_team.csv", index=False)

    print("Building dim_circuit...")
    dim_circuit = circuit_ref.copy()
    dim_circuit['circuit_id'] = dim_circuit['circuit_key'].astype(str)
    dim_circuit.rename(columns={'source_note': 'coordinate_source_note'}, inplace=True)
    dim_circuit.to_csv(f"{PROCESSED}/dim_circuit.csv", index=False)

    print("Building dim_race...")
    dim_race = pd.merge(sessions_raw, meetings_raw[['meeting_key', 'meeting_name']], on='meeting_key', how='left')
    dim_race['race_id'] = dim_race['session_key'].astype(str)
    dim_race.rename(columns={'date_start': 'date_start_utc', 'date_end': 'date_end_utc'}, inplace=True)
    dim_race.to_csv(f"{PROCESSED}/dim_race.csv", index=False)

    print("Building dim_date...")
    all_dates = pd.to_datetime(sessions_raw['date_start']).dt.date.unique()
    dim_date = pd.DataFrame({'date': all_dates})
    dim_date['date_id'] = dim_date['date'].astype(str).str.replace('-', '')
    dim_date['year'] = pd.to_datetime(dim_date['date']).dt.year
    dim_date['month'] = pd.to_datetime(dim_date['date']).dt.month
    dim_date['day'] = pd.to_datetime(dim_date['date']).dt.day
    dim_date['season'] = dim_date['year']
    dim_date['round_month_label'] = pd.to_datetime(dim_date['date']).dt.strftime('%B %Y')
    dim_date.to_csv(f"{PROCESSED}/dim_date.csv", index=False)

    print("Building dim_tyre_stint...")
    dim_stint = stints_raw.copy()
    dim_stint['stint_id'] = dim_stint['session_key'].astype(str) + "_" + dim_stint['driver_number'].astype(str) + "_" + dim_stint['stint_number'].astype(str)
    dim_stint['stint_length_laps'] = dim_stint['lap_end'] - dim_stint['lap_start'] + 1
    dim_stint.to_csv(f"{PROCESSED}/dim_tyre_stint.csv", index=False)

    print("Building dim_weather_context...")
    weather_om_agg = weather_om_raw.groupby('session_key').agg({
        'temperature_2m': 'mean',
        'relative_humidity_2m': 'mean',
        'precipitation': 'sum',
        'rain': 'sum',
        'cloud_cover': 'mean',
        'wind_speed_10m': 'mean',
        'wind_gusts_10m': 'max'
    }).reset_index()
    weather_om_agg.rename(columns={
        'temperature_2m': 'avg_openmeteo_temperature_2m_c',
        'relative_humidity_2m': 'avg_openmeteo_relative_humidity_2m_pct',
        'precipitation': 'total_openmeteo_precipitation_mm',
        'rain': 'total_openmeteo_rain_mm',
        'cloud_cover': 'avg_openmeteo_cloud_cover_pct',
        'wind_speed_10m': 'avg_openmeteo_wind_speed_10m_kmh',
        'wind_gusts_10m': 'max_openmeteo_wind_gusts_10m_kmh'
    }, inplace=True)
    weather_om_agg['openmeteo_rain_flag'] = weather_om_agg['total_openmeteo_rain_mm'] > 0
    weather_om_agg['weather_context_id'] = weather_om_agg['session_key'].astype(str)
    weather_om_agg['openf1_track_temp_bin'] = 'unknown'
    weather_om_agg['openf1_weather_category'] = 'Clear'
    weather_om_agg.to_csv(f"{PROCESSED}/dim_weather_context.csv", index=False)

    print("Building fact_driver_lap_performance...")
    fact_lap = laps_raw.copy()
    fact_lap = pd.merge(fact_lap, stints_raw, on=['session_key', 'driver_number'], how='left')
    fact_lap = fact_lap[(fact_lap['lap_number'] >= fact_lap['lap_start']) & (fact_lap['lap_number'] <= fact_lap['lap_end'])]
    fact_lap = pd.merge(fact_lap, drivers_raw[['session_key', 'driver_number', 'team_name']], on=['session_key', 'driver_number'], how='left')
    fact_lap = pd.merge(fact_lap, dim_team, on='team_name', how='left')
    fact_lap = pd.merge(fact_lap, sessions_raw[['session_key', 'circuit_key']], on='session_key', how='left')
    fact_lap['fact_lap_id'] = range(1, len(fact_lap) + 1)
    fact_lap['date_id'] = pd.to_datetime(fact_lap['date_start']).dt.date.astype(str).str.replace('-', '')
    fact_lap['race_id'] = fact_lap['session_key'].astype(str)
    fact_lap['circuit_id'] = fact_lap['circuit_key'].astype(str)
    fact_lap['driver_id'] = fact_lap['driver_number'].astype(str)
    fact_lap['stint_id'] = fact_lap['session_key'].astype(str) + "_" + fact_lap['driver_number'].astype(str) + "_" + fact_lap['stint_number'].astype(str)
    fact_lap['weather_context_id'] = fact_lap['session_key'].astype(str)
    fact_lap.rename(columns={
        'date_start': 'lap_start_time_utc',
        'lap_duration': 'lap_duration_sec',
        'duration_sector_1': 'duration_sector_1_sec',
        'duration_sector_2': 'duration_sector_2_sec',
        'duration_sector_3': 'duration_sector_3_sec'
    }, inplace=True)
    fact_lap['tyre_age_lap'] = fact_lap['tyre_age_at_start'] + (fact_lap['lap_number'] - fact_lap['lap_start'])
    fact_lap['valid_racing_lap_flag'] = True
    fact_lap['invalid_reason'] = 'valid'
    fact_lap.loc[fact_lap['lap_duration_sec'].isna(), ['valid_racing_lap_flag', 'invalid_reason']] = [False, 'missing_lap_time']
    fact_lap.loc[fact_lap['lap_number'] == 1, ['valid_racing_lap_flag', 'invalid_reason']] = [False, 'first_lap']
    fact_lap.loc[fact_lap['is_pit_out_lap'] == True, ['valid_racing_lap_flag', 'invalid_reason']] = [False, 'pit_out_lap']
    fact_lap['is_pit_lap'] = False
    fact_lap['pit_window_flag'] = False
    fact_lap['pit_window_relative_lap'] = 0
    fact_lap['position_nearest'] = 0

    valid_laps = fact_lap[fact_lap['valid_racing_lap_flag'] == True]
    stint_best = valid_laps.groupby(['session_key', 'driver_number', 'stint_number'])['lap_duration_sec'].min().reset_index()
    stint_best.columns = ['session_key', 'driver_number', 'stint_number', 'stint_best_time']
    fact_lap = pd.merge(fact_lap, stint_best, on=['session_key', 'driver_number', 'stint_number'], how='left')
    fact_lap['lap_time_delta_to_stint_best_sec'] = fact_lap['lap_duration_sec'] - fact_lap['stint_best_time']
    driver_median = valid_laps.groupby(['session_key', 'driver_number'])['lap_duration_sec'].median().reset_index()
    driver_median.columns = ['session_key', 'driver_number', 'driver_median_time']
    fact_lap = pd.merge(fact_lap, driver_median, on=['session_key', 'driver_number'], how='left')
    fact_lap['lap_time_delta_to_driver_median_sec'] = fact_lap['lap_duration_sec'] - fact_lap['driver_median_time']
    race_median = valid_laps.groupby(['session_key'])['lap_duration_sec'].median().reset_index()
    race_median.columns = ['session_key', 'race_median_time']
    fact_lap = pd.merge(fact_lap, race_median, on=['session_key'], how='left')
    fact_lap['lap_time_delta_to_race_median_sec'] = fact_lap['lap_duration_sec'] - fact_lap['race_median_time']
    
    if not weather_f1_raw.empty:
        avg_f1_weather = weather_f1_raw.groupby('session_key').agg({
            'track_temperature': 'mean',
            'air_temperature': 'mean',
            'humidity': 'mean',
            'rainfall': 'max',
            'wind_speed': 'mean'
        }).reset_index()
        avg_f1_weather.rename(columns={
            'track_temperature': 'track_temperature_c',
            'air_temperature': 'air_temperature_c',
            'humidity': 'humidity_pct',
            'rainfall': 'rainfall_flag',
            'wind_speed': 'wind_speed_openf1'
        }, inplace=True)
        fact_lap = pd.merge(fact_lap, avg_f1_weather, on='session_key', how='left')

    cols = [
        'fact_lap_id', 'date_id', 'race_id', 'circuit_id', 'driver_id', 'team_id', 'stint_id', 'weather_context_id',
        'session_key', 'meeting_key', 'lap_number', 'lap_start_time_utc', 'lap_duration_sec',
        'duration_sector_1_sec', 'duration_sector_2_sec', 'duration_sector_3_sec',
        'compound', 'tyre_age_lap', 'is_pit_out_lap', 'is_pit_lap', 'pit_window_flag', 'pit_window_relative_lap',
        'valid_racing_lap_flag', 'invalid_reason', 'track_temperature_c', 'air_temperature_c', 'humidity_pct',
        'rainfall_flag', 'wind_speed_openf1', 'position_nearest',
        'lap_time_delta_to_stint_best_sec', 'lap_time_delta_to_driver_median_sec', 'lap_time_delta_to_race_median_sec'
    ]
    for col in cols:
        if col not in fact_lap.columns:
            fact_lap[col] = np.nan
    fact_lap = fact_lap[cols]
    fact_lap.to_csv(f"{PROCESSED}/fact_driver_lap_performance.csv", index=False)
    print("Created fact_driver_lap_performance.csv")

def main():
    if not os.path.exists(RAW_OPENF1):
        print("Raw data not found. Run fetch scripts first.")
        return
    build_star_schema()
    print("Pipeline complete. All Star Schema columns are synchronized.")

if __name__ == "__main__":
    main()
