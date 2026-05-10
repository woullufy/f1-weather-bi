# BI Data: Star Schema Documentation

## 1. Fact Table Grain
The grain of the **fact_driver_lap_performance** table is defined as:
**One entry corresponds to one completed lap by one driver in a specific Formula 1 race session.**

For the **fact_pit_stop** (MVP+), the grain is:
**One entry corresponds to one pit stop event for a driver during a race session.**

---

## 2. Star Schema Visual Model

```plantuml
@startuml
hide circle
skinparam linetype ortho

entity "fact_driver_lap_performance" as fact_lap <<Fact>> {
  * fact_lap_id : string <<PK>>
  --
  * date_id : string <<FK>>
  * race_id : string <<FK>>
  * circuit_id : string <<FK>>
  * driver_id : string <<FK>>
  * team_id : string <<FK>>
  * stint_id : string <<FK>>
  * weather_context_id : string <<FK>>
  --
  lap_number : integer
  lap_duration_sec : float
  tyre_age_lap : float
  track_temperature_c : float
  lap_time_delta_to_stint_best_sec : float
  valid_racing_lap_flag : boolean
}

entity "dim_date" as dim_date <<Dimension>> {
  * date_id : string <<PK>>
  --
  year : integer
  season : integer
}

entity "dim_race" as dim_race <<Dimension>> {
  * race_id : string <<PK>>
  --
  meeting_name : string
  session_name : string
}

entity "dim_circuit" as dim_circuit <<Dimension>> {
  * circuit_id : string <<PK>>
  --
  circuit_short_name : string
  country_name : string
  latitude : float
  longitude : float
}

entity "dim_driver" as dim_driver <<Dimension>> {
  * driver_id : string <<PK>>
  --
  full_name : string
  name_acronym : string
}

entity "dim_team" as dim_team <<Dimension>> {
  * team_id : string <<PK>>
  --
  team_name : string
  team_colour : string
}

entity "dim_tyre_stint" as dim_stint <<Dimension>> {
  * stint_id : string <<PK>>
  --
  compound : string
  stint_number : integer
}

entity "dim_weather_context" as dim_weather <<Dimension>> {
  * weather_context_id : string <<PK>>
  --
  avg_openmeteo_temperature_2m_c : float
  total_openmeteo_rain_mm : float
  openmeteo_rain_flag : boolean
}

dim_date ||--o{ fact_lap
dim_race ||--o{ fact_lap
dim_circuit ||--o{ fact_lap
dim_driver ||--o{ fact_lap
dim_team ||--o{ fact_lap
dim_stint ||--o{ fact_lap
dim_weather ||--o{ fact_lap
@enduml
```

---

## 3. Design Choices and Justification

### A. Inclusion of `tyre_age_lap` in Fact Table (Targets Q1 & Q5)
- **Choice**: We derive the estimated age of the tyre at the start of every lap during the ETL process.
- **Justification**: This allows for direct correlation between tyre wear and performance loss without requiring window functions in Tableau, ensuring high performance for the "Tyre Age vs Lap Time" line chart.

### B. Denormalizing `track_temperature_c` (Targets Q2)
- **Choice**: Although track temperature is available as a time-series, we aggregate and store it at the lap level in the fact table.
- **Justification**: This supports **Q2** (impact of track temperature on soft tyres) by allowing immediate scatter-plot generation where each point represents a lap's temperature vs its duration.

### C. The `valid_racing_lap_flag` (Targets Q4)
- **Choice**: We implemented a logic to flag "outlier" laps (pit-in/out, first lap, safety cars).
- **Justification**: Essential for **Q4** (driver consistency). Calculating standard deviation or variability on raw lap data would be skewed by pit stops. This choice ensures the BI tool analyzes only "true racing speed."

### D. Weather Context as a Separate Dimension (Targets Q5)
- **Choice**: External weather data (rain, cloud cover) is stored in a separate dimension rather than at the lap level.
- **Justification**: Since ambient weather changes slowly compared to lap times, storing it in a dimension reduces the width of the fact table while still allowing users to filter the entire race by "Rainy" or "Sunny" conditions for **Q5**.
