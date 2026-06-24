# Credit Risk ML System

End-to-end credit risk prediction project for the Home Credit Default Risk dataset.

## What is included

- PySpark ETL pipeline in `pyspark/data_processor.py`
- Model training in `ml/train_model.py`
- FastAPI backend in `api/main.py`
- React dashboard in `frontend/`

## Run locally

Activate your virtual environment first, then run the commands from the project root.

Backend:

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
Set-Location frontend
npm install
npm run dev -- --host 127.0.0.1
```

## Train the model

```powershell
python ml/train_model.py
```

## API endpoints

- `GET /health`
- `GET /metrics`
- `POST /predict`

## Notes

- The frontend sends a curated subset of the processed schema.
- The API aligns missing fields to the trained model pipeline.