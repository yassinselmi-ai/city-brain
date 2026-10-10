# City Brain — Verification Evidence

Concrete proof that the City Brain layer implements the behaviors described
in `ARCHITECTURE.md`. Every claim here is backed by a runnable command.

Date of last verification: 2026-10-10

---

## 1. Test suite

    $ pytest
    26 passed

Covers: mocks, schemas, model, pipeline paths, replay guard, smoke.

## 2. Adversarial scenarios

    $ python scripts/scenario_runner.py
    ✅ spoofed_reading
    ✅ frozen_sensor
    ✅ guardian_unreachable (SKIPPED, chaos=off)
    ✅ duplicate_event
    ✅ replayed_reading

    Result: 5/5 scenarios passed

## 3. Live metrics (`GET /metrics`)

    critical_path_total:       2
    normal_path_total:         2
    dispatches_total:          5
    discards_total:            4
    replays_rejected_total:    3
    discards_by_reason:        {"verdict_rejected": 1, "replay": 3}

- 2 critical events processed via the parallel path (§3.1)
- 2 normal events processed via the sequential path (§3.2)
- 5 dispatches executed by the Twin
- 3 replayed readings blocked before detection

## 4. Model decisions

Every dispatch decision is logged with the source of the decision:

    INFO:city_brain.pipeline.orchestrator:decision chosen_by=model confidence=0.913 reason=model predicted retime_traffic_signal
    INFO:city_brain.pipeline.orchestrator:decision chosen_by=model confidence=1.000 reason=model predicted dispatch_ambulance_police

`chosen_by=model` proves the decision came from the trained RandomForest,
not from the rule-based fallback in `decision/engine.py`.

## 5. Fail-safe behavior (§8)

When Guardian is unreachable:

    $ python -c "... /ingest with GUARDIAN_CHAOS=down ..."
    {"state":"discarded","discarded_reason":"guardian_unreachable","dispatched":[]}

Nothing is dispatched. The pipeline returns cleanly instead of crashing.

## 6. Two processing paths (§3)

- Critical (`severity_class=critical`): decision + verification run in parallel.
  `saved_ms` reports the gain (~40-50ms per event on this machine).
- Normal (`severity_class=normal`): sequential — verify first, then decide.

Both invariants hold: no dispatch without a trusted verdict.

## 7. Replay protection (§8)

    $ python -c "... send same sensor_id + seq twice ..."
    1st: no_incident
    2nd: replay_rejected

Any reading whose `seq` is not strictly greater than the last seen `seq`
for that sensor is rejected before detection runs.

---

## Reproduce

All commands above assume:

    Terminal 1: python scripts/run_mocks.py
    Terminal 2: uvicorn city_brain.main:app --port 8000 --reload
    Terminal 3: <commands from this document>