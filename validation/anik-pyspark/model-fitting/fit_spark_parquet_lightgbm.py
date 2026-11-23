"""Fit the weather LightGBM configuration using batches from Spark Parquet."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import lightgbm as lgb
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
from numpy.lib.format import open_memmap


FEATURES = [
    "building_id", "site_id", "primary_use", "square_feet", "hour",
    "day_of_week", "month", "air_temperature", "dew_temperature", "wind_speed",
]
CATEGORIES = FEATURES[:3]
TARGET = "meter_reading"
BATCH_SIZE = 65_536
COUNTS = {"train": 8_321_304, "validation": 1_887_642, "test": 943_555}
PARAMS = {
    "objective": "regression",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": -1,
    "max_bin": 127,
    "num_threads": 2,
    "seed": 42,
    "verbosity": -1,
    "force_col_wise": True,
    "histogram_pool_size": 128,
}


def scan(dataset, columns, condition):
    return dataset.scanner(
        columns=columns,
        filter=condition,
        batch_size=BATCH_SIZE,
        batch_readahead=1,
        fragment_readahead=1,
        use_threads=False,
    ).to_batches()


def category_maps(dataset, train_filter):
    # Learn codes only from training. LightGBM treats code -1 as missing.
    values = {name: set() for name in CATEGORIES}
    for batch in scan(dataset, CATEGORIES, train_filter):
        for name in CATEGORIES:
            values[name].update(
                value for value in pc.unique(batch.column(name)).to_pylist()
                if value is not None
            )
    return {
        name: {value: number for number, value in enumerate(sorted(levels))}
        for name, levels in values.items()
    }


def numeric_values(batch, name):
    return batch.column(name).cast(pa.float32()).to_numpy(zero_copy_only=False)


def feature_matrix(batch, codes):
    matrix = np.empty((batch.num_rows, len(FEATURES)), dtype=np.float32)
    for index, name in enumerate(FEATURES):
        if name in codes:
            mapping = codes[name]
            matrix[:, index] = [mapping.get(value, -1) for value in batch.column(name).to_pylist()]
        else:
            matrix[:, index] = numeric_values(batch, name)
    return matrix


def label_values(batch):
    labels = numeric_values(batch, TARGET)
    if not np.isfinite(labels).all() or (labels < 0).any():
        raise ValueError("The electricity target must be finite and non-negative.")
    return labels


def train_model(dataset, train_filter, codes, scratch):
    feature_path = scratch / "training_features.npy"
    label_path = scratch / "training_labels.npy"
    features = open_memmap(
        feature_path, mode="w+", dtype=np.float32, shape=(COUNTS["train"], len(FEATURES))
    )
    labels = open_memmap(label_path, mode="w+", dtype=np.float32, shape=(COUNTS["train"],))

    start = perf_counter()
    offset = 0
    for batch in scan(dataset, FEATURES + [TARGET], train_filter):
        end = offset + batch.num_rows
        if end > COUNTS["train"]:
            raise ValueError(f"Training data exceed the expected {COUNTS['train']:,} rows.")
        features[offset:end] = feature_matrix(batch, codes)
        labels[offset:end] = np.log1p(label_values(batch))
        offset = end
    if offset != COUNTS["train"]:
        raise ValueError(f"Expected {COUNTS['train']:,} training rows, found {offset:,}.")
    features.flush()
    labels.flush()
    del features, labels
    preparation_time = perf_counter() - start
    print(f"Prepared {offset:,} training rows in {preparation_time:.2f} seconds.", flush=True)

    train_set = lgb.Dataset(
        np.load(feature_path, mmap_mode="r"),
        label=np.load(label_path, mmap_mode="r"),
        feature_name=FEATURES,
        categorical_feature=CATEGORIES,
        params=PARAMS,
        free_raw_data=True,
    )
    print("Fitting 200 LightGBM trees.", flush=True)
    started = perf_counter()

    def log_progress(environment):
        if (environment.iteration + 1) % 25 == 0:
            print(f"Built {environment.iteration + 1} of 200 trees.", flush=True)

    model = lgb.train(PARAMS, train_set, num_boost_round=200, callbacks=[log_progress])
    return model, preparation_time, perf_counter() - started


def evaluate(name, dataset, condition, codes, model):
    rows = 0
    absolute_errors = 0.0
    squared_log_errors = 0.0
    started = perf_counter()
    for batch in scan(dataset, FEATURES + [TARGET], condition):
        actual = label_values(batch).astype(np.float64)
        predictions = np.maximum(np.expm1(model.predict(feature_matrix(batch, codes), num_threads=2)), 0)
        if not np.isfinite(predictions).all():
            raise ValueError(f"The {name} predictions contain non-finite values.")
        absolute_errors += np.abs(predictions - actual).sum()
        squared_log_errors += np.square(np.log1p(predictions) - np.log1p(actual)).sum()
        rows += batch.num_rows
    if rows != COUNTS[name]:
        raise ValueError(f"Expected {COUNTS[name]:,} {name} rows, found {rows:,}.")
    return {"rows": rows, "mae": round(float(absolute_errors / rows), 4),
            "rmsle": round(float(np.sqrt(squared_log_errors / rows)), 4),
            "seconds": round(perf_counter() - started, 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parquet_folder", type=Path)
    parser.add_argument("output_folder", type=Path)
    args = parser.parse_args()
    args.output_folder.mkdir(parents=True)
    dataset = ds.dataset(str(args.parquet_folder), format="parquet")
    timestamp = ds.field("timestamp")
    timestamp_type = dataset.schema.field("timestamp").type
    january = pa.scalar(datetime(2016, 1, 1), type=timestamp_type)
    october = pa.scalar(datetime(2016, 10, 1), type=timestamp_type)
    december = pa.scalar(datetime(2016, 12, 1), type=timestamp_type)
    next_january = pa.scalar(datetime(2017, 1, 1), type=timestamp_type)
    train_filter = (timestamp >= january) & (timestamp < october)
    validation_filter = (timestamp >= october) & (timestamp < december)
    test_filter = (timestamp >= december) & (timestamp < next_january)

    print(f"LightGBM {lgb.__version__}. Arrow batches up to {BATCH_SIZE:,} rows.", flush=True)
    codes = category_maps(dataset, train_filter)
    with TemporaryDirectory(prefix="fit-matrices-", dir=args.output_folder) as scratch:
        model, prepare_time, training_time = train_model(dataset, train_filter, codes, Path(scratch))
    scores = {
        "lightgbm_version": lgb.__version__,
        "pyarrow_version": pa.__version__,
        "model": "LightGBM with Weather",
        "input": "Original ASHRAE data preprocessed by PySpark",
        "training_rows": COUNTS["train"],
        "params": PARAMS,
        "boosting_rounds": model.current_iteration(),
        "batch_rows": BATCH_SIZE,
        "encoding": {name: len(values) for name, values in codes.items()},
        "training_data_preparation_seconds": round(prepare_time, 2),
        "model_fit_seconds": round(training_time, 2),
        "validation": evaluate("validation", dataset, validation_filter, codes, model),
        "december_test": evaluate("test", dataset, test_filter, codes, model),
    }
    if scores["boosting_rounds"] != 200:
        raise RuntimeError("LightGBM did not build the intended number of trees.")
    model.save_model(str(args.output_folder / "lightgbm_from_spark_parquet.txt"))
    (args.output_folder / "category_codes.json").write_text(
        json.dumps(codes, indent=2) + "\n", encoding="utf-8"
    )
    evidence = json.dumps(scores, indent=2)
    (args.output_folder / "fit_results.json").write_text(evidence + "\n", encoding="utf-8")
    print(evidence, flush=True)


if __name__ == "__main__":
    main()
