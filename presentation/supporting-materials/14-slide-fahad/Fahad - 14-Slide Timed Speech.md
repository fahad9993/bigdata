# Fahad Rahman’s timed speech

**Data Explorers · 14 slides · Target 7 minutes 5 seconds before Q&A**

Use the timestamps as slide-change cues. The PowerPoint speaker notes contain the same speech.

## 00:00–00:18 · Slide 1 · Opening

Assalamu alaikum. Good morning, Ma’am and everyone. I’m Fahad, presenting on behalf of Data Explorers. My teammates are Anik, Sohel, and Shohag. We used ASHRAE data to predict how much electricity buildings use each hour.

## 00:18–00:43 · Slide 2 · Why predict electricity use?

A facilities team can use hourly predictions to plan demand and investigate unusual readings. We wanted to see whether adding weather improves predictions based on building and calendar information. We also wanted a workflow that could handle millions of readings on a laptop.

## 00:43–01:21 · Slide 3 · Dataset and preprocessing

The full Kaggle release contains six CSV files totaling about 2.61 gigabytes. We used three CSVs, about 686 megabytes in total, for meter readings, building details and weather. We started with over 20 million readings across four meter types and kept electricity only. We excluded Site Zero because nearly all its early-year readings were zero and its meters used a different unit. That left 11.15 million readings.

## 01:21–01:49 · Slide 4 · Data processing and features

DuckDB handled the main preprocessing. We joined building details by building ID and weather by site and timestamp. We extracted the hour, weekday and month from the timestamps. Almost 99.6 percent of readings had air-temperature data. We stored the cleaned data as Parquet and repeated the preprocessing independently in PySpark.

## 01:49–02:20 · Slide 5 · Weekday-by-hour heatmap

Each heatmap cell represents one weekday and one hour. We averaged within each building first, so every building in a cell had equal weight. From nine to five, weekday use averaged about 27 percent higher than weekend use. The highest cell was Tuesday at two in the afternoon. The separate daily profile in the report also peaked at two.

## 02:20–02:47 · Slide 6 · Building type and outdoor temperature

The left chart compares hourly electricity use per thousand square feet. Healthcare ranked highest among the categories shown. The right chart groups readings by outdoor temperature. Electricity use was higher in some very cold bins. Heating could contribute to that pattern, and differences in the buildings and sites in each bin could also matter.

## 02:47–03:15 · Slide 7 · Chronological split and model inputs

We trained from January through September, selected the model in October and November, and kept December for the final test. The baseline used the training median for the same building and hour. One LightGBM model used building and time information. The other added air temperature, dew point and wind speed.

## 03:15–03:46 · Slide 8 · LightGBM and evaluation metrics

LightGBM can model nonlinear relationships and interactions. We used the same settings for both versions and trained each on a log transformation of the electricity readings. We converted predictions back to kilowatt-hours. MAE gives the average absolute error in those units. RMSLE measures error on a log scale. We used validation RMSLE to select the model.

## 03:46–04:16 · Slide 9 · October–November validation

In October and November, the model without weather lowered RMSLE compared with the baseline, although its average absolute error was higher. Adding weather reduced MAE by about twelve and a half percent and RMSLE by about four percent compared with LightGBM without weather. The weather model had the lowest error on both measures, so we chose it for December.

## 04:16–04:57 · Slide 10 · December predictions and practical use

In December, the selected model cut RMSLE by 19.5 percent compared with the baseline. Average absolute error fell from about 45 to 41 kilowatt-hours. The scatterplot shows ten thousand readings. The scores use the full test set, about 944 thousand readings. In one example from the report, the model predicted about 200 kilowatt-hours above the actual reading. A facilities team could check whether that gap persisted and compare it with operating schedules and weather.

## 04:57–05:32 · Slide 11 · Feature importance

Building ID and floor area accounted for about 97 percent of split gain. Split gain measures how much a feature helped improve the tree splits during training. Weather accounted for less than half a percent of that gain. Adding weather still lowered validation RMSLE by about four percent. The validation comparison shows what changed in prediction error on held-out data.

## 05:32–05:56 · Slide 12 · Independent PySpark checks

We reran preprocessing in PySpark. All nine checks matched DuckDB, including the cleaned row count, temperature coverage, timestamp boundaries and the sizes of the three data splits. That gave us an independent check of the main preprocessing results.

## 05:56–06:39 · Slide 13 · Batched fitting on two computers

The earlier attempt stopped while loading data for the model. One of us read the Spark Parquet files in batches and wrote them directly into disk-backed arrays. LightGBM then fit all 200 trees on about 8.3 million training rows. I reran the batched code successfully on my computer. The table compares the two completed pipeline runs. DuckDB gave slightly lower December errors, and we kept its scores as the main project results.

## 06:39–07:05 · Slide 14 · Conclusion and Q&A

To conclude, we processed over eleven million electricity readings and found that weather improved predictions. The selected model beat the historical baseline in December. Our test covered one month and excluded Site Zero. The next step would be testing on other periods and on buildings the model has never seen. Thank you. We’re happy to take questions.

## Q&A backup

**Why did weather help with such a small share of split gain?**

Weather accounted for 0.43 percent of split gain. Adding the weather variables to the same model settings lowered validation MAE by 12.44 percent and RMSLE by 3.96 percent. The first number describes the fitted tree splits. The other two measure the change in prediction errors on held-out months.

**What does the large error in the practical example show?**

For building 975, the model predicted 456.67 kWh and the meter showed 257.00 kWh. That gap was one of five examples in the report. Checking for bias across December would require signed errors for the full test set.
