"""
record.py - saves labelled eye-sensor recordings from the ESP32 (record_adc.ino).

Install once:   pip install pyserial
Run:            python record.py COM3 open 30
                         ^port  ^label ^seconds

Labels to record (30 s each, wearing the glasses, repeat each 2-3 times):
    open     eyes open, blinking normally
    slow     slow, heavy blinks / sleepy eyes
    closed   eyes closed for 2-3 s, open for 2 s, repeat
Files are saved in the folder "recordings" as  label_YYYYmmdd_HHMMSS.csv
"""
import csv
import os
import sys
import time
from datetime import datetime

import serial

if len(sys.argv) != 4:
    sys.exit(__doc__)
port, label, seconds = sys.argv[1], sys.argv[2], float(sys.argv[3])

os.makedirs("recordings", exist_ok=True)
path = os.path.join("recordings", f"{label}_{datetime.now():%Y%m%d_%H%M%S}.csv")

ser = serial.Serial(port, 115200, timeout=1)
time.sleep(2)               # the ESP32 restarts when the port opens
ser.reset_input_buffer()

for n in (3, 2, 1):
    print(f"Starting '{label}' in {n}...")
    time.sleep(1)
print("RECORDING - go!")

rows, start = 0, time.time()
with open(path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ms", "adc", "label"])
    while time.time() - start < seconds:
        line = ser.readline().decode(errors="ignore").strip()
        parts = line.split(",")
        if len(parts) != 2 or not (parts[0].isdigit() and parts[1].isdigit()):
            continue        # skips "# ms,adc" and half lines
        w.writerow([parts[0], parts[1], label])
        rows += 1
        if rows % 100 == 0:
            print(f"  {rows // 100} s, last value {parts[1]}")
ser.close()
print(f"Saved {rows} readings to {path}")
if rows < seconds * 50:
    print("WARNING: fewer readings than expected. Is the Serial Monitor closed and the right port chosen?")
