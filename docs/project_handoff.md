# F1 Tyre, Weather and Race Performance BI Project - 10/10 Implementation Handoff

**Purpose:** This document is the concrete project base for the rest of the group. It fixes the project decisions, modelling contract, API/data contract, output file contract, derived metric definitions, dashboard expectations, and teammate handoffs. It is written so that Person 2 can model, Person 3 can implement, and Person 4 can design the dashboard in parallel.

**Important boundary:** This is not the final Person 1 write-up. Person 1 can later polish the narrative, BI justification, and presentation wording. This file is mainly the technical and analytical contract for the team.

---

## 1. Fixed project decisions

| Decision | Final choice |
|---|---|
| Project topic | How tyre compound, tyre age, track/weather conditions, pit windows, drivers, teams, and circuits relate to F1 race lap-time performance. |
| Main domain | Formula 1 race performance and BI analysis. |
| Primary source dataset | OpenF1 API. |
| Secondary source dataset | Open-Meteo Historical Weather API. |
| Reference dataset | `circuit_coordinates.csv`, one row per circuit, manually verified. |
| Main analysis scope | 2023-2025 completed Formula 1 **Race** sessions only. |
| Excluded from MVP | Practice, qualifying, sprint qualifying, sprint races, testing, telemetry/car data, team radio, overtakes. |
| Main fact-table grain | **One row = one completed lap by one driver in one F1 race session.** |
| Mandatory dashboard questions | Q1-Q5 listed below. |
| Mandatory output format | CSV files that can be loaded into Tableau. |
| Primary track-weather source | OpenF1 `/weather`, because it provides track-side minute-level weather including track temperature. |
| Open-Meteo role | External ambient weather context at circuit/session level, not a replacement for OpenF1 track temperature. |

**Why the lap-level grain is fixed:** The questions are about tyre degradation, tyre age, lap-time variability, track temperature, and pit windows. A driver-race fact table would be too coarse because it would lose the lap-by-lap tyre age and stint progression needed for Q1 and Q2.

---

## 2. Assignment fit checkpoint

| Assignment requirement | Project contract |
|---|---|
| Domain with public data | Formula 1 race performance using OpenF1 and Open-Meteo. |
| At least two compatible datasets | OpenF1 race/session/lap/stint/pit/weather data + Open-Meteo historical weather by circuit coordinates and date/time. |
| Clear fact entry | One completed lap by one driver in one race session. |
| At least one measure per fact | Lap duration, lap-time deltas, tyre age, track temperature, air temperature, humidity, wind speed, pit window flags. |
| At least three dimensions | Date, Race, Circuit, Driver, Team, Tyre/Stint, Weather Context. |
| Source data modelling possible | OpenF1 entities and Open-Meteo weather observations can be represented as 3NF source models. |
| Star schema possible | Main `fact_driver_lap_performance` plus dimensions and a small `fact_pit_stop` for Q3. |
| Automatic pipeline possible | Python API extraction, cleaning, integration, star-schema export. |
| Tableau dashboard possible | One dashboard section per analytical question. |

---

## 3. Analytical questions and required data

| ID | Question | Required fact grain | Main measures | Main dimensions | Mandatory chart |
|---|---|---|---|---|---|
| Q1 | **Tyre degradation:** Which tyre compounds lose lap-time performance fastest? | driver-lap | `lap_time_delta_to_stint_best_sec`, `tyre_age_lap`, `degradation_slope` | compound, stint, circuit, driver, team | Line chart: tyre age vs normalized lap-time delta by compound |
| Q2 | **Weather impact:** Does higher track temperature make soft tyres worse? | driver-lap | `track_temperature_c`, `lap_time_delta_to_stint_best_sec`, `degradation_slope_soft` | track temp bin, compound, circuit, race | Box/scatter: SOFT degradation by track temperature bin |
| Q3 | **Pit-stop strategy:** Which teams gain or lose the most around pit windows? | pit stop + nearby laps | `lane_duration_sec`, `pit_window_gain_loss_sec`, optional `position_delta_after_pit` | team, driver, race, circuit | Bar chart: team vs avg pit-window gain/loss |
| Q4 | **Driver consistency:** Which drivers have the lowest lap-time variability? | driver-lap aggregated to driver-race/season | `driver_lap_stddev_sec`, `driver_lap_cv`, valid lap count | driver, team, season, circuit | Ranked bar chart: driver consistency |
| Q5 | **Circuit effects:** Are some circuits more sensitive to tyre wear or weather? | driver-lap aggregated to circuit | `degradation_slope`, `weather_sensitivity_delta_sec` | circuit, compound, weather bin | Heatmap: circuit vs compound/weather sensitivity |

