#!/usr/bin/env python3
"""
Credit Risk ML System - Data Processor

Fresh rewrite focused on reliability and compatibility with run_pipeline.py.
It reads standardized parquet files from data/interim and writes processed
parquet outputs to data/processed.
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pyspark.ml.feature import StringIndexer
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, FloatType, NumericType, StringType


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------

def setup_logger() -> Tuple[logging.Logger, Path]:
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"etl_pipeline_{ts}.log"

    logger = logging.getLogger("credit_risk_data_processor")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Avoid duplicate handlers if module is imported repeatedly.
    if logger.handlers:
        logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger, log_path


LOGGER, LOG_PATH = setup_logger()


# ------------------------------------------------------------
# Config
# ------------------------------------------------------------

@dataclass
class ProcessorConfig:
    input_file: str
    output_file: str
    sample_fraction: float = 1.0
    missing_threshold: float = 60.0
    input_dir: str = "data/interim"
    output_dir: str = "data/processed"
    cast_rules: Dict[str, str] = field(default_factory=dict)
    required_columns: List[str] = field(default_factory=list)
    required_non_null_columns: List[str] = field(default_factory=list)
    dedup_keys: List[str] = field(default_factory=list)
    outlier_method: str = "none"
    outlier_columns: List[str] = field(default_factory=list)
    outlier_iqr_multiplier: float = 1.5
    outlier_max_columns: int = 300
    quality_report_file: str = ""
    schema_contract_file: str = ""


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def read_metadata(interim_dir: Path) -> Dict[str, dict]:
    metadata_path = interim_dir / "metadata.json"
    if not metadata_path.exists():
        LOGGER.warning("metadata.json not found in interim directory")
        return {}

    with metadata_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    LOGGER.info("Loaded metadata.json with %s entries", len(data))
    return data


def parse_csv_list(value: str) -> List[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_json_map(value: str) -> Dict[str, str]:
    if not value:
        return {}

    p = Path(value)
    if p.exists() and p.is_file():
        with p.open("r", encoding="utf-8") as f:
            obj = json.load(f)
    else:
        obj = json.loads(value)

    if not isinstance(obj, dict):
        raise ValueError("cast rules must be a JSON object mapping column to type")

    return {str(k): str(v) for k, v in obj.items()}


def get_file_size_mb(path: Path) -> float:
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    if path.is_file():
        return path.stat().st_size / (1024 * 1024)
    total = sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
    return total / (1024 * 1024)


def remove_existing_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


# Supervised label / split-indicator columns. Standardization prefixes every
# column with a short table tag (e.g. ``fm_``, ``art_``), so a bare ``target``
# becomes ``fm_target``. Match a single-token prefix only, so genuinely derived
# features such as ``art_percentile_target`` stay features rather than labels.
LABEL_RE = re.compile(r"(?:[a-z0-9]+_)?(?:target|set)$")


def label_columns(columns: List[str]) -> List[str]:
    """Return supervised label / split-indicator columns.

    Examples that match: ``target``, ``fm_target``, ``art_target``, ``fm_set``.
    Examples that do not: ``art_percentile_target`` (multi-token prefix → a
    derived feature, not the label).
    """
    return [c for c in columns if LABEL_RE.fullmatch(c.lower())]


def id_columns(columns: List[str]) -> List[str]:
    """Non-feature columns: identifiers plus supervised labels.

    These are excluded from every feature transform (high-missing column
    drops, null fills, ordinal encoding, and outlier capping) so the label is
    never mutated as if it were a feature.
    """
    labels = set(label_columns(columns))
    return [c for c in columns if "client_id" in c.lower() or c in labels]


def choose_partitions(rows: int, cols: int) -> int:
    # Conservative partitioning that works well for medium and wide tables.
    if rows <= 0:
        return 1
    base = max(1, rows // 75000)
    width_factor = max(1, cols // 400)
    return int(min(32, max(1, base * width_factor)))


def is_feature_matrix(input_file: str, metadata: Dict[str, dict]) -> bool:
    name = input_file.replace("_standardized.parquet", "")
    lower_file = input_file.lower()

    if "feature_matrix" in lower_file:
        return True

    # Keep non-feature support/reference tables (for example correlations,
    # feature importances) in passthrough mode. Broad schema heuristics can
    # misclassify very wide analytics tables and trigger unnecessary ML steps.
    return False


def ensure_windows_hadoop() -> None:
    if os.name != "nt":
        return

    project_root = Path(__file__).resolve().parent.parent
    hadoop_home = project_root / "hadoop"
    winutils = hadoop_home / "bin" / "winutils.exe"

    if not winutils.exists():
        LOGGER.warning("winutils.exe not found at %s", winutils)
        return

    os.environ["HADOOP_HOME"] = str(hadoop_home)
    os.environ["hadoop.home.dir"] = str(hadoop_home)

    path_value = os.environ.get("PATH", "")
    hadoop_bin = str(hadoop_home / "bin")
    if hadoop_bin.lower() not in path_value.lower():
        os.environ["PATH"] = hadoop_bin + os.pathsep + path_value

    LOGGER.info("Configured HADOOP_HOME=%s", hadoop_home)


# ------------------------------------------------------------
# Spark helpers
# ------------------------------------------------------------

def create_spark() -> SparkSession:
    ensure_windows_hadoop()
    LOGGER.info("Creating Spark session")
    return (
        SparkSession.builder
        .appName("CreditRiskDataProcessor")
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "4g")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .getOrCreate()
    )


def normalize_sample_fraction(value: float) -> float:
    if value <= 0:
        return 0.001
    if value > 1:
        return 1.0
    return value


def load_df(spark: SparkSession, path: Path) -> DataFrame:
    LOGGER.info("Reading %s", path)
    return spark.read.parquet(str(path))


def validate_required_columns(df: DataFrame, required_columns: List[str]) -> None:
    if not required_columns:
        return

    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing: {missing}")


def apply_cast_rules_spark(df: DataFrame, cast_rules: Dict[str, str]) -> Tuple[DataFrame, List[str], List[str]]:
    if not cast_rules:
        return df, [], []

    applied: List[str] = []
    skipped: List[str] = []

    for col_name, target_type in cast_rules.items():
        if col_name not in df.columns:
            skipped.append(col_name)
            continue
        df = df.withColumn(col_name, F.col(col_name).cast(target_type))
        applied.append(col_name)

    if applied:
        LOGGER.info("Applied cast rules for %s columns", len(applied))
    if skipped:
        LOGGER.warning("Skipped cast rules for missing columns: %s", skipped)

    return df, applied, skipped


def drop_rows_with_nulls(df: DataFrame, columns: List[str]) -> Tuple[DataFrame, int]:
    if not columns:
        return df, 0

    before = df.count()
    kept_cols = [c for c in columns if c in df.columns]
    if not kept_cols:
        return df, 0

    df = df.dropna(subset=kept_cols)
    after = df.count()
    dropped = max(0, before - after)
    if dropped:
        LOGGER.info("Dropped %s rows due to nulls in required columns", dropped)
    return df, dropped


def drop_unlabeled_rows_spark(df: DataFrame, sentinel: float = -999) -> Tuple[DataFrame, int, List[str]]:
    """Drop rows whose supervised label is missing.

    Standardization encodes a missing label as the ``-999`` sentinel; in the
    Home Credit data these are the unlabeled test-split rows. They cannot be
    used for supervised training and, left in place, make the label look like a
    third class. Rows with a null or sentinel label are removed.
    """
    labels = label_columns(df.columns)
    if not labels:
        return df, 0, []

    before = df.count()
    cond = None
    for c in labels:
        valid = F.col(c).isNotNull() & (F.col(c) != F.lit(sentinel))
        cond = valid if cond is None else (cond & valid)
    df = df.filter(cond)
    after = df.count()
    removed = max(0, before - after)
    if removed:
        LOGGER.info("Dropped %s unlabeled rows (label null or == %s); labels=%s", removed, sentinel, labels)
    return df, removed, labels


def apply_deduplication(df: DataFrame, keys: List[str]) -> Tuple[DataFrame, int, List[str]]:
    if not keys:
        return df, 0, []

    present_keys = [k for k in keys if k in df.columns]
    if not present_keys:
        return df, 0, []

    before = df.count()
    df = df.dropDuplicates(present_keys)
    after = df.count()
    removed = max(0, before - after)
    if removed:
        LOGGER.info("Removed %s duplicate rows using keys=%s", removed, present_keys)
    return df, removed, present_keys


def resolve_outlier_columns_spark(df: DataFrame, columns: List[str], max_columns: int = 300) -> List[str]:
    requested = [c.strip() for c in columns if str(c).strip()]
    request_auto = (not requested) or any(c.lower() == "auto" for c in requested)

    schema_map = {f.name: f.dataType for f in df.schema.fields}
    if request_auto:
        ids = set(id_columns(df.columns))
        auto_cols = [
            c for c in df.columns
            if c not in ids and isinstance(schema_map.get(c), NumericType)
        ]
        if max_columns > 0 and len(auto_cols) > max_columns:
            LOGGER.warning(
                "Auto outlier column selection found %s numeric features; capping to first %s for performance",
                len(auto_cols),
                max_columns,
            )
            auto_cols = auto_cols[:max_columns]
        return auto_cols

    valid_cols = [c for c in requested if c in df.columns and isinstance(schema_map.get(c), NumericType)]
    return valid_cols


def resolve_outlier_columns_pandas(
    df,
    feature_cols: List[str],
    columns: List[str],
    max_columns: int = 300,
) -> List[str]:
    import pandas as pd

    requested = [c.strip() for c in columns if str(c).strip()]
    request_auto = (not requested) or any(c.lower() == "auto" for c in requested)

    if request_auto:
        auto_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
        if max_columns > 0 and len(auto_cols) > max_columns:
            LOGGER.warning(
                "Auto outlier column selection found %s numeric features; capping to first %s for performance",
                len(auto_cols),
                max_columns,
            )
            auto_cols = auto_cols[:max_columns]
        return auto_cols

    valid_cols = [c for c in requested if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    return valid_cols


def encode_string_columns_spark(df: DataFrame, string_cols: List[str]) -> Tuple[DataFrame, List[str]]:
    """Ordinal-encode string feature columns to double using StringIndexer.

    Processes columns in batches of 50 to avoid wide-plan blowups.
    Columns that fail encoding are dropped with a warning.
    Returns the transformed DataFrame and the list of columns encoded.
    """
    if not string_cols:
        return df, []

    BATCH = 50
    encoded: List[str] = []

    for i in range(0, len(string_cols), BATCH):
        batch = string_cols[i : i + BATCH]
        out_cols = [f"{c}__idx" for c in batch]
        try:
            indexer = StringIndexer(
                inputCols=batch,
                outputCols=out_cols,
                handleInvalid="keep",
                stringOrderType="frequencyDesc",
            )
            model = indexer.fit(df)
            df = model.transform(df)
            for orig, idx_col in zip(batch, out_cols):
                df = df.withColumn(orig, F.col(idx_col).cast(DoubleType())).drop(idx_col)
            encoded.extend(batch)
        except Exception as exc:
            LOGGER.warning(
                "String encoding batch %s failed: %s; dropping unencoded columns",
                i // BATCH,
                exc,
            )

    if encoded:
        LOGGER.info("Ordinal-encoded %s string columns", len(encoded))

    # Drop any string columns that failed all encoding attempts.
    remaining_string = [c for c in string_cols if c not in encoded and c in df.columns]
    if remaining_string:
        LOGGER.warning("Dropping %s string columns that could not be encoded", len(remaining_string))
        df = df.drop(*remaining_string)

    return df, encoded


def encode_string_columns_pandas(df, string_cols: List[str]) -> Tuple[Any, List[str]]:
    """Ordinal-encode string columns to float64 using pandas category codes.

    Each unique value receives a stable integer code (0-based, sorted by first
    appearance after fillna so \"UNKNOWN\" gets a consistent code). Columns that
    fail encoding are dropped with a warning.
    Returns the transformed DataFrame and the list of columns encoded.
    """
    if not string_cols:
        return df, []

    encoded: List[str] = []
    failed: List[str] = []

    for c in string_cols:
        try:
            df[c] = df[c].astype("category").cat.codes.astype("float64")
            encoded.append(c)
        except Exception as exc:
            LOGGER.warning("Could not encode column '%s': %s", c, exc)
            failed.append(c)

    if encoded:
        LOGGER.info("Ordinal-encoded %s string columns", len(encoded))
    if failed:
        LOGGER.warning("Dropping %s string columns that failed encoding", len(failed))
        df = df.drop(columns=failed)

    return df, encoded


def apply_outlier_strategy_spark(
    df: DataFrame,
    method: str,
    columns: List[str],
    iqr_multiplier: float,
    max_columns: int,
) -> Tuple[DataFrame, Dict[str, Any]]:
    method = (method or "none").lower()
    summary: Dict[str, Any] = {
        "method": method,
        "columns": [],
        "rows_removed": 0,
        "columns_capped": 0,
    }

    if method == "none":
        return df, summary

    numeric_cols = resolve_outlier_columns_spark(df, columns, max_columns=max_columns)
    if not numeric_cols:
        LOGGER.warning("Outlier method enabled but no valid outlier columns were found")
        return df, summary

    LOGGER.info("Outlier handling columns selected: %s", len(numeric_cols))

    bounds: Dict[str, Tuple[float, float]] = {}
    for c in numeric_cols:
        q = df.approxQuantile(c, [0.25, 0.75], 0.01)
        if len(q) != 2:
            continue
        q1, q3 = q
        iqr = q3 - q1
        if iqr <= 0:
            # Constant or heavily imbalanced (e.g. binary) column: Q1 == Q3, so
            # the cap band has zero width and would collapse every value to a
            # single number. Leave such columns untouched.
            continue
        lb = q1 - iqr_multiplier * iqr
        ub = q3 + iqr_multiplier * iqr
        bounds[c] = (lb, ub)

    if not bounds:
        return df, summary

    summary["columns"] = sorted(bounds.keys())

    if method == "iqr_cap":
        # Build one projection to avoid very deep withColumn chains on wide
        # datasets, which can trigger Spark analyzer stack overflows.
        projected_cols = []
        for c in df.columns:
            if c in bounds:
                lb, ub = bounds[c]
                projected_cols.append(
                    F.when(F.col(c).isNull(), F.col(c))
                    .when(F.col(c) < F.lit(lb), F.lit(lb))
                    .when(F.col(c) > F.lit(ub), F.lit(ub))
                    .otherwise(F.col(c))
                    .alias(c)
                )
            else:
                projected_cols.append(F.col(c))
        df = df.select(*projected_cols)
        summary["columns_capped"] = len(bounds)
        LOGGER.info("Applied IQR capping to %s columns", len(bounds))
        return df, summary

    if method == "iqr_remove":
        before = df.count()
        cond = None
        for c, (lb, ub) in bounds.items():
            ccond = F.col(c).isNull() | ((F.col(c) >= F.lit(lb)) & (F.col(c) <= F.lit(ub)))
            cond = ccond if cond is None else (cond & ccond)
        if cond is not None:
            df = df.filter(cond)
        after = df.count()
        summary["rows_removed"] = max(0, before - after)
        LOGGER.info("Applied IQR row removal, removed rows=%s", summary["rows_removed"])
        return df, summary

    LOGGER.warning("Unknown outlier method '%s'; skipping outlier handling", method)
    summary["method"] = "none"
    return df, summary


def apply_sampling(df: DataFrame, fraction: float) -> DataFrame:
    fraction = normalize_sample_fraction(fraction)
    if fraction >= 1.0:
        return df

    sampled = df.sample(withReplacement=False, fraction=fraction, seed=42)
    sampled_count = sampled.count()
    if sampled_count == 0:
        LOGGER.warning("Sample produced 0 rows; falling back to 1-row sample")
        return df.limit(1)

    LOGGER.info("Sampled rows: %s", sampled_count)
    return sampled


def split_columns(df: DataFrame) -> Tuple[List[str], List[str], List[str], Dict[str, object]]:
    schema_map = {f.name: f.dataType for f in df.schema.fields}
    ids = id_columns(df.columns)
    features = [c for c in df.columns if c not in ids]

    numeric = [c for c in features if isinstance(schema_map[c], NumericType)]
    strings = [c for c in features if isinstance(schema_map[c], StringType)]
    return ids, numeric, strings, schema_map


def drop_high_missing_columns(df: DataFrame, threshold: float, schema_map: Dict[str, object]) -> Tuple[DataFrame, List[str]]:
    ids, _, _, _ = split_columns(df)
    feature_cols = [c for c in df.columns if c not in ids]

    if not feature_cols:
        return df, []

    total_rows = df.count()
    if total_rows == 0:
        return df, []

    threshold = max(0.0, min(100.0, float(threshold)))
    max_missing = (threshold / 100.0) * total_rows

    drop_cols: List[str] = []
    batch_size = 200

    for i in range(0, len(feature_cols), batch_size):
        batch = feature_cols[i : i + batch_size]
        exprs = []
        for c in batch:
            is_missing = F.col(c).isNull()
            if isinstance(schema_map[c], (FloatType, DoubleType)):
                is_missing = is_missing | F.isnan(F.col(c))
            exprs.append(F.sum(F.when(is_missing, 1).otherwise(0)).alias(c))

        counts = df.agg(*exprs).collect()[0]
        for c in batch:
            if float(counts[c]) > max_missing:
                drop_cols.append(c)

    if drop_cols:
        LOGGER.info("Dropping %s columns above %.1f%% missing", len(drop_cols), threshold)
        df = df.drop(*drop_cols)
    else:
        LOGGER.info("No columns exceeded missing threshold %.1f%%", threshold)

    return df, drop_cols


def fill_missing_values(df: DataFrame) -> DataFrame:
    _, numeric_cols, string_cols, _ = split_columns(df)

    if numeric_cols:
        numeric_fill = {c: 0.0 for c in numeric_cols}
        df = df.fillna(numeric_fill)
    if string_cols:
        string_fill = {c: "UNKNOWN" for c in string_cols}
        df = df.fillna(string_fill)

    return df


def write_with_pandas_fallback(df: DataFrame, output_path: Path, batch_size: int = 5000) -> None:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    LOGGER.warning("Using streaming pandas/pyarrow fallback writer for %s", output_path)

    remove_existing_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = None
    rows_buffer = []
    columns = df.columns

    try:
        for row in df.toLocalIterator():
            rows_buffer.append(row.asDict(recursive=False))
            if len(rows_buffer) >= batch_size:
                pdf = pd.DataFrame(rows_buffer, columns=columns)
                table = pa.Table.from_pandas(pdf, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(str(output_path), table.schema, compression="snappy")
                writer.write_table(table)
                rows_buffer = []

        if rows_buffer:
            pdf = pd.DataFrame(rows_buffer, columns=columns)
            table = pa.Table.from_pandas(pdf, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(str(output_path), table.schema, compression="snappy")
            writer.write_table(table)

        if writer is None:
            # Handle empty datasets.
            pd.DataFrame(columns=columns).to_parquet(output_path, index=False, compression="snappy")
    finally:
        if writer is not None:
            writer.close()


def process_with_pandas(
    config: ProcessorConfig,
    input_path: Path,
    output_path: Path,
    feature_mode: bool,
) -> Dict[str, Any]:
    import pandas as pd

    LOGGER.warning("Switching to pandas/pyarrow file-level fallback for %s", input_path.name)
    df = pd.read_parquet(input_path)

    summary: Dict[str, Any] = {
        "mode": "pandas_fallback",
        "initial_rows": int(len(df)),
        "initial_cols": int(len(df.columns)),
        "cast_columns_applied": [],
        "cast_columns_skipped": [],
        "rows_dropped_required_nulls": 0,
        "rows_dropped_unlabeled": 0,
        "label_columns": [],
        "rows_removed_dedup": 0,
        "dedup_keys_used": [],
        "dropped_missing_columns": [],
        "encoded_string_columns": 0,
        "outlier_summary": {"method": config.outlier_method, "columns": []},
    }

    validate_required_columns_s = [c for c in config.required_columns if c not in df.columns]
    if validate_required_columns_s:
        raise ValueError(f"Required columns missing: {validate_required_columns_s}")

    for col_name, target_type in config.cast_rules.items():
        if col_name not in df.columns:
            summary["cast_columns_skipped"].append(col_name)
            continue
        try:
            if target_type.lower() in {"int", "integer", "bigint", "long"}:
                df[col_name] = pd.to_numeric(df[col_name], errors="coerce").astype("Int64")
            elif target_type.lower() in {"float", "double", "decimal"}:
                df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
            elif target_type.lower() in {"string", "str"}:
                df[col_name] = df[col_name].astype("string")
            elif target_type.lower() in {"boolean", "bool"}:
                df[col_name] = df[col_name].astype("boolean")
            else:
                df[col_name] = df[col_name].astype(target_type)
            summary["cast_columns_applied"].append(col_name)
        except Exception:
            summary["cast_columns_skipped"].append(col_name)

    if feature_mode:
        label_cols = label_columns(list(df.columns))
        summary["label_columns"] = label_cols
        if label_cols and not df.empty:
            before = len(df)
            mask = pd.Series(True, index=df.index)
            for c in label_cols:
                mask = mask & df[c].notna() & (df[c] != -999)
            df = df[mask]
            summary["rows_dropped_unlabeled"] = int(max(0, before - len(df)))

    if config.required_non_null_columns:
        nn_cols = [c for c in config.required_non_null_columns if c in df.columns]
        if nn_cols:
            before = len(df)
            df = df.dropna(subset=nn_cols)
            summary["rows_dropped_required_nulls"] = int(max(0, before - len(df)))

    sample_fraction = normalize_sample_fraction(config.sample_fraction)
    if sample_fraction < 1.0:
        df = df.sample(frac=sample_fraction, random_state=42)
        if df.empty:
            df = pd.read_parquet(input_path).head(1)

    if feature_mode and not df.empty:
        ids = id_columns(list(df.columns))
        feature_cols = [c for c in df.columns if c not in ids]

        if feature_cols:
            missing_pct = df[feature_cols].isna().mean() * 100.0
            to_drop = list(missing_pct[missing_pct > float(config.missing_threshold)].index)
            if to_drop:
                df = df.drop(columns=to_drop)
                summary["dropped_missing_columns"] = to_drop

        ids = id_columns(list(df.columns))
        feature_cols = [c for c in df.columns if c not in ids]
        numeric_cols = list(df[feature_cols].select_dtypes(include=["number", "bool"]).columns)
        string_cols = [c for c in feature_cols if c not in numeric_cols]

        if numeric_cols:
            df[numeric_cols] = df[numeric_cols].fillna(0.0)
        if string_cols:
            df[string_cols] = df[string_cols].fillna("UNKNOWN")

        # Encode string feature columns to ordinal float64 codes.
        df, enc_cols = encode_string_columns_pandas(df, string_cols)
        summary["encoded_string_columns"] = len(enc_cols)
        # Refresh feature_cols so outlier resolver sees the newly numeric columns.
        ids = id_columns(list(df.columns))
        feature_cols = [c for c in df.columns if c not in ids]

        method = (config.outlier_method or "none").lower()
        outlier_cols = resolve_outlier_columns_pandas(
            df,
            feature_cols,
            config.outlier_columns,
            max_columns=config.outlier_max_columns,
        )
        summary["outlier_summary"] = {"method": method, "columns": outlier_cols, "rows_removed": 0, "columns_capped": 0}

        if method in {"iqr_cap", "iqr_remove"} and outlier_cols:
            if method == "iqr_cap":
                capped = 0
                for c in outlier_cols:
                    q1 = df[c].quantile(0.25)
                    q3 = df[c].quantile(0.75)
                    iqr = q3 - q1
                    if iqr <= 0:
                        # Zero-width band would collapse a constant/imbalanced
                        # column to one value; skip it.
                        continue
                    lb = q1 - config.outlier_iqr_multiplier * iqr
                    ub = q3 + config.outlier_iqr_multiplier * iqr
                    df[c] = df[c].clip(lower=lb, upper=ub)
                    capped += 1
                summary["outlier_summary"]["columns_capped"] = capped
            else:
                before = len(df)
                mask = pd.Series(True, index=df.index)
                for c in outlier_cols:
                    q1 = df[c].quantile(0.25)
                    q3 = df[c].quantile(0.75)
                    iqr = q3 - q1
                    if iqr <= 0:
                        continue
                    lb = q1 - config.outlier_iqr_multiplier * iqr
                    ub = q3 + config.outlier_iqr_multiplier * iqr
                    mask = mask & (df[c].isna() | ((df[c] >= lb) & (df[c] <= ub)))
                df = df[mask]
                summary["outlier_summary"]["rows_removed"] = int(max(0, before - len(df)))

    if config.dedup_keys:
        dedup_cols = [c for c in config.dedup_keys if c in df.columns]
        if dedup_cols:
            before = len(df)
            df = df.drop_duplicates(subset=dedup_cols)
            summary["rows_removed_dedup"] = int(max(0, before - len(df)))
            summary["dedup_keys_used"] = dedup_cols

    remove_existing_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False, compression="snappy")

    summary["final_rows"] = int(len(df))
    summary["final_cols"] = int(len(df.columns))
    return summary


def write_df(df: DataFrame, output_path: Path) -> None:
    rows = df.count()
    cols = len(df.columns)
    partitions = choose_partitions(rows, cols)

    temp_output_dir = output_path.with_name(f"{output_path.stem}__spark_tmp")

    remove_existing_path(output_path)
    remove_existing_path(temp_output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Writing output: rows=%s cols=%s partitions=%s", rows, cols, partitions)

    current_parts = df.rdd.getNumPartitions()
    if current_parts > partitions:
        writer_df = df.coalesce(partitions)
    else:
        writer_df = df.repartition(partitions)

    # Write to a temporary Spark dataset, then extract a single named parquet file.
    writer_df.coalesce(1).write.mode("overwrite").parquet(str(temp_output_dir))

    part_files = list(temp_output_dir.glob("part-*.parquet"))
    if not part_files:
        raise RuntimeError(f"No parquet part file found in temporary output: {temp_output_dir}")

    shutil.move(str(part_files[0]), str(output_path))
    remove_existing_path(temp_output_dir)


# ------------------------------------------------------------
# Processing modes
# ------------------------------------------------------------

def passthrough_mode(
    spark: SparkSession,
    config: ProcessorConfig,
    input_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    LOGGER.info("File classified as metadata/support table; passthrough mode")
    df = load_df(spark, input_path)

    summary: Dict[str, Any] = {
        "mode": "spark_passthrough",
        "initial_rows": df.count(),
        "initial_cols": len(df.columns),
        "cast_columns_applied": [],
        "cast_columns_skipped": [],
        "rows_dropped_required_nulls": 0,
        "rows_removed_dedup": 0,
        "dedup_keys_used": [],
        "dropped_missing_columns": [],
        "outlier_summary": {"method": "none", "columns": []},
    }

    validate_required_columns(df, config.required_columns)
    df, applied_casts, skipped_casts = apply_cast_rules_spark(df, config.cast_rules)
    summary["cast_columns_applied"] = applied_casts
    summary["cast_columns_skipped"] = skipped_casts

    df, dropped_required_nulls = drop_rows_with_nulls(df, config.required_non_null_columns)
    summary["rows_dropped_required_nulls"] = dropped_required_nulls

    df = apply_sampling(df, config.sample_fraction)

    df, dedup_removed, dedup_keys_used = apply_deduplication(df, config.dedup_keys)
    summary["rows_removed_dedup"] = dedup_removed
    summary["dedup_keys_used"] = dedup_keys_used

    summary["final_rows"] = df.count()
    summary["final_cols"] = len(df.columns)
    write_df(df, output_path)
    return summary


def feature_matrix_mode(
    spark: SparkSession,
    config: ProcessorConfig,
    input_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    LOGGER.info("File classified as feature matrix; transform mode")

    df = load_df(spark, input_path)
    _initial_rows = df.count()
    _initial_cols = len(df.columns)
    LOGGER.info("Initial shape: rows=%s cols=%s", _initial_rows, _initial_cols)

    summary: Dict[str, Any] = {
        "mode": "spark_feature_matrix",
        "initial_rows": _initial_rows,
        "initial_cols": _initial_cols,
        "cast_columns_applied": [],
        "cast_columns_skipped": [],
        "rows_dropped_required_nulls": 0,
        "rows_dropped_unlabeled": 0,
        "label_columns": [],
        "rows_removed_dedup": 0,
        "dedup_keys_used": [],
        "dropped_missing_columns": [],
        "encoded_string_columns": 0,
        "outlier_summary": {"method": "none", "columns": []},
    }

    validate_required_columns(df, config.required_columns)
    df, applied_casts, skipped_casts = apply_cast_rules_spark(df, config.cast_rules)
    summary["cast_columns_applied"] = applied_casts
    summary["cast_columns_skipped"] = skipped_casts

    df, dropped_unlabeled, label_cols = drop_unlabeled_rows_spark(df)
    summary["rows_dropped_unlabeled"] = dropped_unlabeled
    summary["label_columns"] = label_cols

    df, dropped_required_nulls = drop_rows_with_nulls(df, config.required_non_null_columns)
    summary["rows_dropped_required_nulls"] = dropped_required_nulls

    df = apply_sampling(df, config.sample_fraction)
    _, _, _, schema_map = split_columns(df)

    df, dropped_cols = drop_high_missing_columns(df, config.missing_threshold, schema_map)
    summary["dropped_missing_columns"] = dropped_cols

    # Keep transformations minimal to avoid very wide-plan blowups.
    df = fill_missing_values(df)

    # Encode remaining string feature columns to ordinal doubles so all
    # downstream ML steps receive an all-numeric feature matrix.
    _, _, string_feature_cols, _ = split_columns(df)
    df, enc_cols = encode_string_columns_spark(df, string_feature_cols)
    summary["encoded_string_columns"] = len(enc_cols)

    df, outlier_summary = apply_outlier_strategy_spark(
        df,
        config.outlier_method,
        config.outlier_columns,
        config.outlier_iqr_multiplier,
        config.outlier_max_columns,
    )
    summary["outlier_summary"] = outlier_summary

    df, dedup_removed, dedup_keys_used = apply_deduplication(df, config.dedup_keys)
    summary["rows_removed_dedup"] = dedup_removed
    summary["dedup_keys_used"] = dedup_keys_used

    LOGGER.info("Final shape: rows=%s cols=%s", df.count(), len(df.columns))
    summary["final_rows"] = df.count()
    summary["final_cols"] = len(df.columns)
    write_df(df, output_path)
    return summary


def build_schema_contract(spark: SparkSession, output_path: Path) -> Dict[str, Any]:
    out_df = load_df(spark, output_path)
    schema = [{"name": f.name, "type": f.dataType.simpleString()} for f in out_df.schema.fields]
    return {
        "rows": out_df.count(),
        "columns": len(out_df.columns),
        "schema": schema,
    }


def resolve_quality_report_path(config: ProcessorConfig, output_path: Path) -> Path:
    if config.quality_report_file:
        return Path(config.quality_report_file)
    return output_path.with_name(f"{output_path.stem}_quality_report.json")


def resolve_schema_contract_path(config: ProcessorConfig, output_path: Path) -> Path:
    if config.schema_contract_file:
        return Path(config.schema_contract_file)
    return output_path.with_name(f"{output_path.stem}_schema_contract.json")


# ------------------------------------------------------------
# Runner
# ------------------------------------------------------------

def run_processor(config: ProcessorConfig) -> bool:
    started = time.time()

    input_path = Path(config.input_dir) / config.input_file
    output_path = Path(config.output_dir) / config.output_file
    metadata = read_metadata(Path(config.input_dir))

    if not input_path.exists():
        LOGGER.error("Input file not found: %s", input_path)
        return False

    try:
        size_mb = get_file_size_mb(input_path)
        LOGGER.info("Input: %s (%.2f MB)", input_path.name, size_mb)
    except Exception as exc:
        LOGGER.warning("Could not read input size: %s", exc)

    spark = create_spark()
    process_summary: Dict[str, Any] = {}
    fallback_used = False
    feature_mode = False

    try:
        feature_mode = is_feature_matrix(config.input_file, metadata)

        if feature_mode:
            try:
                process_summary = feature_matrix_mode(spark, config, input_path, output_path)
            except Exception:
                LOGGER.exception("Spark feature processing failed")
                fallback_used = True
                process_summary = process_with_pandas(config, input_path, output_path, feature_mode=True)
        else:
            try:
                process_summary = passthrough_mode(spark, config, input_path, output_path)
            except Exception:
                LOGGER.exception("Spark passthrough processing failed")
                fallback_used = True
                process_summary = process_with_pandas(config, input_path, output_path, feature_mode=False)

        contract = build_schema_contract(spark, output_path)
        contract_payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "input_file": config.input_file,
            "output_file": config.output_file,
            "feature_mode": feature_mode,
            "fallback_used": fallback_used,
            "contract": contract,
        }
        schema_contract_path = resolve_schema_contract_path(config, output_path)
        write_json(schema_contract_path, contract_payload)

        quality_payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "input_file": config.input_file,
            "output_file": config.output_file,
            "feature_mode": feature_mode,
            "fallback_used": fallback_used,
            "sample_fraction": config.sample_fraction,
            "missing_threshold": config.missing_threshold,
            "cast_rules": config.cast_rules,
            "required_columns": config.required_columns,
            "required_non_null_columns": config.required_non_null_columns,
            "dedup_keys": config.dedup_keys,
            "outlier_method": config.outlier_method,
            "outlier_columns": config.outlier_columns,
            "outlier_iqr_multiplier": config.outlier_iqr_multiplier,
            "outlier_max_columns": config.outlier_max_columns,
            "summary": process_summary,
            "output_schema_contract": str(schema_contract_path),
        }
        quality_report_path = resolve_quality_report_path(config, output_path)
        write_json(quality_report_path, quality_payload)

        elapsed = (time.time() - started) / 60.0
        out_mb = get_file_size_mb(output_path)

        LOGGER.info("Processing complete in %.2f minutes", elapsed)
        LOGGER.info("Output path: %s", output_path)
        LOGGER.info("Output size: %.2f MB", out_mb)
        LOGGER.info("Quality report: %s", quality_report_path)
        LOGGER.info("Schema contract: %s", schema_contract_path)
        LOGGER.info("Log file: %s", LOG_PATH)
        return True
    except Exception as exc:
        LOGGER.exception("Processing failed: %s", exc)
        return False
    finally:
        spark.stop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Credit Risk data processor")
    parser.add_argument("--file", required=True, help="Input parquet filename")
    parser.add_argument("--output", required=True, help="Output parquet filename")
    parser.add_argument("--sample", type=float, default=1.0, help="Sample fraction in range [0,1]")
    parser.add_argument("--missing-threshold", type=float, default=60.0, help="Drop feature columns above this missing percent")
    parser.add_argument("--input-dir", default="data/interim", help="Input directory")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    parser.add_argument("--cast-rules", default="", help="JSON object or JSON file path mapping column names to target types")
    parser.add_argument("--required-columns", default="", help="Comma-separated columns that must exist")
    parser.add_argument("--required-non-null", default="", help="Comma-separated columns that must be non-null")
    parser.add_argument("--dedup-keys", default="", help="Comma-separated keys for deduplication")
    parser.add_argument("--outlier-method", choices=["none", "iqr_cap", "iqr_remove"], default="none", help="Outlier handling method")
    parser.add_argument("--outlier-columns", default="", help="Comma-separated numeric columns for outlier handling")
    parser.add_argument("--outlier-iqr-multiplier", type=float, default=1.5, help="IQR multiplier for outlier bounds")
    parser.add_argument("--outlier-max-columns", type=int, default=300, help="Max auto-selected numeric columns for outlier handling; <=0 means all")
    parser.add_argument("--quality-report-file", default="", help="Path to write quality report JSON")
    parser.add_argument("--schema-contract-file", default="", help="Path to write schema contract JSON")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    try:
        cast_rules = parse_json_map(args.cast_rules)
    except Exception as exc:
        LOGGER.error("Invalid --cast-rules: %s", exc)
        sys.exit(2)

    config = ProcessorConfig(
        input_file=args.file,
        output_file=args.output,
        sample_fraction=args.sample,
        missing_threshold=args.missing_threshold,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        cast_rules=cast_rules,
        required_columns=parse_csv_list(args.required_columns),
        required_non_null_columns=parse_csv_list(args.required_non_null),
        dedup_keys=parse_csv_list(args.dedup_keys),
        outlier_method=args.outlier_method,
        outlier_columns=parse_csv_list(args.outlier_columns),
        outlier_iqr_multiplier=float(args.outlier_iqr_multiplier),
        outlier_max_columns=int(args.outlier_max_columns),
        quality_report_file=args.quality_report_file,
        schema_contract_file=args.schema_contract_file,
    )

    ok = run_processor(config)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
