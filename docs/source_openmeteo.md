# Source Dataset: Open-Meteo Historical Weather API

## Characterization
The Open-Meteo API provides historical weather data (reanalysis) based on geographic coordinates. It is used to supplement track-side data with broader ambient weather context.

- **Type**: REST API
- **Format**: JSON (converted to hourly CSV for processing)
- **Entities**: Hourly Weather Report.

## ER Model (3NF)

```plantuml
@startuml
hide circle
skinparam linetype ortho

entity "Location" {
  * latitude : float <<PK>>
  * longitude : float <<PK>>
  --
  elevation : float
  timezone : string
}

entity "HourlyWeather" {
  * latitude : float <<PK>>
  * longitude : float <<PK>>
  * time : datetime <<PK>>
  --
  temperature_2m : float
  relative_humidity_2m : float
  precipitation : float
  rain : float
  cloud_cover : float
  wind_speed_10m : float
  wind_gusts_10m : float
}

Location ||--o{ HourlyWeather
@enduml
```

## Attribute Summary
- **Unused columns**: `elevation`, `timezone`.
- **Primary focus**: Ambient humidity, precipitation, and wind conditions to contextualize race performance.
