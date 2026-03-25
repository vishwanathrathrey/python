# Python Data Projects Portfolio

This repository contains data analysis, machine learning, and backend data pipeline projects.

## Repository Projects

1. Car Price Prediction
	- Folder: Car Price
	- Focus: Regression modeling for car price estimation

2. File Handling
	- Folder: File Handling
	- Focus: CSV processing and Python file operations

3. Flight Data Analysis
	- Folder: Flight Mini assignmrnt
	- Focus: Exploratory data analysis of flight records

4. Lung Cancer Analysis
	- Folder: Lung Cancer Mini Assignment
	- Focus: Patient health data exploration

5. NYC Taxi Analysis
	- Folder: NYC Taxi Analysis
	- Focus: EDA on NYC taxi trips

6. Traffic Data ETL
	- Folder: Traffic Data Analysis
	- Focus: ETL and analysis of traffic collision data

7. Customer Data Pipeline
	- Folder: customer-data-pipeline
	- Focus: Containerized ingestion pipeline using Flask, FastAPI, and PostgreSQL

## What Is Inside Each Project

Notebook-based projects typically include:

- A Jupyter notebook
- A project-level README
- Sample data under data/sample

The backend pipeline project includes:

- Docker Compose setup
- Service source code for mock API and pipeline API
- Project-level README with API and run instructions

## Quick Start

### Notebook Projects

1. Open a terminal at the repository root.
2. Launch Jupyter for a notebook, for example:

```bash
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

## Data Notes

- This repository includes sample datasets for learning and demonstration.
- Full production datasets are not included.
