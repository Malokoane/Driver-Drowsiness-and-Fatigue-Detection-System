/*
  glasses_final.ino - Anti-Sleep Glasses (ESP32), final firmware for the AI / data-processing part

  Wiring (same as Code.txt):  HW-870 AO -> D34 (GPIO 34), VCC -> 3V3, GND -> GND
                              Buzzer +  -> D4  (GPIO 4),  Buzzer - -> GND
                              LED       -> onboard LED (GPIO 2)

  What it does
   1. Reads the eye sensor 100 times a second and smooths it (average of 5).
   2. Works out the "open eye" level by itself: the 85th percentile of the last 20 s.
      The eye counts as CLOSED when the smoothed reading falls below 80 % of that level.
      (closed eye = LOWER reading, confirmed on the real glasses.)
      This is the same rule as features.py, so the glasses and the Python/ML side agree.
   3. Alerts, instantly and without the laptop (the safety path is NOT the AI):
        closed >= 1 s -> level 1: LED pulses
        closed >= 2 s -> level 2: LED + buzzer pulse
      Blinks (shorter than 1 s) are ignored.
   4. Sends one line per reading to the laptop (115200 baud):
        ms,adc,closed,baseline,severity
      and a status line starting with # once per second (the Python side skips it).

  If the baseline is below MIN_BASELINE the sensor is too close to the eye (or not in range):
  the glasses print "# poor fit" and do not raise alerts, instead of guessing.
*/
#include <algorithm>

const int SENSOR_PIN = 34;
const int BUZZER_PIN = 4;
const int LED_PIN    = 2;

const unsigned long SAMPLE_MS  = 10;      // 100 readings per second
const int   SMOOTH_N     = 5;
const int   BASE_WIN     = 2000;          // 20 s of readings
const float BASE_PCT     = 0.85f;
const float CLOSE_RATIO  = 0.80f;         // closed below 80 % of the open level
const float OPEN_RATIO   = 0.84f;         // open again above 84 % (small gap stops flicker)
const int   MIN_BASELINE = 600;           // below this the sensor is too close / badly placed
const unsigned long WARMUP_MS  = 3000;    // learn the open level before judging
const unsigned long WARNING_MS = 1000;    // closed this long = level 1
const unsigned long SEVERE_MS  = 2000;    // closed this long = level 2
const int   BUZZER_HZ    = 2000;
const int   NO_SIGNAL    = 3800;          // at or above this the sensor sees no eye (glasses off the face / too far)
const unsigned long OFF_FACE_MS = 1000;   // no signal this long = glasses were taken off: forget the old open level

uint16_t ring[BASE_WIN];
uint16_t tmp[BASE_WIN];
int  ringCount = 0, ringHead = 0;
uint16_t sm[SMOOTH_N];
int  smCount = 0, smHead = 0;

float baseline = 0;
bool  eyeClosed = false;
unsigned long closedStart = 0;
int   severity = 0;
bool  buzzing = false;
unsigned long lastSample = 0, lastBase = 0, lastStatus = 0, startMs = 0;
unsigned long learnStart = 0;             // when the current open level started being learned
bool noSignal = false;
unsigned long noSignalSince = 0;

uint16_t smoothed(uint16_t raw) {
  sm[smHead] = raw;
  smHead = (smHead + 1) % SMOOTH_N;
  if (smCount < SMOOTH_N) smCount++;
  unsigned long s = 0;
  for (int i = 0; i < smCount; i++) s += sm[i];
  return (uint16_t)(s / smCount);
}

void pushRing(uint16_t v, unsigned long now) {
  if (ringCount == 0) learnStart = now;
  ring[ringHead] = v;
  ringHead = (ringHead + 1) % BASE_WIN;
  if (ringCount < BASE_WIN) ringCount++;
}

float percentileLevel() {
  int n = ringCount;
  if (n < 50) return 0;
  for (int i = 0; i < n; i++) tmp[i] = ring[i];
  int k = (int)(n * BASE_PCT);
  if (k >= n) k = n - 1;
  std::nth_element(tmp, tmp + k, tmp + n);
  return (float)tmp[k];
}

void setBuzzer(bool on) {
  if (on && !buzzing) { tone(BUZZER_PIN, BUZZER_HZ); buzzing = true; }
  if (!on && buzzing) { noTone(BUZZER_PIN); digitalWrite(BUZZER_PIN, LOW); buzzing = false; }
}

void setup() {
  Serial.begin(115200);
  pinMode(SENSOR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  delay(500);
  setBuzzer(true); delay(150); setBuzzer(false);       // power-on chime
  Serial.println("# ms,adc,closed,baseline,severity");
  Serial.println("# calibrating: keep the glasses on and your eyes open for 3 seconds");
  startMs = millis();
}

void loop() {
  unsigned long now = millis();
  if (now - lastSample < SAMPLE_MS) return;
  lastSample = now;

  uint16_t raw = analogRead(SENSOR_PIN);
  uint16_t v = smoothed(raw);
  bool invalid = (v >= NO_SIGNAL);          // saturated reading: no eye in range, so it must not teach the open level
  if (invalid) {
    if (!noSignal) { noSignal = true; noSignalSince = now; }
    if (now - noSignalSince >= OFF_FACE_MS && ringCount > 0) {
      ringCount = 0; ringHead = 0; baseline = 0;      // glasses were off the face: learn the open level again
      eyeClosed = false;
    }
  } else {
    noSignal = false;
    pushRing(v, now);
  }

  if (now - lastBase >= 250) {              // refresh the open level 4 times a second
    lastBase = now;
    baseline = percentileLevel();
  }

  bool ready   = !invalid && ringCount > 0 && (now - learnStart >= WARMUP_MS) && baseline >= MIN_BASELINE;
  bool nowClosed = eyeClosed;
  if (ready) {
    if (!eyeClosed && v < CLOSE_RATIO * baseline) nowClosed = true;
    if (eyeClosed  && v > OPEN_RATIO  * baseline) nowClosed = false;
  } else {
    nowClosed = false;
  }

  if (nowClosed && !eyeClosed) { eyeClosed = true; closedStart = now; }
  if (!nowClosed && eyeClosed) { eyeClosed = false; }

  unsigned long closedFor = eyeClosed ? (now - closedStart) : 0;
  severity = 0;
  if (closedFor >= SEVERE_MS) severity = 2;
  else if (closedFor >= WARNING_MS) severity = 1;

  bool phase = (now / 200) % 2 == 0;        // 200 ms on / 200 ms off
  digitalWrite(LED_PIN, (severity >= 1) ? phase : LOW);
  setBuzzer(severity == 2 && phase);

  Serial.print(now); Serial.print(',');
  Serial.print(raw); Serial.print(',');
  Serial.print(eyeClosed ? 1 : 0); Serial.print(',');
  Serial.print((int)baseline); Serial.print(',');
  Serial.println(severity);

  if (now - lastStatus >= 1000) {
    lastStatus = now;
    if (noSignal) Serial.println("# no signal: glasses off the face or too far from the eye, no alerts");
    else if (ringCount == 0 || now - learnStart < WARMUP_MS) Serial.println("# calibrating...");
    else if (baseline < MIN_BASELINE) Serial.println("# poor fit: sensor too close or not in range, no alerts");
  }
}
