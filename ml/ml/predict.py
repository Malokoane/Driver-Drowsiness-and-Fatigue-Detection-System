"""
predict.py - runs the trained model on a recording, window by window.

    python predict.py recordings/closed_20261022_210000.csv
"""
import sys

import joblib

import features as F

bundle = joblib.load("model.joblib")
df = F.load_recording(sys.argv[1])
w = F.window_features(df, "?", sys.argv[1])
pred = bundle["model"].predict(w[bundle["features"]].values)
for i, (p, r) in enumerate(zip(pred, w.itertuples())):
    print(f"window {i + 1} (starts {i * F.STEP_S:>4.0f} s): {p:7s}  "
          f"perclos {r.perclos:.2f}  longest closure {r.longest_closure:.1f} s  "
          f"blinks/min {r.blink_rate:.0f}")
