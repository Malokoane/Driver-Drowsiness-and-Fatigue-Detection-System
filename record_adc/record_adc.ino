/*
  record_adc.ino - sends the eye sensor reading as plain text for recording.
  Output (115200 baud), 100 lines per second:   milliseconds,adc
  Same wiring as your analog sketch: sensor AO -> GPIO 34, VCC -> 3V3, GND -> GND.
  Close the Serial Monitor before running record.py (only one program can use the port).
*/
const int IR_AO_PIN = 34;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);        // 0 - 4095
  analogSetAttenuation(ADC_11db);  // full 0 - 3.3 V range
  delay(500);
  Serial.println("# ms,adc");
}

void loop() {
  static unsigned long last = 0;
  unsigned long now = millis();
  if (now - last >= 10) {          // 100 readings per second
    last = now;
    Serial.print(now);
    Serial.print(",");
    Serial.println(analogRead(IR_AO_PIN));
  }
}
