# Dashboard Plan

## Current dashboard status

Current Tableau file:

- `tableau/f1_tyre_weather_dashboard.twbx`

Current dashboard tab:

- `F1 Dashboard Overview`

Current worksheet tabs:

- `Q1 Tyre Degradation`
- `Q2 Temperature Impact`
- `Q4 Driver Consistency`
- `Q5 Circuit Effects`

The dashboard currently includes:

- Tyre degradation by compound
- Driver consistency ranking
- Soft tyre performance by track temperature
- Circuit and compound sensitivity heatmap
- Dashboard limitation note

## Current data status

Current available files:

- `fact_driver_lap_performance.csv`
- `dim_date.csv`
- `dim_race.csv`
- `dim_circuit.csv`
- `dim_driver.csv`
- `dim_team.csv`
- `dim_tyre_stint.csv`
- `dim_weather_context.csv`

The current fact table contains one race session:

- Bahrain Grand Prix 2024
- Session key: 9472
- 20 drivers
- 10 teams
- Compounds currently available: SOFT and HARD
- One circuit: Sakhir
- One main track temperature value

This means that while Q1 and Q4 can already be visualized usefully, Q2 and Q5 are prepared as placeholders because they require more weather and circuit variation. Q3 pit strategy is currently not included because no pit-stop fact table is available.

## Tableau data model

Central fact table:

- `fact_driver_lap_performance.csv`

Dimension tables:

- `dim_date.csv`
- `dim_race.csv`
- `dim_circuit.csv`
- `dim_driver.csv`
- `dim_team.csv`
- `dim_tyre_stint.csv`
- `dim_weather_context.csv`

Relationships used in Tableau:

- `fact_driver_lap_performance.date_id = dim_date.date_id`
- `fact_driver_lap_performance.race_id = dim_race.race_id`
- `fact_driver_lap_performance.circuit_id = dim_circuit.circuit_id`
- `fact_driver_lap_performance.driver_id = dim_driver.driver_id`
- `fact_driver_lap_performance.team_id = dim_team.team_id`
- `fact_driver_lap_performance.stint_id = dim_tyre_stint.stint_id`
- `fact_driver_lap_performance.weather_context_id = dim_weather_context.weather_context_id`

In Tableau, all dimension tables are connected directly to the central fact table. This keeps the model as a star schema rather than a snowflake-style model.

## Notes on Tableau setup

Some CSV files required manual adjustment in Tableau:

- Field separator was set to comma where needed.
- Some fields had to be manually matched in relationships.
- `dim_weather_context.csv` did not initially show all headers correctly in Tableau, so weather fields were checked and renamed for readability where useful.
- The weather context relationship was created using the weather context ID field.

## Dashboard filters and legends

The dashboard currently includes:

- Compound filter
- Compound legend
- Team legend
- Color legend for circuit/compound sensitivity

The `valid_racing_lap_flag` filter is used internally and set to `True`, but it should normally stay hidden from the audience because invalid or non-racing laps should not be included in the analysis.

## Dashboard components

### Q1 — Tyre degradation

Question:

Which tyre compounds lose lap-time performance fastest?

Chart:

Line chart showing tyre age against average lap-time delta to the best lap in the same stint.

Fields:

- Columns: `tyre_age_lap`
- Rows: average `lap_time_delta_to_stint_best_sec`
- Color: `compound`
- Filter: `valid_racing_lap_flag = True`

Status:

Built and usable as a prototype analysis.

Current observation:

In the current Bahrain GP 2024 data, both hard and soft tyres show increasing lap-time loss as tyre age increases. The soft tyre line is more volatile and includes a visible spike around tyre age 9, which may be an outlier.

### Q2 — Soft tyre temperature impact

Question:

Does higher track temperature make soft tyres worse?

Chart:

Scatter plot showing track temperature against average lap-time loss for soft tyres.

Fields:

- Columns: `track_temperature_c`
- Rows: average `lap_time_delta_to_stint_best_sec`
- Filter: `compound = SOFT`
- Filter: `valid_racing_lap_flag = True`
- Detail: `full_name`

