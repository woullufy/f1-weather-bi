# Person 1 Slide Content - Topic, Data Selection, and BI Justification

This file is copy-ready content for Person 1's part of the final presentation. It focuses on Assignment 1 tasks 1 and 2, while also giving a short bridge to the modelling, pipeline, dashboard, and insight tasks handled by the rest of the group.

---

## Slide 1 - Topic and Motivation

**Title:** F1 Tyre, Weather and Race Performance BI Project

**Main message:**

We analyse Formula 1 race performance to understand how tyre compound, tyre age, track temperature, weather, pit windows, drivers, teams, and circuits relate to lap-time performance.

**Why this matters:**

From the perspective of a race strategy analyst, tyre choice, stint length, weather adaptation, and pit-window timing are important strategic decisions during a race weekend. A BI dashboard can make these relationships easier to compare across races, teams, drivers, compounds, and circuits.

**Presentation bullets:**

- Domain: Formula 1 race performance and race strategy.
- Focus: lap-time performance under tyre, weather, driver, team, and circuit conditions.
- BI perspective: support strategic comparison, not causal proof.
- Scope: completed Formula 1 race sessions, with OpenF1 as the main performance source and Open-Meteo as external weather context.

---

## Slide 2 - Dataset Overview

| Dataset | Type | Granularity | Main entities | Used for |
|---|---|---|---|---|
| OpenF1 | Public/unofficial F1 data API | session, driver-lap, stint, pit stop, weather timestamp | sessions, meetings, laps, stints, drivers, teams, pit stops, track-side weather | F1 performance, tyre, pit, driver/team, and track-weather data |
| Open-Meteo Historical Weather API | Public weather API | hourly weather by latitude, longitude, and date | ambient weather observations by circuit/date | external ambient weather context for race sessions |
| `circuit_coordinates.csv` | Reference CSV | one row per circuit | circuit location and coordinates | latitude/longitude bridge between F1 circuits and Open-Meteo weather queries |

**Presentation bullets:**

- The datasets are compatible because race sessions can be connected to circuit coordinates, and circuit coordinates can be used to query historical weather.
- OpenF1 provides the lap-level performance facts and track-side weather measurements.
- Open-Meteo adds external ambient weather context by circuit location and race date.
- The reference coordinate file makes the integration reproducible.

---

## Slide 3 - Analytical Questions Q1-Q5

| ID | Analytical question | Main comparison |
|---|---|---|
| Q1 | Which tyre compounds lose lap-time performance fastest? | tyre age vs normalized lap-time delta by compound |
| Q2 | Does higher track temperature make soft tyres worse? | SOFT tyre performance across track-temperature bins |
| Q3 | Which teams gain or lose the most around pit windows? | team-level pit-window gain/loss |
| Q4 | Which drivers have the lowest lap-time variability? | driver consistency after filtering abnormal laps |
| Q5 | Are some circuits more sensitive to tyre wear or weather? | circuit-level tyre/weather sensitivity |

**Presentation bullets:**

- The questions cover multiple BI dimensions: tyre compound, weather, team, driver, circuit, and date/race context.
- Q1, Q2, Q4, and Q5 are the MVP dashboard questions.
- Q3 is MVP-plus because it requires pit-stop data and pit-window calculations.

---

## Slide 4 - BI Justification / Expected Benefits

| Question | Concrete BI benefit |
|---|---|
| Q1 Tyre degradation | Helps compare compounds and identify which tyres lose performance fastest over a stint. |
| Q2 Weather impact | Helps assess whether high track temperature reduces soft-tyre effectiveness. |
| Q3 Pit-stop strategy | Helps compare which teams gain or lose race pace around pit windows. |
| Q4 Driver consistency | Helps identify drivers with stable race pace after filtering abnormal laps. |
| Q5 Circuit effects | Helps identify circuits where tyre wear or weather sensitivity has a stronger performance impact. |

**Presentation bullets:**

- The dashboard is useful for comparing race-strategy patterns across events instead of looking at isolated lap times.
- The BI value comes from combining performance, tyre, weather, and circuit context in one model.
- The analysis supports management-style insight: where performance changes, which factors are associated with it, and where strategy decisions may matter most.

---

## Slide 5 - Fact Table Grain

**Fact grain:**

One row in the main fact table represents one completed lap by one driver in one Formula 1 race session.

**Why this grain is necessary:**

Tyre degradation, tyre age, lap-time variability, track-temperature effects, and pit-window analysis all happen at lap level. A coarser driver-race or race-level fact table would lose the stint progression and lap-by-lap conditions needed for Q1, Q2, Q4, and Q5.

**Main fact and dimensions:**

