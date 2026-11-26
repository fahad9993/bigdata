# Fahad Rahman’s presentation script

**Target delivery is 7 minutes 5 seconds.** The timestamps are slide-change cues and exclude Q&A.

**00:00–00:18 | Slide 1 | Opening**

Assalamu alaikum. Good morning, Ma’am and everyone. I’m Fahad, presenting on behalf of Data Explorers. My teammates are Anik, Sohel, and Shohag. We used ASHRAE data to predict hourly electricity use in buildings.

**00:18–00:36 | Slide 2 | Motivation and objectives**

Our main question was whether weather improves predictions based on building and calendar information. We also wanted to understand when electricity use is higher and see whether a second processing pipeline could reproduce the key checks.

**00:36–01:02 | Slide 3 | Dataset and scale**

The complete Kaggle release is about 2.61 gigabytes. Our analysis used three CSV files totaling about 686 megabytes. We started with 20.22 million labeled readings across four meter types. After keeping electricity and excluding Site 0, we had about 11.15 million readings from 1,308 buildings.

**01:02–01:20 | Slide 4 | Predictors and target**

We predict the electricity reading for one building in one hour, measured in kilowatt-hours. Our inputs describe the building, the time, and the weather. The three weather variables are air temperature, dew point and wind speed.

**01:20–01:44 | Slide 5 | Big Data pipeline**

DuckDB handled the main processing. We joined building details by building ID and weather by site and timestamp. Filtering the data and saving it as Parquet cut file size by about 92 percent. We also reproduced the preprocessing in PySpark.

**01:44–02:06 | Slide 6 | Site 0**

Site 0 showed an unusual pattern. About 38 percent of its electricity readings across the year were zero. From January through April, almost all were zero. The training readings there also used a different unit, so we excluded that site.

**02:06–02:33 | Slide 7 | Joins and chronological split**

About 99.6 percent of the cleaned readings matched an air-temperature observation. We used January through September for training, October and November to choose the model, and December for the final test. We learned category encodings from the training data and kept December separate until evaluation.

**02:33–02:55 | Slide 8 | Models and error metrics**

Our baseline used the training median for the same building and hour. We compared it with two LightGBM models, with and without weather. Both models trained on log-transformed readings. MAE measures average absolute error in kilowatt-hours, and RMSLE measures prediction error on a log scale.

**02:55–03:14 | Slide 9 | Hourly pattern**

The average electricity reading was lowest at three in the morning, around 139 kilowatt-hours. It rose through the morning and peaked at about 189 at two in the afternoon. The timing is consistent with regular building operating hours.

**03:14–03:33 | Slide 10 | Building categories**

We compared electricity use per thousand square feet, giving each building equal weight in its category. Among the categories shown, healthcare had the highest average, at about four kilowatt-hours per thousand square feet. Lodging and residential had the lowest, at about one point one.

**03:33–03:54 | Slide 11 | Outdoor temperature**

We grouped readings into two-degree temperature bins. Average electricity use was higher in some very cold bins and lower at moderate temperatures. Heating and cooling could help explain the pattern. The mix of sites and building types may also matter.

**03:54–04:22 | Slide 12 | Weekday and hour heatmap**

Each cell represents one weekday and one hour. We averaged the building-level means so each building in that cell had equal weight. Between nine and five, weekday averages were about 27 percent higher than weekend averages. The highest cell was Tuesday at two in the afternoon.

**04:22–04:53 | Slide 13 | Validation results**

We used the same LightGBM settings for both versions and compared them on the October and November data. Adding weather lowered validation MAE by about 12.4 percent and RMSLE by about 4 percent. The weather model had the lowest validation RMSLE, so we selected it for the December test.

**04:53–05:24 | Slide 14 | December test results**

In December, the final model reduced RMSLE by 19.5 percent compared with the baseline. MAE fell from about 45 to 41 kilowatt-hours. The scatterplot shows ten thousand readings, with better predictions closer to the diagonal. The table uses the full December test set, about 944 thousand readings.

**05:24–06:03 | Slide 15 | PySpark checks and batch fitting**

PySpark matched DuckDB on all nine preprocessing checks. One of us loaded the Spark Parquet files in batches into disk-backed arrays. LightGBM fit all 200 trees on about 8.3 million training rows, and the Python process peaked at about one gigabyte of memory. I reran the code successfully. The DuckDB run had slightly lower December errors. The fit times came from separate runs.

**06:03–06:25 | Slide 16 | Five prediction examples**

The model overpredicted all five December examples. The largest gap was about 200 kilowatt-hours for building 975. A facilities team could review gaps like this when they persist over several hours and compare them with operating schedules and weather. Testing for systematic bias would require the full December set.

**06:25–06:49 | Slide 17 | Feature importance and limitations**

Building ID and floor area accounted for about 97 percent of the fitted model’s split gain. Those two predictors contributed the most improvement across the model’s splits. The final test covered only December 2016, so performance in other periods and on new buildings still needs testing.

**06:49–07:05 | Slide 18 | Conclusion and questions**

To conclude, we processed more than eleven million readings and independently verified the preprocessing. Adding weather improved validation results, and the final model beat the historical baseline in December. Thank you. We’re happy to take questions.

## Q&A backup

**Why did weather help if building ID and floor area accounted for about 97 percent of split gain?**

Split gain measures how much features contributed to improving the splits in the fitted trees. Weather accounted for only 0.43 percent of that gain. We also compared two LightGBM models with the same settings on the October–November validation set. Adding weather lowered MAE by 12.4 percent and RMSLE by 4.0 percent. That comparison directly measured the change in prediction errors when we added weather.

