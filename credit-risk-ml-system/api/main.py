"""FastAPI service for credit risk prediction."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "credit_model.pkl"
METRICS_PATH = PROJECT_ROOT / "models" / "credit_model_metrics.json"
FEATURE_MATRIX_PATH = PROJECT_ROOT / "data" / "processed" / "feature_matrix_processed.parquet"
DEFAULT_LOW_RISK_THRESHOLD = 0.33
DEFAULT_HIGH_RISK_THRESHOLD = 0.66


app = FastAPI(title="Credit Risk Prediction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    """Incoming feature payload for one applicant."""

    features: dict[str, Any] = Field(default_factory=dict)


class PredictResponse(BaseModel):
    """Prediction payload returned by the API."""

    default_probability: float
    risk_level: str
    selected_model: str
    missing_feature_count: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    feature_count: int


def _is_label_like(column_name: str) -> bool:
    lower_name = column_name.lower()
    return lower_name.startswith("fm_") and lower_name.endswith(("target", "set"))


@lru_cache(maxsize=1)
def get_feature_columns() -> tuple[str, ...]:
    """Infer the trained feature columns from the processed parquet schema."""
    if not FEATURE_MATRIX_PATH.exists():
        raise FileNotFoundError(f"Feature matrix not found: {FEATURE_MATRIX_PATH}")

    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - dependency issue is environment-specific
        raise RuntimeError("pyarrow is required to inspect the parquet schema") from exc

    parquet_file = pq.ParquetFile(FEATURE_MATRIX_PATH)
    columns = [name for name in parquet_file.schema.names if name != "fm_client_id" and not _is_label_like(name)]
    return tuple(columns)


@lru_cache(maxsize=1)
def get_model_bundle() -> dict[str, Any]:
    """Load the trained model and its saved metrics."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")
    if not METRICS_PATH.exists():
        raise FileNotFoundError(f"Metrics artifact not found: {METRICS_PATH}")

    model = joblib.load(MODEL_PATH)
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return {"model": model, "metrics": metrics}


def risk_level_from_probability(probability: float) -> str:
    """Map a probability to a simple risk band for the dashboard."""
    if probability < DEFAULT_LOW_RISK_THRESHOLD:
        return "low"
    if probability < DEFAULT_HIGH_RISK_THRESHOLD:
        return "medium"
    return "high"


def build_model_input(features: dict[str, Any]) -> pd.DataFrame:
    """Align an incoming feature payload to the trained feature schema."""
    expected_columns = list(get_feature_columns())
    row = {column: None for column in expected_columns}

    for key, value in features.items():
        if key in row:
            row[key] = value

    frame = pd.DataFrame([row], columns=expected_columns)
    frame = frame.apply(pd.to_numeric, errors="coerce")
    return frame


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a minimal liveness/readiness signal."""
    feature_count = len(get_feature_columns())
    _ = get_model_bundle()
    return HealthResponse(status="ok", model_loaded=True, feature_count=feature_count)


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    """Return the saved training metrics for the dashboard."""
    return get_model_bundle()["metrics"]


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Score one applicant using the trained model pipeline."""
    bundle = get_model_bundle()
    model = bundle["model"]

    model_input = build_model_input(request.features)
    missing_feature_count = int(model_input.isna().sum(axis=1).iloc[0])

    try:
        probability = float(model.predict_proba(model_input)[:, 1][0])
    except Exception as exc:  # pragma: no cover - runtime model errors are surfaced to the client
        raise HTTPException(status_code=400, detail=f"Unable to score request: {exc}") from exc

    return PredictResponse(
        default_probability=probability,
        risk_level=risk_level_from_probability(probability),
        selected_model=str(bundle["metrics"].get("selected_model", "unknown")),
        missing_feature_count=missing_feature_count,
    )
