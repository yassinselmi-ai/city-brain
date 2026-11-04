# City Brain Convergence — Triplet 07 (Placeholder)

Welcome to the repository for the TSYP14 City Brain Convergence challenge.
This repository is structured to hold the three independently developed layers of our smart city system.

## The Three Layers

- **Twin (`/twin`)** — Simulates city sensors and actuators. Built by the Twin team.
- **Brain (`/brain`)** — Consumes data, makes operational decisions, and dispatches actions. Built by our team (City Brain).
- **Guardian (`/guardian`)** — Monitors data for anomalies and provides trust verdicts. Built by the Guardian team.

## How the layers connect

The three layers operate as a single system, with a deliberate difference between **critical** and **normal** events:

- **Normal path (sequential):** The Twin emits a reading. The Guardian verifies it. If the verdict is `trusted`, the City Brain receives it, computes a decision using its AI model, and dispatches an action to the Twin's actuators.
- **Critical path (parallel, §3.1):** For time-sensitive events (fires, accidents), the Twin broadcasts the reading to **both** the Guardian and the City Brain at the same time. The City Brain computes the decision immediately while the Guardian verifies the reading in parallel. Once both finish, the City Brain gates the decision: if trusted -> dispatch, if rejected -> discard.

**Invariant:** No actuator action is ever dispatched without a `trusted` Guardian verdict attached.

## Repository Structure

```text
triplet-07/
├── README.md               # This file
├── INTEGRATION.md          # How the 3 layers connect
├── TESTBOOK.md             # Scenarios tested by the triplet
├── docker-compose.yml      # Starts the whole city with one command
├── docs/                   # Report, pitch deck, diagrams
├── twin/                   # Twin layer code
├── brain/                  # City Brain layer code (ours)
└── guardian/               # Guardian layer code