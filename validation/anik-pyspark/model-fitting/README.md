# LightGBM Fit From Spark Parquet

**Contribution.** Anik Halder ([@nikhofficial-lab](https://github.com/nikhofficial-lab)) ran and verified this independent LightGBM fitting experiment using the original ASHRAE data prepared by PySpark. Fahad Rahman ([@fahad9993](https://github.com/fahad9993)) provided the reference DuckDB and LightGBM results.

The full-size LightGBM fit completed on 22 November 2026 with all **200 trees** built. The input was the six PySpark-produced Parquet parts from the original ASHRAE data. The saved model reloaded and reproduced the December metrics on all **943,555** held-out rows.

## Evaluation

| Period and metric | LightGBM from Spark Parquet | Fahad’s LightGBM from DuckDB |
| --- | ---: | ---: |
| October–November validation MAE | 36.3942 | 35.9330 |
| October–November validation RMSLE | 0.7017 | 0.6939 |
| December test MAE | 41.6046 | 41.0866 |
| December test RMSLE | 0.6318 | 0.6245 |

Both runs used weather features and the January–September training period. The fit here used **8,321,304** training rows, **1,887,642** validation rows, and **943,555** December test rows. Fahad’s model has the lower saved errors on all four measures. The experiment verifies that fitting on the Spark-produced files is feasible on this laptop. A controlled comparison would be needed to isolate why the scores differ. [Fahad’s validation scores](https://github.com/fahad9993/bigdata/blob/8a8b6611e7c4cbf8e1a3566712ae473a5fcd40d2/outputs/tables/validation_results.csv) · [Fahad’s test scores](https://github.com/fahad9993/bigdata/blob/8a8b6611e7c4cbf8e1a3566712ae473a5fcd40d2/outputs/tables/final_test_results.csv)

## How the fit avoided a large pandas load

PySpark produced the input Parquet in Ubuntu. On Windows, PyArrow read the ten input features and the target in batches of up to **65,536** rows. Training-only category codes were used for building, site, and building use. The batches went into disk-backed NumPy arrays. LightGBM 4.7.0 fitted the 200 trees with two threads, column-wise histograms, and a 128 MB histogram cache limit. Training used the log-transformed target, and scoring converted predictions back to the original units. The Python environment used PyArrow 26.0.0, NumPy 2.5.5, SciPy 1.18.1, and Narwhals 2.29.0.

- **Fit time** was **87.26 seconds**, including LightGBM’s dataset construction.
- **Full run time** was **129.12 seconds**, including input preparation and both evaluation periods. The process exited with code **0**.
- **Memory high-water mark near completion** was **1,029,689,344 bytes** (about **0.96 GiB**) for the actual Python training process. This is a process working-set reading, which measures resident memory rather than total system usage.
- **Saved-model check** reloaded the 200-tree model and reproduced December MAE **41.6046** and RMSLE **0.6318**.

This is a separate fitting experiment on Anik’s laptop. The report can describe the memory-aware fitting method and its results. Fahad’s completed DuckDB-based run remains the source of the group’s main model scores.

## Report comparison table

The [LaTeX subsection](lightgbm_pipeline_comparison.tex) contains the
side-by-side validation and December test scores. Insert it at the end
of **Independent PySpark Validation**, before Discussion. The report
already loads `booktabs` for the table rules.

When compiling from the `report` directory, include the subsection with:

```latex
\input{../validation/anik-pyspark/model-fitting/lightgbm_pipeline_comparison.tex}
```