---

## 4. Dataset and endpoint contract

### 4.1 Dataset A - OpenF1 API

**Source URL:** https://openf1.org/docs/  
**Use:** Main performance, race operations, tyre, pit, position, and track-weather data.  
**Format:** JSON by default; CSV is also supported by the API.  
**Historical scope:** Free historical data from 2023 onward.

| Endpoint | Build priority | Use | Join keys | Main fields |
|---|---:|---|---|---|
| `/sessions` | 1 | Identify race sessions and time windows | `session_key`, `meeting_key` | `session_key`, `meeting_key`, `session_type`, `session_name`, `date_start`, `date_end`, `year`, `circuit_key`, `circuit_short_name`, `country_name`, `location` |
| `/meetings` | 1 | Race/circuit/event metadata | `meeting_key` | `meeting_key`, `meeting_name`, `year`, `circuit_key`, `circuit_short_name`, `country_name`, `location` |
| `/drivers` | 1 | Driver and team dimensions | `session_key`, `driver_number` | `driver_number`, `full_name`, `name_acronym`, `team_name`, `team_colour`, `session_key` |
| `/laps` | 1 | Main lap performance fact data | `session_key`, `meeting_key`, `driver_number`, `lap_number` | `lap_duration`, `date_start`, `is_pit_out_lap`, sector durations, speed fields |
| `/stints` | 1 | Tyre compound and tyre age | `session_key`, `driver_number`, `lap_number BETWEEN lap_start AND lap_end` | `stint_number`, `compound`, `lap_start`, `lap_end`, `tyre_age_at_start` |
| `/weather` | 1 | Track-side weather and track temperature | `session_key`, nearest timestamp | `date`, `air_temperature`, `track_temperature`, `humidity`, `rainfall`, `pressure`, `wind_speed`, `wind_direction` |
| `/pit` | 2 | Pit stop and pit-window analysis | `session_key`, `driver_number`, `lap_number` | `date`, `lap_number`, `lane_duration`, `stop_duration` |
| `/position` | 2 | Position before/after pit windows | `session_key`, `driver_number`, nearest timestamp | `date`, `position` |
| `/session_result` | 2 | Final result and DNF/DNS/DSQ flags | `session_key`, `driver_number` | `position`, `dnf`, `dns`, `dsq`, `number_of_laps`, `gap_to_leader` |
| `/race_control` | Optional | Better filtering of safety-car/red-flag laps | `session_key`, `lap_number` | `category`, `flag`, `message`, `lap_number` |

**Do not use in MVP:** `/car_data`, `/location`, `/team_radio`, `/overtakes`, championship endpoints. They are interesting but unnecessary for the analytical questions and increase complexity.

### 4.2 Dataset B - Open-Meteo Historical Weather API

**Source URL:** https://open-meteo.com/en/docs/historical-weather-api  
**Use:** External ambient weather context for each circuit/session.  
**Endpoint:** `/v1/archive`  
**Required parameters:** `latitude`, `longitude`, `start_date`, `end_date`, and selected `hourly` variables.  
**Important:** Open-Meteo gives ambient/reanalysis weather. It does not give F1 track surface temperature.

| Variable | Use in project | Aggregation |
|---|---|---|
| `temperature_2m` | Ambient temperature context | mean over race session window or race day |
| `relative_humidity_2m` | Humidity context | mean |
| `precipitation` | Wet/dry context | sum |
| `rain` | Wet/dry context | sum |
| `cloud_cover` | Weather context | mean |
| `wind_speed_10m` | Wind context | mean/max |
| `wind_direction_10m` | Wind context | circular mean or keep dominant value if implemented |
| `wind_gusts_10m` | Windy-session flag | max |
| `pressure_msl` or `surface_pressure` | Optional pressure context | mean |

