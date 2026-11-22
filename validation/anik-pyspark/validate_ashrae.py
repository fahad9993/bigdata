"""Reproduce the team's electricity preprocessing on the original ASHRAE CSV files."""

import argparse
import csv
import json
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


SOURCES = {
    "train.csv": "building_id INT, meter INT, timestamp TIMESTAMP, meter_reading DOUBLE",
    "building_metadata.csv": (
        "site_id INT, building_id INT, primary_use STRING, square_feet INT, "
        "year_built DOUBLE, floor_count DOUBLE"
    ),
    "weather_train.csv": (
        "site_id INT, timestamp TIMESTAMP, air_temperature DOUBLE, cloud_coverage DOUBLE, "
        "dew_temperature DOUBLE, precip_depth_1_hr DOUBLE, sea_level_pressure DOUBLE, "
        "wind_direction DOUBLE, wind_speed DOUBLE"
    ),
}

# Baselines from the team's committed DuckDB inspection, preprocessing, and modeling.
EXPECTED = {
    "raw_meter_rows": 20_216_100,
    "raw_electricity_rows": 12_060_910,
    "processed_rows": 11_152_501,
    "rows_with_air_temperature": 11_105_485,
    "first_timestamp": "2016-01-01 00:00:00",
    "last_timestamp": "2016-12-31 23:00:00",
    "train_rows": 8_321_304,
    "validation_rows": 1_887_642,
    "test_rows": 943_555,
}


def inventory(raw_dir):
    manifest = {}
    for filename in SOURCES:
        source = raw_dir / filename
        if not source.is_file():
            raise FileNotFoundError(f"Missing required ASHRAE file: {source}")
        digest = sha256()
        with source.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        manifest[filename] = {"bytes": source.stat().st_size, "sha256": digest.hexdigest()}
    return manifest


def read_csv(spark, raw_dir, name):
    return (
        spark.read.schema(SOURCES[name])
        .option("header", True)
        .option("enforceSchema", False)
        .option("mode", "FAILFAST")
        .option("ignoreLeadingWhiteSpace", True)
        .option("ignoreTrailingWhiteSpace", True)
        .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
        .csv(str(raw_dir / name))
    )


