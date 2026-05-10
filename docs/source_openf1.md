# Source Dataset: OpenF1 API

## Characterization
The OpenF1 API provides real-time and historical data from Formula 1 sessions, including lap times, tyre stints, and track-side weather measurements.

- **Type**: REST API
- **Format**: JSON (converted to CSV for processing)
- **Entities**: Meetings, Sessions, Drivers, Laps, Stints, Weather.

## ER Model (3NF)

```plantuml
@startuml
hide circle
skinparam linetype ortho

entity "Meeting" {
  * meeting_key : integer <<PK>>
  --
  meeting_name : string
  meeting_official_name : string
  location : string
  country_key : integer
  country_code : string
  country_name : string
  circuit_key : integer
  circuit_short_name : string
  date_start : datetime
  gmt_offset : string
  year : integer
}

entity "Session" {
  * session_key : integer <<PK>>
  --
  * meeting_key : integer <<FK>>
  session_name : string
  session_type : string
  date_start : datetime
  date_end : datetime
  gmt_offset : string
}

entity "Driver" {
  * session_key : integer <<PK>>
  * driver_number : integer <<PK>>
  --
  broadcast_name : string
  full_name : string
  name_acronym : string
  first_name : string
  last_name : string
  team_name : string
  team_colour : string
}

entity "Lap" {
  * session_key : integer <<PK>>
  * driver_number : integer <<PK>>
  * lap_number : integer <<PK>>
  --
  date_start : datetime
  lap_duration : float
  duration_sector_1 : float
  duration_sector_2 : float
  duration_sector_3 : float
  i1_speed : integer
  i2_speed : integer
  st_speed : integer
  is_pit_out_lap : boolean
}

entity "Stint" {
  * session_key : integer <<PK>>
  * driver_number : integer <<PK>>
  * stint_number : integer <<PK>>
  --
  compound : string
  tyre_age_at_start : integer
  lap_start : integer
  lap_end : integer
}

entity "Weather" {
  * session_key : integer <<PK>>
  * date : datetime <<PK>>
  --
  track_temperature : float
  air_temperature : float
  humidity : float
  pressure : float
  rainfall : integer
  wind_direction : integer
  wind_speed : float
}

Meeting ||--o{ Session
Session ||--o{ Driver
Session ||--o{ Lap
Session ||--o{ Stint
Session ||--o{ Weather
Driver ||--o{ Lap
Driver ||--o{ Stint
@enduml
```

## Attribute Summary
- **Unused columns**: `country_key`, `country_code`, `i1_speed`, `i2_speed`, `st_speed`, `pressure`, `wind_direction`.
- **Primary focus**: Performance metrics (lap times, stint length) and track conditions (temperature).