### 4.3 Dataset C - `circuit_coordinates.csv`

**Purpose:** Required because Open-Meteo queries need latitude and longitude.

**Location in repo:** `data/reference/circuit_coordinates.csv`

**Schema:**

```text
circuit_key,circuit_short_name,country_name,location,latitude,longitude,source_note
```

**Rules:**

- One row per circuit used in 2023-2025 race sessions.
- Coordinates must be WGS84 decimal degrees.
- Prefer circuit coordinates over city-center coordinates.
- If exact circuit coordinates cannot be found quickly, use a documented fallback and write it in `source_note`.

---

## 5. Minimum viable product vs optional extensions

### MVP - must be implemented

The project is considered functional if these are completed:

1. Fetch OpenF1 race sessions for 2023-2025 where `session_type == "Race"`.
2. Fetch OpenF1 meetings, drivers, laps, stints, and weather.
3. Load `circuit_coordinates.csv`.
4. Fetch Open-Meteo hourly weather for each race session location/date.
5. Build `fact_driver_lap_performance` and the mandatory dimensions.
6. Calculate Q1, Q2, Q4, and Q5 metrics.
7. Build dashboard components for Q1, Q2, Q4, Q5.
8. Include Open-Meteo data in `dim_weather_context` so the project clearly uses two datasets.

### MVP-plus - should be implemented if possible

1. Fetch OpenF1 `/pit` and create `fact_pit_stop`.
2. Calculate `pit_window_gain_loss_sec` using laps before/after a pit stop.
3. Add Q3 dashboard component.

### Optional extensions - only if everything above works

1. Use `/position` to compute position before/after pit stops.
2. Use `/race_control` to remove safety-car/red-flag laps more precisely.
3. Add 2026 data only if the group explicitly wants current-season examples.
4. Add sprint races as a separate analysis, not mixed into the main race analysis.

---

## 6. Integration contract

### 6.1 Core joins

| Join | Type | Keys/rule | Notes |
|---|---|---|---|
| sessions -> meetings | many-to-one | `meeting_key` | Adds race/event/circuit metadata. |
| sessions -> drivers | one-to-many | `session_key` | Drivers and teams are session-specific because driver/team membership can change. |
| laps -> drivers | many-to-one | `session_key`, `driver_number` | Adds driver/team info to each lap. |
| laps -> stints | many-to-one | `session_key`, `driver_number`, `lap_number BETWEEN lap_start AND lap_end` | Adds compound and tyre age. |
| laps -> OpenF1 weather | many-to-one nearest-time | same `session_key`; nearest previous weather timestamp to `lap.date_start` | Track temperature is lap-level approximation. |
| laps -> pit | left join | `session_key`, `driver_number`, `lap_number` | Marks pit laps. |
| sessions -> coordinates | many-to-one | prefer `circuit_key`; fallback `circuit_short_name + country_name` | Required for Open-Meteo. |
| sessions -> Open-Meteo | many-to-one | lat/lon + date range from session start/end | External ambient weather context. |

### 6.2 Weather integration rule

For each race session:

1. Use OpenF1 `date_start` and `date_end` as the target race-session window.
2. Use `circuit_coordinates.csv` for latitude and longitude.
3. Query Open-Meteo `/v1/archive` with hourly variables.
4. Keep all timestamps in UTC internally.
5. Aggregate Open-Meteo to session level for `dim_weather_context`.
6. Join OpenF1 `/weather` to laps by nearest previous timestamp inside the same `session_key`.
7. Use OpenF1 `track_temperature` for Q2.

---

## 7. Output file contract for Person 3

All files go into `data/processed/`. Person 4 should be able to load these directly into Tableau.

### 7.1 Mandatory output files

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

### 7.2 MVP-plus output file

```text
data/processed/fact_pit_stop.csv
```

### 7.3 Fact table schema - `fact_driver_lap_performance.csv`

One row = one completed lap by one driver in one race session.

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

### 7.4 Dimension schemas

#### `dim_date.csv`

```text
date_id,date,year,month,day,season,round_month_label
```

#### `dim_race.csv`