def validate(raw_dir, output_dir):
    manifest = inventory(raw_dir)
    output_dir.mkdir()
    spark = (
        SparkSession.builder.appName("ASHRAEElectricityValidation")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    try:
        meter = read_csv(spark, raw_dir, "train.csv")
        buildings = read_csv(spark, raw_dir, "building_metadata.csv").select(
            "building_id", "site_id", "primary_use", "square_feet"
        )
        weather = read_csv(spark, raw_dir, "weather_train.csv").select(
            "site_id", "timestamp", "air_temperature", "dew_temperature", "wind_speed"
        )
        for frame, keys in (
            (buildings, ["building_id"]),
            (weather, ["site_id", "timestamp"]),
        ):
            duplicated_keys = (
                frame.groupBy(*keys).count().where(F.col("count") > 1).limit(1).count()
            )
            if duplicated_keys:
                raise ValueError(f"Input contains duplicate join keys: {keys}")

        print("Counting rows in the original meter file", flush=True)
        start = perf_counter()
        raw_counts = {
            row["meter"]: row["count"]
            for row in meter.groupBy("meter").count().collect()
        }
        raw_count_seconds = perf_counter() - start

        # All large transformations stay in Spark. The building and weather lookup
        # tables are small enough to send to each worker for the joins.
        electricity = (
            meter.where(F.col("meter") == 0)
            .drop("meter")
            .join(F.broadcast(buildings), "building_id", "inner")
            .where(F.col("site_id") != 0)
            .join(F.broadcast(weather), ["site_id", "timestamp"], "left")
            .withColumn("hour", F.hour("timestamp"))
            .withColumn("day_of_week", F.dayofweek("timestamp") - 1)
            .withColumn("month", F.month("timestamp"))
            .select(
                "building_id", "site_id", "primary_use", "square_feet", "timestamp",
                "hour", "day_of_week", "month", "air_temperature", "dew_temperature",
                "wind_speed", "meter_reading",
            )
        )
        parquet_path = output_dir / "electricity_data_spark.parquet"
        print("Preprocessing the original CSV files and writing Parquet", flush=True)
        start = perf_counter()
        electricity.write.parquet(str(parquet_path), compression="zstd")
        preprocessing_seconds = perf_counter() - start

        print("Verifying the written Parquet against the DuckDB counts", flush=True)
        start = perf_counter()
        processed = spark.read.parquet(str(parquet_path))
        timestamp = F.col("timestamp")
        october = F.lit("2016-10-01 00:00:00").cast("timestamp")
        december = F.lit("2016-12-01 00:00:00").cast("timestamp")
        stats = processed.agg(
            F.count("*").alias("processed_rows"),
            F.count("air_temperature").alias("rows_with_air_temperature"),
            F.date_format(F.min(timestamp), "yyyy-MM-dd HH:mm:ss").alias("first_timestamp"),
            F.date_format(F.max(timestamp), "yyyy-MM-dd HH:mm:ss").alias("last_timestamp"),
            F.count(F.when(timestamp < october, 1)).alias("train_rows"),
            F.count(F.when((timestamp >= october) & (timestamp < december), 1)).alias(
                "validation_rows"
            ),
            F.count(F.when(timestamp >= december, 1)).alias("test_rows"),
        ).first().asDict()
        stats.update(
            raw_meter_rows=sum(raw_counts.values()),
            raw_electricity_rows=raw_counts.get(0, 0),
        )
        audit_seconds = perf_counter() - start

        print("Summarizing weekday and hour use in Spark", flush=True)
        start = perf_counter()
        building_averages = processed.groupBy("building_id", "day_of_week", "hour").agg(
            F.avg("meter_reading").alias("building_average"),
            F.count("*").alias("readings"),
        )
        summary = (
            building_averages.groupBy("day_of_week", "hour")
            .agg(
                F.avg("building_average").alias("mean_meter_reading"),
                F.count("*").alias("buildings"),
                F.sum("readings").alias("readings"),
            )
            .orderBy("day_of_week", "hour")
            .collect()
        )
        heatmap_seconds = perf_counter() - start
        summarized_rows = sum(row["readings"] for row in summary)
        if not 0 < len(summary) <= 168 or summarized_rows != stats["processed_rows"]:
            raise ValueError("Weekday/hour aggregation did not cover the expected rows.")

        with (output_dir / "weekday_hour_summary.csv").open("w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out)
            writer.writerow(("day_of_week", "hour", "mean_meter_reading", "buildings", "readings"))
            writer.writerows(summary)

        comparison = {
            name: {"pyspark": stats[name], "duckdb": expected, "match": stats[name] == expected}
            for name, expected in EXPECTED.items()
        }
        matches = all(check["match"] for check in comparison.values())
        evidence = {
            "spark_version": spark.version,
            "mode": spark.sparkContext.master,
            "source_files": manifest,
            "source_total_bytes": sum(item["bytes"] for item in manifest.values()),
            "parquet_bytes": sum(part.stat().st_size for part in parquet_path.glob("part-*.parquet")),
            "air_temperature_coverage_percent": round(
                100 * stats["rows_with_air_temperature"] / stats["processed_rows"], 2
            ),
            "comparison": comparison,
            "all_checks_match": matches,
            "summary_rows": len(summary),
            "wall_seconds": {
                "pyspark_meter_count": round(raw_count_seconds, 2),
                "pyspark_preprocess_write": round(preprocessing_seconds, 2),
                "pyspark_parquet_audit": round(audit_seconds, 2),
                "pyspark_weekday_hour_summary": round(heatmap_seconds, 2),
            },
        }
        evidence_text = json.dumps(evidence, indent=2)
        (output_dir / "pyspark_validation.json").write_text(evidence_text + "\n", encoding="utf-8")
        print(evidence_text, flush=True)
        if not matches:
            raise SystemExit("At least one verified DuckDB count or timestamp differs.")
    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_dir", type=Path, help="Directory containing the three original CSVs")
    parser.add_argument("output_dir", type=Path, help="New directory for this validation run")
    args = parser.parse_args()
    validate(args.raw_dir.resolve(), args.output_dir.resolve())


if __name__ == "__main__":
    main()

