# HeatShield API Contract

> Base URL: `http://localhost:8000/api/v1`
> All responses are JSON. All list responses include a `meta` object and a `status` object.
> Demo responses carry `"status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }`.

---

## Standard envelopes

### Success (list)
```json
{
  "data": [ ...items ],
  "meta": { "count": 3, "page": 1, "page_size": 3 },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

### Success (single item)
```json
{
  "data": { ...item },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

### Error
```json
{ "detail": { "error": "Hospital 'ZZZZ' not found", "code": "HOSPITAL_NOT_FOUND" } }
```

### Validation error (422)
FastAPI default — returned when query params fail `ge`/`le` constraints.

---

## Endpoints

### GET /health
**Purpose:** Liveness check — frontend and monitoring poll this.

**Response 200:**
```json
{ "status": "ok", "env": "development", "version": "1.0.0" }
```

---

### GET /hospitals
**Purpose:** List all hospitals with current capacity and risk status.

**Response 200:**
```json
{
  "data": [
    {
      "hospital_id": "H001",
      "name": "City General Hospital [DEMO]",
      "region": "Greater London",
      "capacity_total": 300,
      "capacity_available": 72,
      "occupancy_pct": 76.0,
      "risk_status": "amber"
    }
  ],
  "meta": { "count": 3, "page": 1, "page_size": 3 },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

**risk_status values:** `green` | `amber` | `red` | `critical`

---

### GET /hospitals/{hospital_id}
**Purpose:** Full detail for a single hospital.

**Path param:** `hospital_id` — e.g. `H001` (case-insensitive)

**Response 200:**
```json
{
  "data": {
    "hospital_id": "H001",
    "name": "City General Hospital [DEMO]",
    "region": "Greater London",
    "address": "1 Demo Road, London, E1 1AA",
    "latitude": 51.5074,
    "longitude": -0.1278,
    "contact_email": "ops@demo-citygen.nhs",
    "capacity_total": 300,
    "capacity_available": 72,
    "occupancy_pct": 76.0,
    "risk_status": "amber"
  },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

**Response 404:** `{ "detail": { "error": "Hospital 'ZZZZ' not found", "code": "HOSPITAL_NOT_FOUND" } }`

---

### GET /forecasts
**Purpose:** Demand forecast for a hospital over the next N days.

**Query params:**

| Param | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `hospital_id` | string | yes | — | must be a known ID |
| `days` | integer | no | 7 | 1–14 |

**Response 200:**
```json
{
  "data": {
    "hospital_id": "H001",
    "model_version": "v1.2.0-demo",
    "generated_at": "2026-10-09T08:00:00+00:00",
    "days_requested": 7,
    "points": [
      {
        "forecast_date": "2026-10-10",
        "predicted_admissions": 42.5,
        "confidence_lower": 36.1,
        "confidence_upper": 48.9,
        "risk_status": "amber"
      }
    ]
  },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

**Response 404:** hospital not found
**Response 422:** `days` out of range or `hospital_id` missing

---

### GET /weather
**Purpose:** Daily temperature and humidity for the region linked to a hospital, fetched live from [Open-Meteo](https://open-meteo.com/) (open-source weather API, no API key).

**Query params:**

| Param | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `hospital_id` | string | yes | — | used to resolve lat/lon (London/Manchester defaults if unknown) |
| `days` | integer | no | 7 | 1–92 |

**Response 200:**
```json
{
  "data": {
    "hospital_id": "H001",
    "days_requested": 7,
    "observations": [
      {
        "observation_date": "2026-10-09",
        "temperature_max_c": 34.2,
        "temperature_min_c": 23.7,
        "humidity_pct": 65.0,
        "heat_index_c": 38.0,
        "condition": "Heatwave"
      }
    ]
  },
  "status": { "data_source": "live", "note": "Live temperature and humidity from Open-Meteo" }
}
```

**Response 503:** Open-Meteo unreachable (`WEATHER_UNAVAILABLE`)
**Response 422:** `days` out of range or `hospital_id` missing

---

### GET /alerts
**Purpose:** Active capacity-risk alerts, optionally filtered to one hospital.

**Query params:**

| Param | Type | Required | Default |
|---|---|---|---|
| `hospital_id` | string | no | — (returns all) |

**Response 200:**
```json
{
  "data": [
    {
      "alert_id": "ALT-0042",
      "hospital_id": "H002",
      "hospital_name": "Riverside Medical Centre [DEMO]",
      "severity": "high",
      "message": "DEMO: Predicted admissions exceed 85% capacity on 2026-10-12",
      "triggered_at": "2026-10-09T06:05:00+00:00",
      "forecast_date": "2026-10-12",
      "resolved": false
    }
  ],
  "meta": { "count": 1, "page": 1, "page_size": 1 },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

**severity values:** `low` | `medium` | `high` | `critical`

---

### GET /metrics
**Purpose:** Latest ML model evaluation metrics (produced by the ML team after each training run).

**Response 200:**
```json
{
  "data": {
    "model_version": "v1.2.0-demo",
    "evaluated_on": "2026-10-01",
    "mae": 3.8,
    "rmse": 5.1,
    "r2": 0.87,
    "training_data_from": "2023-01-01",
    "training_data_to": "2026-09-30",
    "feature_count": 12
  },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

---

## Common HTTP status codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 404 | Resource not found (unknown hospital_id) |
| 422 | Validation error (bad query params) |
| 500 | Internal server error |

---

## Cross-team notes

- Frontend: use `status.data_source` to show a "demo data" banner in the UI when `data_source === "demo"`.
- ML team: `model_version` in `/forecasts` and `/metrics` must match the artifact version stored in `ML_MODEL_PATH`. Agree the `feature_count` and field names before `ml_adapter.py` is wired up.
- DB team: `hospital_id` values (`H001`, `H002`, `H003`) must match the primary keys in the `hospitals` table.
