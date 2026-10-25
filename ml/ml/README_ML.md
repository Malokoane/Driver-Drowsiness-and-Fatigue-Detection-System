# Drowsiness model (AI/ML part)

1. Record real data with `record.py` (folder `recordings/`, files named `open_*`, `slow_*`, `closed_*`).
2. `python train.py recordings`  -> trains 3 models, compares them with the rule-based detector, saves `model.joblib`.
3. `python predict.py recordings/<file>.csv`  -> model output per 10 s window.

`make_sim_data.py` makes practice data to test the pipeline. Scores on it mean nothing.
pip install: pandas numpy scikit-learn joblib
