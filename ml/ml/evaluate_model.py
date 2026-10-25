"""
evaluate_model.py - scores the SAVED model (model.joblib) on recordings it has never seen.

Use it for a fair test:
  1. train on session 1:      python train.py recordings          (or: python train.py recordings binary)
  2. record session 2 into a NEW folder, e.g. recordings_day2  (do NOT train on it)
  3. test:                    python evaluate_model.py recordings_day2

The model is the last one train.py saved. If it was trained with "binary" it has two classes
(alert / drowsy); otherwise three (alert / drowsy / severe). The rule-based detector
(closed 1 s = drowsy, 2 s = severe) is scored on the same windows for comparison.
"""
import glob
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report

import features as F

folder = sys.argv[1] if len(sys.argv) > 1 else "recordings_day2"
bundle = joblib.load("model.joblib")
model, feats, classes = bundle["model"], bundle["features"], bundle["classes"]
binary = len(classes) == 2
label_map = ({"open": "alert", "slow": "drowsy", "closed": "drowsy"} if binary
             else {"open": "alert", "slow": "drowsy", "closed": "severe"})

parts = []
for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
    name = os.path.basename(path)
    label = name.split("_")[0]
    if label not in label_map:
        continue
    df = F.load_recording(path)
    if len(df) < 1500:
        print("skipping (too short):", name)
        continue
    parts.append(F.window_features(df, label_map[label], name))
if not parts:
    sys.exit(f"No open/slow/closed recordings found in {folder}")

data = pd.concat(parts, ignore_index=True)
y = data["label"].values
pred = model.predict(data[feats].values)


def rules(r):
    if binary:
        return "drowsy" if r.longest_closure >= 1.0 else "alert"
    return "severe" if r.longest_closure >= 2.0 else ("drowsy" if r.longest_closure >= 1.0 else "alert")


rule_pred = np.array([rules(r) for r in data.itertuples()])
majority = pd.Series(y).value_counts(normalize=True).max()
print(f"{len(parts)} recordings, {len(data)} windows from {folder}")
print(f"Guessing the most common class: {majority:.3f}")
print(f"Model accuracy:       {(pred == y).mean():.3f}")
print(f"Rule-based accuracy:  {(rule_pred == y).mean():.3f}\n")
print(f"Model confusion matrix (rows = true, columns = predicted; {classes}):")
print(confusion_matrix(y, pred, labels=classes))
print("\nRule-based confusion matrix:")
print(confusion_matrix(y, rule_pred, labels=classes))
print("\n", classification_report(y, pred, labels=classes, zero_division=0))