```text
race_id,meeting_key,session_key,meeting_name,session_name,session_type,date_start_utc,date_end_utc,year
```

#### `dim_circuit.csv`

```text
circuit_id,circuit_key,circuit_short_name,country_name,location,latitude,longitude,coordinate_source_note
```

#### `dim_driver.csv`

```text
driver_id,driver_number,full_name,name_acronym,first_name,last_name
```

#### `dim_team.csv`

```text
team_id,team_name,team_colour
```

#### `dim_tyre_stint.csv`

```text
stint_id,session_key,driver_number,stint_number,compound,lap_start,lap_end,tyre_age_at_start,stint_length_laps
```

#### `dim_weather_context.csv`

One row per race session. It contains Open-Meteo session-level ambient weather and OpenF1-derived weather bins.

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

### 7.5 MVP-plus fact table schema - `fact_pit_stop.csv`

One row = one pit stop by one driver in one race session.

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

## 8. Derived metric definitions

### 8.1 Tyre age

```text
tyre_age_lap = tyre_age_at_start + (lap_number - lap_start)
```

Example: if a stint starts at lap 10 with `tyre_age_at_start = 2`, then lap 10 has tyre age 2, lap 11 has tyre age 3, etc.

### 8.2 Normalized lap-time deltas

Use only valid racing laps for baselines.

```text
lap_time_delta_to_stint_best_sec = lap_duration_sec - min(lap_duration_sec within same session_key, driver_number, stint_number)
```

```text
lap_time_delta_to_driver_median_sec = lap_duration_sec - median(lap_duration_sec within same session_key, driver_number)
```

```text
lap_time_delta_to_race_median_sec = lap_duration_sec - median(lap_duration_sec within same session_key)
```

### 8.3 Degradation slope

For each driver-stint with enough valid laps:

```text
x = tyre_age_lap
y = lap_time_delta_to_stint_best_sec
degradation_slope = slope of y over x
```

Minimum rule:

```text
Only calculate slope if the stint has at least 5 valid racing laps.
```

Interpretation:

```text
larger positive slope = lap times become slower faster = stronger degradation
```

### 8.4 Driver consistency

Calculate per driver-race first, then aggregate to driver-season or whole scope.

```text
driver_lap_stddev_sec = stddev(lap_time_delta_to_driver_median_sec for valid racing laps)
```

```text
driver_lap_cv = stddev(lap_duration_sec) / mean(lap_duration_sec)
```

Minimum rule:

```text
Only include driver-race groups with at least 10 valid racing laps.
Only rank drivers with at least 150 valid racing laps across the selected scope.
```

### 8.5 Pit-window gain/loss

Mandatory simple version:

```text
pre_pit_avg_lap_delta_sec = avg(lap_time_delta_to_driver_median_sec for laps -3 to -1 before pit)
post_pit_avg_lap_delta_sec = avg(lap_time_delta_to_driver_median_sec for laps +2 to +4 after pit)
pit_window_gain_loss_sec = pre_pit_avg_lap_delta_sec - post_pit_avg_lap_delta_sec
```

Interpretation:

```text
positive value = post-pit laps are faster than pre-pit laps
negative value = post-pit laps are not faster or the pit window did not help lap pace
```

Why use +2 to +4 after pit instead of +1 to +3? The first lap after a pit stop can be an out lap and may be distorted.

Optional position version:

```text
position_delta_after_pit = position_before_pit - position_after_pit
```

Positive value means the driver gained positions after the pit window.

### 8.6 Weather categories and bins

Use these bins consistently in pipeline and Tableau.

```text
track_temp_bin:
- Cold/low track temp: < 30 C
- Medium track temp: 30-39.9 C
- High track temp: 40-49.9 C
- Very high track temp: >= 50 C
```

```text
openf1_weather_category:
- Wet: rainfall_flag == 1 at any point in session or Open-Meteo rain > 0
- Hot dry: no rain and avg track temperature >= 40 C
- Normal dry: no rain and avg track temperature < 40 C
- Windy: max Open-Meteo gust >= 40 km/h or high wind bin
```

If a session fits multiple labels, priority order:

```text
Wet > Windy > Hot dry > Normal dry
```

---

## 9. Data cleaning and filtering rules

