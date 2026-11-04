# Brain Layer — Interface Card (R1)

This document describes the Brain layer's external contract: what it
consumes, what it emits, how to point it at a different partner, and how
it authenticates. It is designed so a partner team can connect their
layer without reading our source code.

---

## 1. Inputs (what the Brain consumes)

### 1.1 Sensor readings (from the Twin layer)

The Brain reads sensor readings from a **Redis Stream** named
`sensors.readings` (configurable via `SENSOR_STREAM` env var).

Each reading is a JSON object embedded in the `payload` field:

```json
{
  "sensor_id": "cam-1",
  "type": "traffic",
  "value": 0.9,
  "unit": "ratio",
  "ts": "2026-10-06T12:00:00Z",
  "seq": 1,
  "sig": "abc123...",
  "severity_class": "normal",
  "correlation_id": "corr-abc-123",
  "zone": "downtown"
}