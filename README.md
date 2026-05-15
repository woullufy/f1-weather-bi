# F1 Tyre, Weather and Race Performance BI Project

## Project Overview

This project analyses how tyre compound, tyre age, track/weather conditions, pit windows, drivers, teams, and circuits relate to Formula 1 race lap-time performance.

| Item | Scope |
|---|---|
| Domain | Formula 1 race performance and race-strategy analysis |
| Seasons | 2023-2025 completed Formula 1 race sessions |
| Session type | Race sessions only |
| Main fact-table grain | One completed lap by one driver in one race session |
| Primary source | OpenF1 API |
| Secondary source | Open-Meteo Historical Weather API |
| Reference data | `data/reference/circuit_coordinates.csv` |
| BI tool | Tableau |

The project downloads public Formula 1 and weather data, transforms it into a star-schema-style CSV model, and uses Tableau to answer analytical questions about race performance.

## Analytical Questions

| ID | Analytical question | Dashboard component |
|---|---|---|
| Q1 | Which tyre compounds lose lap-time performance fastest? | Tyre age vs normalized lap-time delta by compound |
| Q2 | Does higher track temperature make soft tyres worse? | Soft-tyre lap-time loss by track temperature |
| Q3 | Which teams gain or lose the most around pit windows? | Pit-window comparison by team/phase |
| Q4 | Which drivers have the lowest lap-time variability? | Driver consistency ranking |
| Q5 | Are some circuits more sensitive to tyre wear or weather? | Circuit and compound sensitivity heatmap |

## Data Sources

| Source | Type | Used for | Link |
|---|---|---|---|
| OpenF1 API | Public API | Race sessions, meetings, drivers, laps, stints, pit stops, and track-side weather | https://openf1.org/docs/ |
| Open-Meteo Historical Weather API | Public API | External ambient weather context by circuit location and race date | https://open-meteo.com/en/docs/historical-weather-api |
| `circuit_coordinates.csv` | Local reference CSV | Circuit latitude/longitude for Open-Meteo requests | `data/reference/circuit_coordinates.csv` |

OpenF1 weather is used for track-side race conditions such as track temperature. Open-Meteo is used as external ambient weather context and does not replace OpenF1 track temperature.

## Repository Structure

```text
f1-weather-bi/
|-- README.md
|-- requirements.txt
|-- data/
|   |-- raw/
|   |   |-- openf1/
|   |   `-- openmeteo/
|   |-- processed/
|   `-- reference/
|       `-- circuit_coordinates.csv
|-- src/
|   |-- fetch_openf1.py
|   |-- fetch_openmeteo.py
|   `-- process_pipeline.py
|-- docs/
|   |-- data_dictionary.md
|   |-- source_er_models.md
|   |-- source_openf1.md
|   |-- source_openmeteo.md
|   |-- source_reference.md
|   `-- star_schema.md
|-- diagrams/
|-- dashboard_screenshots/
|-- tableau/
|   `-- f1_tyre_weather_dashboard.twbx
`-- slides/
    `-- presentation.pdf
```

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running The Pipeline

The repository already contains raw and processed CSV files. To rebuild the processed star-schema output from the existing raw files, run:

```bash
python src/process_pipeline.py
```

This reads:

```text
data/raw/openf1/
data/raw/openmeteo/
data/reference/circuit_coordinates.csv
```

and writes:

```text
data/processed/
```

To regenerate the raw API extracts first, run the fetch scripts before the processing step:

```bash
python src/fetch_openf1.py
python src/fetch_openmeteo.py
python src/process_pipeline.py
```

The fetch scripts create combined 2023-2025 CSV files. If an expected raw output file already exists, the fetch script skips it instead of downloading it again.

## Raw Data

OpenF1 raw files:

```text
data/raw/openf1/sessions_2023_2025.csv
data/raw/openf1/meetings_2023_2025.csv
data/raw/openf1/drivers_2023_2025.csv
data/raw/openf1/laps_2023_2025.csv
data/raw/openf1/stints_2023_2025.csv
data/raw/openf1/weather_2023_2025.csv
data/raw/openf1/pit_2023_2025.csv
```

Open-Meteo raw file:

```text
data/raw/openmeteo/openmeteo_2023_2025.csv
```

The reference file for circuit coordinates is:

```text
data/reference/circuit_coordinates.csv
```

## Processed Data

The pipeline exports these Tableau-ready files:

```text
data/processed/fact_driver_lap_performance.csv
data/processed/fact_pit_stop.csv
data/processed/dim_date.csv
data/processed/dim_race.csv
data/processed/dim_circuit.csv
data/processed/dim_driver.csv
data/processed/dim_team.csv
data/processed/dim_tyre_stint.csv
data/processed/dim_weather_context.csv
```