| Component | Role |
|---|---|
| `fact_driver_lap_performance` | Main lap-level performance fact table |
| `dim_date` | Date and season context |
| `dim_race` | Race/session context |
| `dim_circuit` | Circuit and location context |
| `dim_driver` | Driver context |
| `dim_team` | Team context |
| `dim_tyre_stint` | Compound, stint, and tyre-age context |
| `dim_weather_context` | External weather and weather-category context |

**Presentation bullets:**

- The fact grain was fixed before modelling and pipeline implementation.
- It supports at least one measure per fact, including lap duration, lap-time deltas, tyre age, and track temperature.
- It supports more than three dimensions, including date, race, circuit, driver, team, tyre/stint, and weather context.

---

## Source Notes / Appendix

**OpenF1**

OpenF1 is used as the main F1 performance source. It is a public and unofficial F1 data API that provides race sessions, meetings, drivers, laps, stints, pit stops, session results, and track-side weather.

Source: https://openf1.org/docs/

**Open-Meteo**

Open-Meteo is used as an external weather source. Its Historical Weather API provides hourly historical ambient weather by latitude, longitude, and date range, which is useful for adding race-session weather context.

Source: https://open-meteo.com/en/docs/historical-weather-api

**Circuit coordinates**

The project uses a small local reference CSV to connect F1 race sessions to Open-Meteo weather queries. It stores one row per circuit with latitude and longitude.

Source file: `data/reference/circuit_coordinates.csv`

---

## Assignment Coverage Check

| Assignment task | Current coverage |
|---|---|
| 1. Topic and data selection | Covered by topic motivation, dataset overview, source links, and fixed fact-table grain. |
| 2. BI justification and focus | Covered by Q1-Q5 and the expected-benefits table. |
| 3. Data modelling | Covered at overview level here; detailed star schema is in `docs/star_schema.md`. Source ER and data dictionary completion remain with Person 2. |
| 4. Data processing | Covered at overview level here; pipeline implementation and processed CSV generation remain with Person 3. |
| 5. Data analytics | Cannot be finalized here because the Tableau workbook is not present yet. |
| 6. Key insights | Cannot be finalized until the Tableau dashboard and final visual findings exist. |

---

## Final Repository and Coordination Checklist

### Finalized now by Person 1

- Topic motivation text is ready for one slide.
- Dataset characterization table is ready for the presentation/report.
- Q1-Q5 are stated in slide-ready wording.
- BI justification table gives one concrete benefit per analytical question.
- Fact-table grain explanation is slide-ready.
- Source notes include OpenF1, Open-Meteo, and the circuit coordinate reference file.

### Needs coordination before final submission

| Item | Current status | Reason it cannot be finalized by Person 1 alone |
|---|---|---|
| Final slide deck PDF | `slides/presentation.pdf` is not present. | Requires the whole group to assemble the final deck. |
| Tableau workbook | `tableau/f1_tyre_weather_dashboard.twbx` is not present. | Person 4 must build/export the Tableau dashboard. |
| Dashboard screenshots | Not present. | Blocked until the Tableau workbook exists. |
| Final key insights | Not present. | Must be based on the finished dashboard charts. |
| Source ER models | `docs/source_er_models.md` is empty. | Person 2 owns final ER modelling. |
| Data dictionary | `docs/data_dictionary.md` is empty. | Person 2 and Person 3 own column and metric documentation. |
| Q3 pit-stop fact table | `data/processed/fact_pit_stop.csv` is not present. | Person 3 must implement pit-stop extraction and pit-window metrics, or the group must mark Q3 as MVP-plus/pending. |
| Full 2023-2025 processed scope | Current processed fact rows only cover session `9472`. | Person 3 must expand the pipeline output or the group must explicitly state that the current output is a sample. |

### Consistency checks for Person 1 with the team

- Confirm with Person 2 that the fact grain did not change.
- Confirm with Person 2 that source ER models use OpenF1, Open-Meteo, and the circuit reference file consistently.
- Confirm with Person 2 that the star schema still supports Q1-Q5.
- Confirm with Person 3 whether final processed data covers 2023-2025 or only a sample session.
- Confirm with Person 3 whether `fact_pit_stop.csv` will be delivered for Q3.
- Confirm with Person 4 that the Tableau dashboard has one relevant component per analytical question.
- Confirm final slides include the repository link, limitations, and all six assignment tasks.

---

## Limitations to Mention

- The analysis shows associations, not causal proof.
- Lap times are affected by fuel load, traffic, safety cars, tyre strategy, team orders, car performance, and driver behavior.
- OpenF1 track weather is track-side and minute-level.
- Open-Meteo provides external ambient/reanalysis weather and may not match the exact circuit microclimate.
- Wet and extreme-weather samples may be small.
- Safety-car and red-flag filtering may be approximate if race-control filtering is not implemented.
