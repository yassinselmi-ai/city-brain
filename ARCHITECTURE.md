# City Brain Layer — Architecture

**Challenge:** TSYP14 — City Brain Convergence
**Layer owned by this team:** City Brain (operational decision-maker)
**Status:** Draft, Phase 1 preparation

---

## 1. Role in the system

City Brain sits between the Twin (sensors/actuators) and Guardian (trust verifier). One job: consume real-time sensor data, decide the correct operational response, dispatch through Twin's actuator tools — only once Guardian confirms the reading is trustworthy.

---

## 2. System architecture

Twin broadcasts every reading to both City Brain and Guardian. Guardian returns a trust verdict. City Brain only dispatches to actuators with a trusted verdict attached.

---

## 3. Two processing paths

Critical path (parallel): compute decision immediately, hold it, dispatch only if Guardian says trusted.
Normal path (sequential): wait for Guardian verdict, then decide and dispatch.

Rule on both paths: nothing dispatched without a trusted Guardian verdict attached.

---

## 4. Data contract

### 4.1 Twin -> City Brain
sensor_id, type, value, unit, ts, seq, sig, severity_class, correlation_id, zone, emergency payload, action_ack.

### 4.2 Guardian -> City Brain
correlation_id, sensor_id, ts, seq, trust_score, verdict, sig, reason_codes.

### 4.3 City Brain -> Twin
actuator_id, action, params, correlation_id, trust_score, requested_by.

---

## 5. Incident types

- Accidents, Fires, Traffic jams, Flooding — see rules.py TODOs.

---

## 6. State machine

Critical: Detected -> Decided (held) -> Dispatched | Discarded
Normal:   Detected -> Verified -> Decided -> Dispatched

---

## 7. Technology

Python 3.12 + FastAPI, mcp SDK, Redis Streams, PostgreSQL, pytest, GitHub Actions, Docker.

---

## 8. Security

- Fail-safe default: Guardian unreachable -> no action
- Independent sig check
- Replay protection via monotonic seq
- Trust gate enforced twice
- Full audit log

---

## 9. Open questions for the triplet

- Who sets severity_class?
- Exact trust_score threshold?
- correlation_id format?
- Twin-side threshold enforcement?
