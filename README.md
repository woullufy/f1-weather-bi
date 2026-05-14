# F1 Tyre, Weather and Race Performance BI Project

## 1. Project overview

This project analyses how tyre compound, tyre age, track/weather conditions, pit windows, drivers, teams, and circuits relate to Formula 1 race lap-time performance.

The project was created for **Business Intelligence 1 – Assignment 1**.

### Fixed project scope

| Item | Decision |
|---|---|
| Main domain | Formula 1 race performance and BI analysis |
| Seasons | 2023–2025 completed Formula 1 race sessions |
| Session type | Race sessions only |
| Main fact-table grain | One completed lap by one driver in one race session |
| Primary source | OpenF1 API |
| Secondary source | Open-Meteo Historical Weather API |
| Reference data | `data/reference/circuit_coordinates.csv` |
| BI tool | Tableau |

The project transforms raw API data into a star schema and exports Tableau-ready CSV files.

For the detailed implementation contract, see:

```text
docs/project_handoff.md
```

---

## 2. Analytical questions

The dashboard answers the following analytical questions:

| ID | Analytical question | Main dashboard component |
|---|---|---|
| Q1 | Which tyre compounds lose lap-time performance fastest? | Line chart: tyre age vs normalized lap-time delta by compound |
| Q2 | Does higher track temperature make soft tyres worse? | Box/scatter plot: SOFT tyre degradation by track-temperature bin |
| Q3 | Which teams gain or lose the most around pit windows? | Bar chart: team vs pit-window gain/loss |
| Q4 | Which drivers have the lowest lap-time variability? | Ranked bar chart: driver consistency |
| Q5 | Are some circuits more sensitive to tyre wear or weather? | Heatmap: circuit vs degradation/weather sensitivity |

### MVP priority

The minimum viable project must answer:

```text
Q1 Tyre degradation
Q2 Track temperature and soft tyres
Q4 Driver consistency
Q5 Circuit effects
```

Q3 pit-stop strategy is **MVP-plus** and should be implemented after the core pipeline works.

---

## 3. Data sources

| Source | Type | Used for | Link |
|---|---|---|---|
| OpenF1 API | Public API | Race sessions, meetings, drivers, laps, stints, pit stops, position data, session results, and track-side weather | https://openf1.org/docs/ |
| Open-Meteo Historical Weather API | Public API | External ambient weather context by circuit location and date/time | https://open-meteo.com/en/docs/historical-weather-api |
| `circuit_coordinates.csv` | Manual reference CSV | Circuit latitude/longitude for Open-Meteo requests | `data/reference/circuit_coordinates.csv` |

### Important data-source distinction

OpenF1 `/weather` is used for **track-side weather**, especially track temperature.

Open-Meteo is used for **external ambient weather context**. It does not replace OpenF1 track temperature.

---

## 4. Repository structure

Use this structure unless the whole group agrees to change it.

```text
f1-bi-assignment/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   │   ├── openf1/
│   │   └── openmeteo/
│   ├── processed/
│   └── reference/
│       └── circuit_coordinates.csv
├── notebooks/
│   └── 01_pipeline_exploration.ipynb
├── src/
│   ├── config.py
│   ├── fetch_openf1.py
│   ├── fetch_openmeteo.py
│   ├── load_reference.py
│   ├── clean_laps.py
│   ├── join_stints_weather.py
│   ├── derive_metrics.py
│   ├── build_dimensions.py
│   ├── build_facts.py
│   └── export_tableau_csv.py
├── docs/
│   ├── project_handoff.md
│   ├── source_er_models.md
│   ├── star_schema.md
│   └── data_dictionary.md
├── tableau/
│   └── f1_tyre_weather_dashboard.twbx
└── slides/
    └── presentation.pdf
```

### Folder purpose

| Folder/file | Purpose |
|---|---|
| `data/raw/` | Raw downloaded API data. Should be reproducible by running fetch scripts. |
| `data/processed/` | Final Tableau-ready CSV files. |
| `data/reference/` | Stable manually maintained lookup files, especially circuit coordinates. |
| `src/` | Reusable Python pipeline code. |
| `notebooks/` | Exploration and debugging notebooks. Final logic should be moved into `src/` where possible. |
| `docs/` | Modelling, handoff, schema, and data dictionary documentation. |
| `tableau/` | Tableau workbook. |
| `slides/` | Final presentation PDF and optional appendix material. |

