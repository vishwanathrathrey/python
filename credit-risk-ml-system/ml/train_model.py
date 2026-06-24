#!/usr/bin/env python3
"""Train credit risk models from the processed feature matrix."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "feature_matrix_processed.parquet"
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "credit_model.pkl"
METRICS_PATH = MODELS_DIR / "credit_model_metrics.json"
RANDOM_STATE = 42


def load_feature_matrix(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the processed feature matrix with pandas."""
    if not path.exists():
        raise FileNotFoundError(f"Processed parquet not found: {path}")

    return pd.read_parquet(path)


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split the feature matrix into model features and target label."""
    required_columns = {"fm_target", "fm_client_id"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise KeyError(f"Missing required columns: {missing_list}")

    label_like_columns = [column for column in df.columns if column.startswith("fm_") and column.endswith(("target", "set"))]
    feature_drop_columns = ["fm_client_id", *label_like_columns]
    X = df.drop(columns=feature_drop_columns)
    y = df["fm_target"]
    return X, y


def validate_target(y: pd.Series) -> None:
    """Ensure the target can support binary classification training."""
    target_counts = y.value_counts(dropna=False)
    if target_counts.shape[0] < 2:
        raise ValueError(
            "Target column fm_target contains only one class. "
            "Regenerate the processed dataset with a valid binary target before training."
        )

    if (target_counts < 2).any():
        raise ValueError(
            "Each target class must contain at least two rows for stratified training and testing."
        )


def build_models() -> dict[str, Pipeline]:
    """Build candidate training pipelines for step 3."""
    logistic_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=None,
                ),
            ),
        ]
    )

    random_forest_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    class_weight="balanced_subsample",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    return {
        "logistic_regression": logistic_pipeline,
        "random_forest": random_forest_pipeline,
    }


def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, object]:
    """Generate evaluation metrics for a trained model."""
    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    return {
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "classification_report": classification_report(
            y_test, predictions, zero_division=0, output_dict=True
        ),
    }


def train_and_select_best_model(X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.Series, y_test: pd.Series) -> tuple[str, Pipeline, dict[str, dict[str, object]]]:
    """Train candidate models and return the best one by ROC-AUC."""
    model_candidates = build_models()
    results: dict[str, dict[str, object]] = {}
    best_model_name = ""
    best_model: Pipeline | None = None
    best_roc_auc = float("-inf")

    for model_name, pipeline in model_candidates.items():
        pipeline.fit(X_train, y_train)
        metrics = evaluate_model(pipeline, X_test, y_test)
        results[model_name] = metrics

        if metrics["roc_auc"] > best_roc_auc:
            best_roc_auc = metrics["roc_auc"]
            best_model_name = model_name
            best_model = pipeline

    if best_model is None:
        raise RuntimeError("No model could be trained successfully.")

    return best_model_name, best_model, results


def save_artifacts(model_name: str, model: Pipeline, metrics: dict[str, dict[str, object]], X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.Series, y_test: pd.Series) -> None:
    """Persist the winning model and metrics for downstream API use."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    payload = {
        "selected_model": model_name,
        "model_path": str(MODEL_PATH),
        "train_shape": [int(X_train.shape[0]), int(X_train.shape[1])],
        "test_shape": [int(X_test.shape[0]), int(X_test.shape[1])],
        "train_target_distribution": y_train.value_counts().to_dict(),
        "test_target_distribution": y_test.value_counts().to_dict(),
        "metrics": metrics,
    }
    with METRICS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def main() -> None:
    df = load_feature_matrix()
    X, y = split_features_target(df)
    validate_target(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    best_model_name, best_model, metrics = train_and_select_best_model(
        X_train, X_test, y_train, y_test
    )
    save_artifacts(best_model_name, best_model, metrics, X_train, X_test, y_train, y_test)

    print(f"Loaded feature matrix: {df.shape}")
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    print(f"Selected model: {best_model_name}")
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved metrics to: {METRICS_PATH}")


if __name__ == "__main__":
    main()