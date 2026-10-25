"""
train.py - trains the drowsiness model and compares it with the rule-based detector.

    python train.py recordings          (real data from record.py)
    python train.py recordings_sim      (practice data, pipeline test only)

Classes come from the file label:  open -> alert,  slow -> drowsy,  closed -> severe
Split: whole RECORDINGS are held out for testing (never part of one recording in both
train and test), otherwise the score would be fake-high.
Saves: model.joblib   and prints the confusion matrix and rule-based comparison.
"""
import glob
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

import features as F

CLASSES = {"open": "alert", "slow": "drowsy", "closed": "severe"}
ORDER = ["alert", "drowsy", "severe"]
BINARY = "binary" in sys.argv          # python train.py recordings binary  -> alert vs drowsy only
if BINARY:
    CLASSES = {"open": "alert", "slow": "drowsy", "closed": "drowsy"}
    ORDER = ["alert", "drowsy"]


def rule_based(row):
    """The current detector: closed >= 2 s severe, >= 1 s drowsy, else alert."""
    if BINARY:
        return "drowsy" if row.longest_closure >= 1.0 else "alert"
    if row.longest_closure >= 2.0:
        return "severe"
    if row.longest_closure >= 1.0:
        return "drowsy"
    return "alert"


def main():
    args = [a for a in sys.argv[1:] if a != "binary"]
    folder = args[0] if args else "recordings"
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        sys.exit(f"No .csv files in {folder}")
    parts = []
    for path in files:
        label = os.path.basename(path).split("_")[0]
        if label not in CLASSES:
            print("skipping (label not open/slow/closed):", os.path.basename(path))
            continue
        df = F.load_recording(path)
        if len(df) < 1500:      # needs at least 15 s of readings at 100 per second
            print(f"skipping (only {len(df)} readings, delete it): {os.path.basename(path)}")
            continue
        parts.append(F.window_features(df, CLASSES[label], os.path.basename(path)))
    if not parts:
        sys.exit("No usable recordings found.")
    data = pd.concat(parts, ignore_index=True)
    print(f"{len(parts)} recordings used -> {len(data)} windows")
    print(data["label"].value_counts().to_string(), "\n")

    X, y, groups = data[F.FEATURES].values, data["label"].values, data["source"].values
    majority = pd.Series(y).value_counts(normalize=True).max()
    print(f"Guessing the most common class every time would score {majority:.3f}  <- the number to beat\n")
    n_splits = min(4, len(set(groups)))
    models = {
        "logistic regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "decision tree": DecisionTreeClassifier(max_depth=4, random_state=0),
        "random forest": RandomForestClassifier(n_estimators=200, max_depth=6, random_state=0),
    }
    pred = {name: np.empty(len(y), dtype=object) for name in models}
    pred["rule-based (1 s / 2 s)"] = np.array([rule_based(r) for r in data.itertuples()])
    for train, test in GroupKFold(n_splits=n_splits).split(X, y, groups):
        for name, m in models.items():
            m.fit(X[train], y[train])
            pred[name][test] = m.predict(X[test])

    print(f"Cross-validated on held-out recordings ({n_splits} folds):")
    best, best_acc = None, -1
    for name, p in pred.items():
        acc = float((p == y).mean())
        print(f"  {name:24s} accuracy {acc:.3f}")
        if name in models and acc > best_acc:
            best, best_acc = name, acc
    print(f"\nBest model: {best}\nConfusion matrix (rows = true, columns = predicted; {ORDER}):")
    print(confusion_matrix(y, pred[best], labels=ORDER))
    print("\n", classification_report(y, pred[best], labels=ORDER, zero_division=0))
    print("Rule-based confusion matrix for comparison:")
    print(confusion_matrix(y, pred["rule-based (1 s / 2 s)"], labels=ORDER))

    final = models[best].fit(X, y)
    joblib.dump({"model": final, "features": F.FEATURES, "classes": ORDER}, "model.joblib")
    print("\nSaved model.joblib")
    if best == "random forest" or best == "decision tree":
        imp = pd.Series(final.feature_importances_, index=F.FEATURES).sort_values(ascending=False)
        print("\nWhat the model relies on most:\n", imp.round(3).to_string())


if __name__ == "__main__":
    main()