---

## 5. Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Suggested packages for `requirements.txt`:

```text
pandas
numpy
requests
python-dateutil
pyarrow
tqdm
```

Add further packages only when they are actually used.

---

## 6. How to run the pipeline

### Option A: run the full export script

From the project root:

```bash
python src/export_tableau_csv.py
```

This should create or update the final CSV files in:

```text
data/processed/
```

### Option B: run step by step

```bash
python src/fetch_openf1.py
python src/fetch_openmeteo.py
python src/clean_laps.py
python src/join_stints_weather.py
python src/derive_metrics.py
python src/build_dimensions.py
python src/build_facts.py
python src/export_tableau_csv.py
```

### Pipeline stages

| Stage | Description | Owner |
|---|---|---|
| 1 | Fetch OpenF1 race sessions, meetings, drivers, laps, stints, and weather | Person 3 |
| 2 | Load circuit coordinates | Person 3 |
| 3 | Fetch Open-Meteo weather by circuit/date | Person 3 |
| 4 | Join laps with stints, drivers, teams, race metadata, and weather | Person 3 |
| 5 | Clean invalid laps and add filtering flags | Person 3 |
| 6 | Derive metrics for tyre degradation, driver consistency, pit windows, and weather bins | Person 3 |
| 7 | Build star-schema fact and dimension tables | Person 3 with Person 2 |
| 8 | Export Tableau-ready CSV files | Person 3 |
| 9 | Connect Tableau workbook to processed CSVs | Person 4 |

---

## 7. Raw data

Raw API data should be stored here:

```text
data/raw/openf1/
data/raw/openmeteo/
```

Suggested raw file naming:

```text
data/raw/openf1/sessions_2023_2025.csv
data/raw/openf1/meetings_2023_2025.csv
data/raw/openf1/laps_<session_key>.csv
data/raw/openf1/stints_<session_key>.csv
data/raw/openf1/weather_<session_key>.csv
data/raw/openmeteo/openmeteo_<session_key>.csv
```

Raw data should not be manually edited. If cleaning is needed, implement it in the pipeline.

---

## 8. Reference data

The circuit coordinate file is stored here:

```text
data/reference/circuit_coordinates.csv
```

Required schema:

```text
circuit_key,circuit_short_name,country_name,location,latitude,longitude,source_note
```

Rules:

- one row per circuit used in the selected race sessions,
- coordinates must be WGS84 decimal degrees,
- prefer exact circuit coordinates over city-center coordinates,
- if a fallback coordinate is used, explain it in `source_note`.

---

## 9. Processed data

Final Tableau-ready files are stored here:

```text
data/processed/
```

Mandatory output files:

```text
data/processed/fact_driver_lap_performance.csv
data/processed/dim_date.csv
data/processed/dim_race.csv
data/processed/dim_circuit.csv
data/processed/dim_driver.csv
data/processed/dim_team.csv
data/processed/dim_tyre_stint.csv
data/processed/dim_weather_context.csv
```

MVP-plus output:

```text
data/processed/fact_pit_stop.csv
```

The processed files should be reproducible by running the pipeline.

---

## 10. Data model summary

### Main fact table

```text
fact_driver_lap_performance
```

Fact-table grain:

```text
One row = one completed lap by one driver in one F1 race session.
```

Main dimensions:

```text
dim_date
dim_race
dim_circuit
dim_driver
dim_team
dim_tyre_stint
dim_weather_context
```

MVP-plus fact table:

```text
fact_pit_stop
```

Detailed modelling documentation is stored in:

```text
docs/source_er_models.md
docs/star_schema.md
docs/data_dictionary.md
```

---

## 11. Required processed-file schemas

### `fact_driver_lap_performance.csv`