### 9.1 Valid racing lap flag

Set `valid_racing_lap_flag = false` if any of the following apply:

```text
lap_duration_sec is missing
lap_number == 1
is_pit_out_lap == true
is_pit_lap == true
lap is within pit window and analysis is not about pit windows
lap_duration_sec is outside driver-race median +/- 3 * driver-race stddev
```

If `/race_control` is implemented, also exclude:

```text
safety car laps
virtual safety car laps
red flag laps
formation or restart laps, if identifiable
```

### 9.2 Invalid reason values

Use these exact labels:

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

### 9.3 Compound handling

Keep these compounds as normal categories:

```text
SOFT, MEDIUM, HARD, INTERMEDIATE, WET
```

For Q1 and Q2, default to dry compounds only:

```text
SOFT, MEDIUM, HARD
```

For wet-weather context, `INTERMEDIATE` and `WET` can be shown separately or excluded from dry-tyre degradation comparisons.

---

## 10. Source ER model starter for Person 2

Person 2 should refine this into clean 3NF diagrams. This starter gives the intended entities and relationships.

### 10.1 OpenF1 source model starter

```text
Meeting(
    meeting_key PK,
    meeting_name,
    year,
    country_name,
    location,
    circuit_key,
    circuit_short_name
)

Session(
    session_key PK,
    meeting_key FK,
    session_name,
    session_type,
    date_start,
    date_end,
    year
)

DriverSession(
    session_key FK,
    driver_number,
    full_name,
    name_acronym,
    team_name,
    team_colour,
    PRIMARY KEY(session_key, driver_number)
)

Lap(
    session_key FK,
    meeting_key FK,
    driver_number,
    lap_number,
    date_start,
    lap_duration,
    duration_sector_1,
    duration_sector_2,
    duration_sector_3,
    is_pit_out_lap,
    PRIMARY KEY(session_key, driver_number, lap_number)
)

Stint(
    session_key FK,
    meeting_key FK,
    driver_number,
    stint_number,
    compound,
    lap_start,
    lap_end,
    tyre_age_at_start,
    PRIMARY KEY(session_key, driver_number, stint_number)
)

PitStop(
    session_key FK,
    meeting_key FK,
    driver_number,
    lap_number,
    date,
    lane_duration,
    stop_duration,
    PRIMARY KEY(session_key, driver_number, lap_number)
)

TrackWeatherObservation(
    session_key FK,
    meeting_key FK,
    date,
    air_temperature,
    track_temperature,
    humidity,
    rainfall,
    pressure,
    wind_speed,
    wind_direction,
    PRIMARY KEY(session_key, date)
)

SessionResult(
    session_key FK,
    meeting_key FK,
    driver_number,
    position,
    dnf,
    dns,
    dsq,
    number_of_laps,
    gap_to_leader,
    PRIMARY KEY(session_key, driver_number)
)
```

### 10.2 Open-Meteo source model starter

```text
WeatherLocation(
    location_id PK,
    circuit_key,
    latitude,
    longitude,
    timezone
)

OpenMeteoHourlyObservation(
    location_id FK,
    observation_time,
    temperature_2m,
    relative_humidity_2m,
    precipitation,
    rain,
    cloud_cover,
    wind_speed_10m,
    wind_direction_10m,
    wind_gusts_10m,
    pressure_msl,
    PRIMARY KEY(location_id, observation_time)
)
```

### 10.3 Design choices Person 2 should explicitly mention

- We model OpenF1 source data in separate entities because meetings, sessions, laps, stints, pit stops, drivers, and weather observations have different natural keys.
- We use a lap-level fact table because tyre degradation and driver consistency require lap-level observations.
- We keep weather both as fact-level numeric fields and as a weather-context dimension because Tableau needs both precise measures and easy categories.
- We keep pit stops as a separate fact table in the MVP-plus version because pit stops have a different grain from laps.

---

## 11. Star schema contract for Person 2 and Person 3

### 11.1 Main star schema

```text
fact_driver_lap_performance
    -> dim_date via date_id
    -> dim_race via race_id
    -> dim_circuit via circuit_id
    -> dim_driver via driver_id
    -> dim_team via team_id
    -> dim_tyre_stint via stint_id
    -> dim_weather_context via weather_context_id
```

