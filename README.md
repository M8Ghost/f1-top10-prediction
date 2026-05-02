# f1-top10-prediction

V0 pipeline for predicting whether a Formula 1 driver finishes in the top 10.

## Data source

Raw data is fetched from the Jolpica F1 API, an Ergast-compatible public API:
https://github.com/jolpica/jolpica-f1

The V0 importer uses Jolpica for race results, qualifying, drivers, constructors,
circuits and historical standings-derived features. Weather, race-control,
pit-stop and telemetry features are currently V0 placeholders or derived proxies
when the public API does not provide the exact signal.

## Setup

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the full V0

```powershell
python generate_raw_data.py --start-year 2018 --end-year 2026
python generate_final_dataset.py
python train_model.py
```

Main outputs:

- `data/raw/*.csv`: fetched and derived raw feature tables
- `data/final/f1_top10_model_dataset.csv`: model-ready dataset
- `outputs/models/top10_classifier.joblib`: trained model
- `outputs/metrics.json`: validation metrics
- `outputs/figures/*.png`: EDA and model figures