```text
fact_lap_id
session_key
meeting_key
date_id
race_id
circuit_id
driver_id
team_id
stint_id
weather_context_id
lap_number
lap_start_time_utc
lap_duration_sec
duration_sector_1_sec
duration_sector_2_sec
duration_sector_3_sec
compound
tyre_age_lap
is_pit_out_lap
is_pit_lap
pit_window_flag
pit_window_relative_lap
valid_racing_lap_flag
invalid_reason
track_temperature_c
air_temperature_c
humidity_pct
rainfall_flag
wind_speed_openf1
position_nearest
lap_time_delta_to_stint_best_sec
lap_time_delta_to_driver_median_sec
lap_time_delta_to_race_median_sec
```

### `dim_date.csv`

```text
date_id,date,year,month,day,season,round_month_label
```

### `dim_race.csv`

```text
race_id,meeting_key,session_key,meeting_name,session_name,session_type,date_start_utc,date_end_utc,year
```

### `dim_circuit.csv`

```text
circuit_id,circuit_key,circuit_short_name,country_name,location,latitude,longitude,coordinate_source_note
```

### `dim_driver.csv`

```text
driver_id,driver_number,full_name,name_acronym,first_name,last_name
```

### `dim_team.csv`

```text
team_id,team_name,team_colour
```

### `dim_tyre_stint.csv`

```text
stint_id,session_key,driver_number,stint_number,compound,lap_start,lap_end,tyre_age_at_start,stint_length_laps
```

### `dim_weather_context.csv`

```text
weather_context_id
session_key
meeting_key
avg_openmeteo_temperature_2m_c
avg_openmeteo_relative_humidity_2m_pct
total_openmeteo_precipitation_mm
total_openmeteo_rain_mm
avg_openmeteo_cloud_cover_pct
avg_openmeteo_wind_speed_10m_kmh
max_openmeteo_wind_gusts_10m_kmh
openmeteo_rain_flag
openf1_track_temp_bin
openf1_weather_category
```

### `fact_pit_stop.csv`

```text
pit_stop_id
session_key
meeting_key
race_id
circuit_id
driver_id
team_id
lap_number
pit_time_utc
lane_duration_sec
stop_duration_sec
pre_pit_avg_lap_delta_sec
post_pit_avg_lap_delta_sec
pit_window_gain_loss_sec
position_before_pit
position_after_pit
position_delta_after_pit
```

---

## 12. Main derived metrics

| Metric | Meaning |
|---|---|
| `tyre_age_lap` | Estimated tyre age on a given lap |
| `lap_time_delta_to_stint_best_sec` | Lap-time loss compared to the best valid lap in the same stint |
| `lap_time_delta_to_driver_median_sec` | Lap-time difference from the driver’s median race lap |
| `lap_time_delta_to_race_median_sec` | Lap-time difference from the race median lap |
| `degradation_slope` | Estimated rate at which lap time worsens as tyre age increases |
| `driver_lap_stddev_sec` | Driver lap-time variability |
| `driver_lap_cv` | Coefficient of variation for driver lap times |
| `pit_window_gain_loss_sec` | Estimated lap-time gain/loss around pit windows |

Detailed formulas are in:

```text
docs/project_handoff.md
docs/data_dictionary.md
```

---

## 13. Cleaning and filtering rules

The pipeline should create:

```text
valid_racing_lap_flag
invalid_reason
```

Set `valid_racing_lap_flag = false` for:

```text
missing lap time
first lap
pit-out lap
pit lap
pit-window lap when the analysis is not about pit windows
clear outlier lap
safety-car/red-flag lap, if race-control filtering is implemented
```

Allowed `invalid_reason` values:

```text
missing_lap_time
first_lap
pit_out_lap
pit_lap
pit_window_lap
outlier_lap
safety_car_or_red_flag
valid
```

---

## 14. Tableau workbook

The Tableau workbook is stored here:

```text
tableau/f1_tyre_weather_dashboard.twbx
```

To open it:

1. Open Tableau.
2. Open `tableau/f1_tyre_weather_dashboard.twbx`.
3. If Tableau asks for data-source locations, reconnect to the CSV files in `data/processed/`.
4. Use the global filters for season, race, circuit, driver, team, compound, weather category, and track-temperature bin.