### 11.2 Secondary star for pit stops

```text
fact_pit_stop
    -> dim_race via race_id
    -> dim_circuit via circuit_id
    -> dim_driver via driver_id
    -> dim_team via team_id
```

### 11.3 Tableau relationship advice

In Tableau, relate tables using these keys:

```text
fact_driver_lap_performance.date_id = dim_date.date_id
fact_driver_lap_performance.race_id = dim_race.race_id
fact_driver_lap_performance.circuit_id = dim_circuit.circuit_id
fact_driver_lap_performance.driver_id = dim_driver.driver_id
fact_driver_lap_performance.team_id = dim_team.team_id
fact_driver_lap_performance.stint_id = dim_tyre_stint.stint_id
fact_driver_lap_performance.weather_context_id = dim_weather_context.weather_context_id
fact_pit_stop.team_id = dim_team.team_id
fact_pit_stop.race_id = dim_race.race_id
```

---

## 12. Pipeline plan for Person 3

### 12.1 Recommended project files

```text
src/config.py
src/fetch_openf1.py
src/fetch_openmeteo.py
src/load_reference.py
src/clean_laps.py
src/join_stints_weather.py
src/derive_metrics.py
src/build_dimensions.py
src/build_facts.py
src/export_tableau_csv.py
notebooks/01_pipeline_exploration.ipynb
```

### 12.2 Pipeline stages

| Stage | Input | Output | Definition of done |
|---|---|---|---|
| 1. Fetch sessions | OpenF1 `/sessions` | raw sessions JSON/CSV | Only 2023-2025 Race sessions kept. |
| 2. Fetch base OpenF1 data | session list | raw meetings, drivers, laps, stints, weather | One raw file per endpoint or one combined file per endpoint. |
| 3. Load circuit coordinates | `circuit_coordinates.csv` | coordinate table | All race sessions have lat/lon. |
| 4. Fetch Open-Meteo | coordinates + session dates | raw Open-Meteo hourly data | One session-level aggregation available per race. |
| 5. Join laps/stints/weather | raw OpenF1 data | enriched lap table | Every valid lap has compound, tyre age, and nearest weather. |
| 6. Clean and flag laps | enriched lap table | cleaned lap table | Invalid laps are flagged with exact reason. |
| 7. Derive metrics | cleaned lap table | metric-ready lap table | Normalized deltas and degradation inputs exist. |
| 8. Build dimensions | metric-ready lap table | dimension CSVs | IDs are stable and no duplicate primary keys. |
| 9. Build fact tables | metric-ready lap table + pit data | fact CSVs | Fact rows link to all dimension keys. |
| 10. Export for Tableau | processed tables | CSV output folder | Tableau can load all CSVs without manual edits. |

### 12.3 Implementation priority

```text
Priority 1: sessions, meetings, drivers, laps, stints, OpenF1 weather
Priority 2: circuit coordinates, Open-Meteo session weather
Priority 3: cleaning flags and normalized lap-time deltas
Priority 4: dimension and fact CSV export
Priority 5: pit stop fact table
Priority 6: position endpoint and race-control filtering
```

### 12.4 Fallbacks to avoid getting stuck

| Problem | Fallback |
|---|---|
| Open-Meteo hourly join is annoying | Aggregate Open-Meteo by race day/session and store only in `dim_weather_context`. |
| Circuit coordinates are missing | Fill manually in `circuit_coordinates.csv` and document `source_note`. |
| Safety-car filtering is too hard | Use statistical outlier filtering and mention limitation. |
| Position endpoint is hard to align | For Q3 use lap-time gain/loss, not position gain/loss. |
| `stop_duration` missing | Use `lane_duration_sec`, because it is available more consistently. |
| Too much data | Start with 2024 only, then expand to 2023 and 2025 after the pipeline works. |

---

## 13. Dashboard blueprint for Person 4

### 13.1 Required global filters

```text
Season/year
Race/Grand Prix
Circuit
Driver
Team
Tyre compound
Weather category
Track temperature bin
Valid racing laps only: true/false
```

### 13.2 Mandatory dashboard components

