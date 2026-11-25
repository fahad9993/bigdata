# Data Explorers presentation visuals

These widescreen figures are ready to insert in a PowerPoint slide.

## 01 Weekday-by-hour electricity heatmap

- Covers all 11,152,501 cleaned ASHRAE electricity readings in 2016, with Site 0 excluded.
- Each cell first averages readings for each building at that weekday and hour, then averages those building means. Every building represented in a cell receives equal weight.
- From 09:00 through 17:00, the mean across weekday cells is 196.49 kWh and the mean across weekend cells is 155.11 kWh. Tuesday at 14:00 is the peak cell at 204.85 kWh. The clock follows the source timestamps.
- Suggested talking point. Electricity use was higher during weekday daytime hours, a pattern consistent with building operating schedules.

[Source](../../../validation/anik-pyspark/README.md)

## 02 December actual versus predicted electricity readings

- The scatterplot uses a sample of 10,000 readings drawn from the December 2016 holdout. The dashed line marks exact agreement. The displayed axes end at the pooled 99th percentile of the actual and predicted sample values.
- The score table uses all 943,555 December observations. Historical baseline MAE was 44.9097 and RMSLE was 0.7756. LightGBM with weather achieved 41.0866 MAE and 0.6245 RMSLE.
- Suggested talking point. The final LightGBM model lowered RMSLE by 19.5% compared with the historical baseline on the same December holdout.

[Source](../../../outputs/tables/final_test_results.csv)