Status:

Built as a placeholder.

Current limitation:

The current processed data has only one track temperature value, so the visualization forms a vertical cluster rather than a meaningful temperature-performance relationship. This question requires more race sessions or more detailed lap-level weather data.

### Q3 — Pit strategy

Question:

Which teams gain or lose the most around pit windows?

Planned chart:

Bar chart by team showing average pit-window gain/loss.

Fields needed:

- `team_name`
- `pit_window_gain_loss_sec`
- `lane_duration_sec`

Status:

Blocked.

Reason:

The current data does not contain a separate `fact_pit_stop.csv` table.

### Q4 — Driver consistency

Question:

Which drivers have the lowest lap-time variability?

Chart:

Ranked horizontal bar chart showing driver lap-time variability.

Fields:

- Rows: `full_name`
- Columns: calculated field `Driver Lap Variability`
- Color: `team_name`
- Filter: `valid_racing_lap_flag = True`

Calculated field:

`STDEV([lap_time_delta_to_driver_median_sec])`

Status:

Built and usable.

Current observation:

The chart ranks drivers by consistency, where lower lap-time variability means more consistent race pace. Logan Sargeant appears as a major outlier in the current one-race prototype.

Interpretation:

This view is useful for comparing driver consistency, but it is sensitive to outlier laps. It should not be interpreted as a season-wide ranking until more race data is processed and unusually slow laps are reviewed.

### Q5 — Circuit effects

Question:

Are some circuits more sensitive to tyre wear or weather?

Chart:

Heatmap showing average lap-time loss by circuit and compound.

Fields:

- Rows: `circuit_short_name`
- Columns: `compound`
- Color: average `lap_time_delta_to_stint_best_sec`
- Label: average `lap_time_delta_to_stint_best_sec`
- Filter: `valid_racing_lap_flag = True`

Status:

Built as a placeholder.

Current observation:

The current fact table contains only one circuit, Sakhir. The current heatmap therefore compares average lap-time loss for HARD and SOFT tyres only for this circuit. In the prototype data, SOFT has a higher average lap-time loss than HARD for Sakhir.

Interpretation:

This visualization is structurally ready for the final dataset, but it cannot yet answer the full circuit-sensitivity question. To compare circuits properly, the processed fact table needs to include multiple races and circuits. Once more circuits are available, this heatmap can show whether some circuits have stronger tyre degradation patterns or stronger performance differences between tyre compounds.

## Dashboard layout

Current dashboard layout:

Top:

- Q1 Tyre Degradation as the main full-width chart

Bottom left:

- Q4 Driver Consistency as the second main chart

Bottom/right area:

- Q2 Temperature Impact placeholder
- Q5 Circuit Effects placeholder

Bottom note:

- Short limitation note explaining that the dashboard is based on prototype data and requires more race sessions for temperature/circuit comparisons

## Current limitations

- Current dashboard prototype is based on one race session only.
- Current track temperature is effectively constant in the processed fact table.
- Circuit comparison is limited because the current fact table contains one circuit only.
- Pit strategy analysis is not possible until pit-stop data is added.
- Lap time is affected by many factors outside the current model, including fuel load, traffic, safety cars, team orders, car performance, and outlier laps.
- The dashboard shows patterns and associations, not causal proof.

## What is needed for the final dashboard

For the final version, the following is needed:

- More race sessions across several circuits
- More weather variation, ideally at lap-level or at least across many sessions
- A pit-stop fact table if Q3 remains part of the final analytical questions
- Optional outlier handling for unusually slow laps
- Final dashboard screenshots after the full dataset is available

## Deliverables so far

- `tableau/f1_tyre_weather_dashboard.twbx`
- `dashboard_screenshots/f1_dashboard_overview.png`
- `dashboard_screenshots/q1_tyre_degradation.png`
- `dashboard_screenshots/q4_driver_consistency.png`
- `dashboard_screenshots/q2_temperature_impact_placeholder.png`
- `dashboard_screenshots/q5_circuit_effects_placeholder.png`
- `docs/dashboard_plan.md`