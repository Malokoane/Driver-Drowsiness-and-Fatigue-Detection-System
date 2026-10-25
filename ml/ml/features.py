"""
features.py - turns a recording (ms, adc) into numbers a model can learn from.

Steps
  1. closed / open per reading: closed when the value falls below the midpoint
     between this recording's "open" level and "closed" level (so it works even if
     the open level is not exactly 4095 on another face or in other light).
  2. find closures (runs of closed readings) and their length in seconds
  3. cut the recording into windows (default 10 s, every 5 s) and describe each one:
        perclos         share of the window the eye was closed (0-1)
        blink_rate      closures of 0.1-1.0 s, per minute
        longest_closure longest closure in the window (s)
        mean_closure    average closure length (s)
        long_closures   number of closures of 1 s or more
        mean_level      average sensor value / open level (0-1), shows half-closed eyes
"""
import numpy as np
import pandas as pd

WINDOW_S = 10.0
STEP_S = 5.0
FEATURES = ["perclos", "blink_rate", "longest_closure", "mean_closure",
            "long_closures", "mean_level"]


def load_recording(path):
    df = pd.read_csv(path)
    df = df.dropna().astype({"ms": float, "adc": float})
    return df


RATIO = 0.80          # closed = below 80 % of the recent "open" level
BASELINE_S = 20.0     # the open level is tracked over the last 20 s (handles drift)
HZ = 100


def detect_closed(adc):
    """
    Returns (closed, level, baseline) for one recording.
    The sensor numbers move between sessions and drift, so nothing is fixed:
      baseline = recent "open" level = 85th percentile of the last 20 s
      closed   = smoothed reading below 80 % of that baseline
    Direction: closed eye = LOWER reading (confirmed on the real glasses).
    """
    x = pd.Series(adc, dtype=float)
    sm = x.rolling(5, center=True, min_periods=1).median()          # removes single-sample spikes
    win = int(BASELINE_S * HZ)
    base = sm.rolling(win, min_periods=1).quantile(0.85)
    base = base.bfill()
    closed = (sm < RATIO * base).values
    level = np.clip((sm / base).values, 0, 1.5)
    return closed, level, base.values


def closures(ms, closed):
    """List of (start_s, length_s) for every run of closed readings."""
    out, start = [], None
    for t, c in zip(ms, closed):
        if c and start is None:
            start = t
        elif not c and start is not None:
            out.append((start / 1000.0, (t - start) / 1000.0))
            start = None
    if start is not None:
        out.append((start / 1000.0, (ms[-1] - start) / 1000.0))
    return out


def window_features(df, label, source, window_s=WINDOW_S, step_s=STEP_S):
    ms, adc = df["ms"].values, df["adc"].values
    closed, level, _ = detect_closed(adc)
    cl = closures(ms, closed)
    t0, t1 = ms[0] / 1000.0, ms[-1] / 1000.0
    rows, start = [], t0
    while start + window_s <= t1 + 1e-9:
        end = start + window_s
        in_win = (ms / 1000.0 >= start) & (ms / 1000.0 < end)
        lens = []
        for s, length in cl:                       # clip closures to the window
            a, b = max(s, start), min(s + length, end)
            if b > a:
                lens.append(b - a)
        blinks = [x for x in lens if 0.1 <= x < 1.0]
        rows.append({
            "perclos": float(closed[in_win].mean()) if in_win.any() else 0.0,
            "blink_rate": len(blinks) * 60.0 / window_s,
            "longest_closure": max(lens) if lens else 0.0,
            "mean_closure": float(np.mean(lens)) if lens else 0.0,
            "long_closures": sum(1 for x in lens if x >= 1.0),
            "mean_level": float(level[in_win].mean()) if in_win.any() else 1.0,
            "label": label, "source": source,
        })
        start += step_s
    return pd.DataFrame(rows)
