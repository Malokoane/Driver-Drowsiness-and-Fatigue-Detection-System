# Anti Sleep Glasses Backend

Backend MVP for the PRJ 361 AI Powered Anti Sleep Glasses project.

## What is included

- Driver registration and JWT login
- Secure glasses pairing with a one time device API key
- Driving session start, end, and history
- Idempotent batch telemetry ingestion for offline recovery
- Warning and critical drowsiness classification
- Alert delivery records for glasses, buzzer, dashboard, and mobile channels
- Thirty day dashboard summary
- PostgreSQL migration, Docker setup, validation, rate limits, security headers, logs, and graceful shutdown
- MQTT status bridge stub for Raspberry Pi or ESP32 integration

## Architecture decision

The PDF conflicts with itself. One section specifies Python, PostgreSQL, and tutor bookings. Another specifies Node.js, MS SQL, MongoDB, and athlete heart rate data. This implementation follows the actual anti sleep product and uses Node.js, Express, TypeScript, PostgreSQL, and MQTT.

One relational database is enough for the academic prototype. Adding MongoDB creates two backup, consistency, deployment, and security problems. PostgreSQL handles the current telemetry load and preserves links between devices, sessions, readings, events, and alerts.

## Quick start

1. Copy `.env.example` to `.env` and replace `JWT_SECRET`.
2. Run `docker compose up -d postgres`.
3. Run `npm install`.
4. Run `npm run db:migrate`.
5. Run `npm test`.
6. Run `npm run dev`.

The API listens on `http://localhost:4000` by default.

## Device flow

1. A driver registers and signs in.
2. The dashboard calls `POST /api/v1/devices` with the glasses serial number.
3. The API returns the device key once. Store it in the device secure storage.
4. The dashboard starts a session through `POST /api/v1/sessions`.
5. The device sends buffered samples to `POST /api/v1/telemetry/batch` with `x-device-serial` and `x-device-key` headers.
6. Duplicate sequence numbers are ignored, so reconnect retries do not duplicate readings.
7. The dashboard reads session events and the thirty day summary.

## Example telemetry payload

```json
{
  "sessionId": "00000000-0000-0000-0000-000000000000",
  "samples": [
    {
      "sequenceNumber": 1042,
      "capturedAt": "2026-08-30T18:40:00.000Z",
      "eyeAspectRatio": 0.17,
      "eyeClosedMs": 1250,
      "blinkRate": 7.5,
      "headPitch": 13.2,
      "confidence": 0.93,
      "drowsinessScore": 0.72,
      "batteryPercent": 76,
      "firmwareVersion": "0.1.0"
    }
  ]
}
```

## Detection boundary

The glasses or Raspberry Pi should run the real time model and trigger its local buzzer without waiting for the cloud. The backend records and escalates events. It must never become the only safety alert path. Thresholds in `src/detection.ts` are prototype defaults, not medically validated values.

## Main API routes

| Method | Route | Authentication | Purpose |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register` | None | Create driver account |
| POST | `/api/v1/auth/login` | None | Issue two hour JWT |
| POST | `/api/v1/devices` | Driver JWT | Pair glasses |
| GET | `/api/v1/devices` | Driver JWT | List paired devices |
| POST | `/api/v1/sessions` | Driver JWT | Start drive |
| PATCH | `/api/v1/sessions/:id/end` | Driver JWT | End drive |
| GET | `/api/v1/sessions` | Driver JWT | Session history |
| GET | `/api/v1/sessions/:id/events` | Driver JWT | Drowsiness events |
| POST | `/api/v1/telemetry/batch` | Device headers | Upload readings |
| GET | `/api/v1/dashboard/summary` | Driver JWT | Thirty day metrics |

## Similar work used as engineering reference

- AWS IoT Device Shadows informed the offline state and reconnection model: https://docs.aws.amazon.com/iot/latest/developerguide/iot-device-shadows.html
- Express production security guidance informed TLS expectations, input validation, Helmet, rate limiting, and reduced error leakage: https://expressjs.com/en/advanced/best-practice-security/
- Smart Driver Monitoring System demonstrates EAR, MQTT, and ESP32 integration: https://github.com/alhoripy/Smart-Driver-Monitoring-System
- DriveSafe demonstrates multi cue detection, MQTT alerts, and ESP32 hardware alerts: https://github.com/hadi-mostafa-27/DriveSafe

## Next engineering work

- Add refresh tokens with rotation and revocation
- Add WebSocket or server sent event delivery for live dashboard alerts
- Connect alert delivery workers to Firebase Cloud Messaging
- Add device certificate authentication before field testing
- Add data retention and driver deletion workflows for POPIA
- Add integration tests against a disposable PostgreSQL database
- Calibrate model thresholds using an approved dataset and controlled simulator tests
- Add firmware acknowledgement messages so alert delivery reflects hardware receipt