| Section | Question | Chart | Required fields |
|---|---|---|---|
| 1 | Q1 tyre degradation | Line chart | `tyre_age_lap`, avg `lap_time_delta_to_stint_best_sec`, `compound` |
| 2 | Q2 soft tyre temperature | Box plot or scatter | `track_temp_bin`, `track_temperature_c`, SOFT-only `degradation_slope` or lap delta |
| 3 | Q3 pit strategy | Bar chart | `team_name`, avg `pit_window_gain_loss_sec`, avg `lane_duration_sec` |
| 4 | Q4 driver consistency | Ranked bar chart | `full_name`, `driver_lap_stddev_sec` or `driver_lap_cv` |
| 5 | Q5 circuit effects | Heatmap | `circuit_short_name`, `compound` or `weather_category`, `degradation_slope` |

### 13.3 Suggested layout

```text
Top row: project title + filters
Row 1: Q1 tyre degradation line chart
Row 2: Q2 weather/track-temperature impact + Q4 driver consistency ranking
Row 3: Q3 pit-window team comparison + Q5 circuit heatmap
Bottom/side: short insight text boxes
```

### 13.4 Insight template

For each question, Person 4 should write:

```text
Finding: What changed or stood out?
Evidence: Which chart and metric supports it?
Interpretation: Why does it matter for race strategy/performance?
Caveat: What limitation should be kept in mind?
```

---

## 14. Handoff definitions of done

### Person 2 - Data modelling

Person 2 is done when they provide:

```text
1. Structured description of OpenF1 source data.
2. Structured description of Open-Meteo source data.
3. OpenF1 3NF ER model.
4. Open-Meteo 3NF ER model.
5. Final star schema diagram.
6. Short explanation of design choices tied to Q1-Q5.
```

They should not change the fact grain unless the whole group agrees.

### Person 3 - Pipeline

Person 3 is done when they provide:

```text
1. Reusable Python/Jupyter pipeline.
2. Raw data fetching or clear instructions for fetching.
3. Automatic cleaning and integration.
4. Processed CSV files matching the output contract.
5. README section explaining how to run the pipeline.
6. Notes about cleaning/integration issues and fallbacks used.
```

They should not manually edit processed CSVs except for the reference coordinate file.

### Person 4 - Tableau and insights

Person 4 is done when they provide:

```text
1. Tableau workbook connected to processed CSVs.
2. Dashboard with one component per analytical question.
3. Dashboard filters listed above.
4. Key insights written in management-style language.
5. Screenshots or export-ready dashboard views for slides.
```

They should not add dashboard charts unrelated to Q1-Q5.

---

## 15. Repository structure

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

---

## 16. README checklist

The final repository README should include:

```text
Project topic
Analytical questions Q1-Q5
Data sources and links
How to install dependencies
How to run the pipeline
Where raw data is stored
Where processed CSVs are stored
How to open the Tableau workbook
Known limitations
Group member responsibilities
```

---

## 17. Known limitations to mention later in the presentation

- The analysis shows associations, not causal proof.
- Lap times are affected by fuel load, traffic, safety cars, tyre strategy, team orders, car performance, and driver behavior.
- OpenF1 track weather is track-side and minute-level; Open-Meteo is external ambient/reanalysis weather and may not match exact circuit microclimate.
- `stop_duration` is only available from part of the data period, so `lane_duration_sec` is the safer pit metric.
- Wet and extreme-weather samples may be small.
- Some filtering choices, especially safety-car filtering, may be approximate if `/race_control` is not implemented.

---

## 18. Person 1 follow-up tasks later

These are not blocking the others, but Person 1 should polish them later for the final presentation:

```text
1. Write a clean 1-slide topic motivation.
2. Write a structured dataset-characterization table in presentation style.
3. Strengthen BI justification in management/strategy language.
4. Add short source descriptions with citations/links.
5. Coordinate with Person 2 so the final ER/star-schema wording matches the slides.
```

---

## 19. Source references

- Assignment description PDF: University of Vienna, Business Intelligence 1, Assignment 1 SS2026.
- OpenF1 documentation: https://openf1.org/docs/
- Open-Meteo Historical Weather API documentation: https://open-meteo.com/en/docs/historical-weather-api
