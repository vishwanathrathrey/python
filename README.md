# Python Data Projects Portfolio

This repository contains data analysis, machine learning, and backend data pipeline projects.

## Repository Projects

1. Car Price Prediction
	- Folder: Car Price
	- Focus: Regression modeling for car price estimation

2. CardioRisk Prediction
	- Folder: CardioRisk
	- Focus: Cardiovascular disease risk classification

3. File Handling
	- Folder: File Handling
	- Focus: CSV processing and Python file operations

4. Flight Data Analysis
	- Folder: Flight Mini assignmrnt
	- Focus: Exploratory data analysis of flight records

5. Lung Cancer Analysis
	- Folder: Lung Cancer Mini Assignment
	- Focus: Patient health data exploration

6. NYC Taxi Analysis
	- Folder: NYC Taxi Analysis
	- Focus: EDA on NYC taxi trips

7. Traffic Data ETL
	- Folder: Traffic Data Analysis
	- Focus: ETL and analysis of traffic collision data

8. Customer Data Pipeline
	- Folder: customer-data-pipeline
	- Focus: Containerized ingestion pipeline using Flask, FastAPI, and PostgreSQL

9. Credit Risk ML System
	- Folder: credit-risk-ml-system
	- Focus: End-to-end credit risk prediction system with PySpark ETL, model training, FastAPI, and a React dashboard

## What Is Inside Each Project

Notebook-based projects typically include:

- A Jupyter notebook
- A project-level README
- Sample data under data/sample
- Some projects use a full dataset under data/ instead of a sample file

The backend pipeline project includes:

- Docker Compose setup
- Service source code for mock API and pipeline API
- Project-level README with API and run instructions

## Quick Start

### Notebook Projects

1. Open a terminal at the repository root.
2. Launch Jupyter for a notebook, for example:

```bash
jupyter notebook "CardioRisk/CardioRisk_Prediction.ipynb"
jupyter notebook "Car Price/CarPricePrediction.ipynb"
```

### Customer Data Pipeline

1. Move to the project folder:

```bash
cd customer-data-pipeline
```

2. Start services:

```bash
docker-compose up -d --build
```

3. Check health:

```bash
curl http://localhost:5000/api/health
curl http://localhost:8000/api/health
```

### Credit Risk ML System

1. Move to the project folder:

```bash
cd credit-risk-ml-system
```

2. Start the API and frontend locally:

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

3. Train the model if needed:

```bash
python ml/train_model.py
```

## Data Notes

- This repository includes sample datasets for learning and demonstration.
- Full production datasets are not included.
- The credit risk project uses the Home Credit Default Risk dataset from Kaggle and stores its data notes in `credit-risk-ml-system/data/README.md`.
