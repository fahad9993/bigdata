
from pathlib import Path

# Project root directory
PROJECT_DIR = Path(r"D:\Big Data Project")

# Data directories
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Output directories
OUTPUT_DIR = PROJECT_DIR / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"
MODEL_DIR = OUTPUT_DIR / "models"

# Notebook directory
NOTEBOOK_DIR = PROJECT_DIR / "notebooks"

# Create necessary output directories
for directory in [
    PROCESSED_DIR,
    FIGURE_DIR,
    TABLE_DIR,
    MODEL_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)

# PySpark settings (local execution on an 8 GB Windows laptop)
SPARK_LOCAL_THREADS = 2
SPARK_SHUFFLE_PARTITIONS = 8
# Spark writes a directory of part-*.parquet files rather than one file.
SPARK_PARQUET_DIR = PROCESSED_DIR / "electricity_data_spark.parquet"
