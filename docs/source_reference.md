# Source Dataset: Circuit Coordinates (Reference)

## Characterization
A manually maintained CSV file providing the mapping between OpenF1 circuit keys and geographic coordinates required for weather API requests.

- **Type**: Reference File
- **Format**: CSV
- **Entities**: Circuit Reference.

## ER Model (3NF)

```plantuml
@startuml
hide circle
skinparam linetype ortho

entity "CircuitReference" {
  * circuit_key : integer <<PK>>
  --
  circuit_short_name : string
  country_name : string
  location : string
  latitude : float
  longitude : float
  source_note : string
}

@enduml
```

## Attribute Summary
- **Unused columns**: `source_note` (metadata only).
- **Primary focus**: Providing the link between the racing dataset (OpenF1) and the environmental dataset (Open-Meteo).