### Required dashboard sections

| Section | Question | Chart |
|---|---|---|
| 1 | Q1 tyre degradation | Line chart |
| 2 | Q2 soft tyre temperature impact | Box plot or scatter plot |
| 3 | Q3 pit strategy | Bar chart |
| 4 | Q4 driver consistency | Ranked bar chart |
| 5 | Q5 circuit effects | Heatmap |

The dashboard should avoid unrelated visualizations.

---

## 15. Documentation files

| File | Owner | Purpose |
|---|---|---|
| `docs/project_handoff.md` | Person 1 | Detailed implementation contract and project setup |
| `docs/source_er_models.md` | Person 2 | Source-data ER models in 3NF |
| `docs/star_schema.md` | Person 2 | Final star schema and modelling design choices |
| `docs/data_dictionary.md` | Person 2 + Person 3 | Column definitions, metric definitions, cleaning rules |
| `slides/person1_slide_content.md` | Person 1 | Copy-ready slide content for topic, data selection, analytical questions, BI value, and fact grain |
| `slides/presentation.pdf` | Whole group | Final presentation slides |
| `tableau/f1_tyre_weather_dashboard.twbx` | Person 4 | Tableau workbook |

---

## 16. Group responsibilities

| Person | Responsibility | Main outputs |
|---|---|---|
| Person 1 | Topic, data selection, analytical questions, BI justification, project setup | `docs/project_handoff.md`, presentation content for topic/data/questions |
| Person 2 | Data modelling | `docs/source_er_models.md`, `docs/star_schema.md`, modelling slides |
| Person 3 | Data pipeline | `src/`, `notebooks/`, `data/processed/`, pipeline documentation |
| Person 4 | Tableau dashboard and insights | `tableau/f1_tyre_weather_dashboard.twbx`, dashboard screenshots, insights slides |

---

## 17. Definition of done

### Person 1

```text
Topic is clearly described.
Datasets are listed with links.
Analytical questions Q1-Q5 are finalized.
BI justification is written.
Project handoff is available in docs/project_handoff.md.
```

### Person 2

```text
OpenF1 source data is described.
Open-Meteo source data is described.
Source ER models are provided in 3NF.
Star schema is documented.
Design choices are tied to Q1-Q5.
```

### Person 3

```text
Pipeline can be run from the repository.
Raw data can be fetched or regenerated.
Processed CSVs match the schemas in this README.
Cleaning and integration steps are documented.
Tableau can load the processed CSVs without manual editing.
```

### Person 4

```text
Tableau workbook is connected to processed CSVs.
Dashboard contains one section per analytical question.
Filters are included.
Key insights are written in management-style language.
Dashboard screenshots are available for slides.
```

---

## 18. Known limitations

- The analysis shows associations, not causal proof.
- Lap times are affected by fuel load, traffic, safety cars, tyre strategy, team orders, car performance, and driver behavior.
- OpenF1 track weather is track-side and minute-level.
- Open-Meteo provides external ambient/reanalysis weather and may not match the exact circuit microclimate.
- `stop_duration_sec` is only available for part of the period, so `lane_duration_sec` is the safer pit metric.
- Wet and extreme-weather samples may be small.
- Safety-car and red-flag filtering may be approximate if `/race_control` is not implemented.

---

## 19. Notes for future extensions

Possible extensions after the MVP works:

```text
Add position-based pit-stop analysis.
Add race-control filtering for safety cars and red flags.
Add sprint races as a separate dashboard view.
Add 2026 data when complete enough.
Add predictive modelling for degradation or pit timing.
```

Do not start with these extensions before the MVP works.

---

## 20. Quick start for group members

1. Read this `README.md`.
2. Read `docs/project_handoff.md`.
3. Check your responsibility in Section 16.
4. Do not change the fact-table grain.
5. Keep all output CSVs compatible with the schemas in Section 11.
6. Document every important assumption in `docs/data_dictionary.md` or the relevant file in `docs/`.
7. Change the schema as it fits your task, the current one is only a broad-brush approach at an architecture