### Main Fact Table

`fact_driver_lap_performance.csv` contains one row per completed driver lap after joining lap data, driver/team metadata, tyre stint information, race metadata, pit-window flags, and session-level weather values.

Current exported columns:

```text
fact_lap_id,date_id,race_id,circuit_id,driver_id,team_id,stint_id,
weather_context_id,session_key,meeting_key,driver_number,lap_number,
lap_duration_sec,sector_1_duration_sec,sector_2_duration_sec,
sector_3_duration_sec,i1_speed,i2_speed,st_speed,compound,tyre_age_lap,
track_temperature_c,air_temperature_c,rainfall_flag,
lap_time_delta_to_stint_best_sec,lap_time_delta_to_driver_median_sec,
valid_racing_lap_flag,is_pit_lap,pit_window_flag,
pit_window_relative_lap,pit_window_phase,position_nearest
```

### Pit-Stop Fact Table

`fact_pit_stop.csv` contains one row per pit stop and includes pit timing plus a pit-window gain/loss metric.

Current exported columns:

```text
fact_pit_id,date_id,race_id,circuit_id,driver_id,team_id,
weather_context_id,session_key,meeting_key,driver_number,lap_number,
pit_time_utc,pit_duration_sec,lane_duration_sec,stop_duration_sec,
pit_window_gain_loss_sec
```

### Dimensions

The dimension tables provide date, race, circuit, driver, team, tyre-stint, and weather context attributes. Their current schemas are visible in the CSV headers in `data/processed/`.

## Data Model

The central model is a star schema around `fact_driver_lap_performance.csv`.

Main relationships:

```text
fact_driver_lap_performance.date_id = dim_date.date_id
fact_driver_lap_performance.race_id = dim_race.race_id
fact_driver_lap_performance.circuit_id = dim_circuit.circuit_id
fact_driver_lap_performance.driver_id = dim_driver.driver_id
fact_driver_lap_performance.team_id = dim_team.team_id
fact_driver_lap_performance.stint_id = dim_tyre_stint.stint_id
fact_driver_lap_performance.weather_context_id = dim_weather_context.weather_context_id
```

The pit-stop table uses the same race, circuit, driver, team, and weather context identifiers, but it has a different grain: one row per pit stop.

More modelling detail is available in:

```text
docs/source_openf1.md
docs/source_openmeteo.md
docs/source_reference.md
docs/star_schema.md
```

## Main Derived Fields

| Field | Meaning |
|---|---|
| `tyre_age_lap` | Estimated tyre age for a lap based on stint start and tyre age at stint start |
| `lap_time_delta_to_stint_best_sec` | Lap-time loss compared with the best valid lap in the same stint |
| `lap_time_delta_to_driver_median_sec` | Lap-time difference from the driver's median lap in the same race session |
| `valid_racing_lap_flag` | Boolean flag used to exclude pit laps and invalid lap-time rows from race-pace analysis |
| `pit_window_flag` | Marks laps around a pit stop window |
| `pit_window_phase` | Labels the lap's position relative to a pit stop |
| `pit_window_gain_loss_sec` | Difference between post-pit and pre-pit average lap-time delta in the current pipeline |
| `openf1_track_temp_bin` | Session-level OpenF1 track-temperature category |
| `openf1_weather_category` | Session-level dry/rain category derived from OpenF1 and Open-Meteo rain indicators |

## Tableau Workbook

The Tableau workbook is stored at:

```text
tableau/f1_tyre_weather_dashboard.twbx
```

To view it:

1. Open Tableau.
2. Open `tableau/f1_tyre_weather_dashboard.twbx`.
3. If Tableau asks for file locations, reconnect the data sources to the CSV files in `data/processed/`.

Dashboard screenshots used for presentation material are stored in:

```text
dashboard_screenshots/
```

## Presentation

The final slide deck is stored at:

```text
slides/presentation.pdf
```

## Known Limitations

- The analysis shows associations, not causal proof.
- Lap times are affected by fuel load, traffic, safety cars, tyre strategy, team orders, car performance, and driver behavior.
- The current processing script aggregates OpenF1 weather to the race-session level before joining it to lap facts, so track-temperature analysis compares session-level conditions rather than exact lap-by-lap weather changes.
- Open-Meteo provides external ambient/reanalysis weather and may not match the exact circuit microclimate.
- `position_nearest` is currently exported as a placeholder because the position endpoint is not part of the current pipeline.
- `stop_duration_sec` is not consistently available for all races, so `lane_duration_sec` is usually the safer pit-stop timing measure.
- Safety-car and red-flag filtering is approximate because race-control events are not part of the current pipeline.
