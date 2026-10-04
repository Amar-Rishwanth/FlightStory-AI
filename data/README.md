# FlightStory AI - Synthetic Development Datasets

## Status

**IMPORTANT:** These are **SYNTHETIC DEVELOPMENT DATASETS** created for proof-of-concept development and testing purposes only.

The official hackathon dataset has **NOT** been provided yet. These files are temporary placeholders to enable system design and prototyping.

---

## Dataset Overview

This folder contains four heterogeneous log family CSV files representing events from a distributed three-node system:

- **NODE_A** — Primary control node
- **NODE_B** — Secondary monitoring node  
- **NODE_C** — Tertiary redundancy/recovery node

### Files

| File | Records | Format | Purpose |
|------|---------|--------|---------|
| `operator_actions.csv` | 37 | CSV | Operator commands, parameter changes, interventions |
| `system_state.csv` | 38 | CSV | State transitions, performance metrics, resource usage |
| `guidance_events.csv` | 35 | CSV | Guidance recommendations, confidence levels, acceptance status |
| `faults_recovery.csv` | 21 | CSV | Fault detection, recovery procedures, resolution status |

---

## Intentional Heterogeneity

Each CSV has a **different schema** to reflect real-world log diversity. Column names, timestamp fields, and event structures vary:

- **operator_actions.csv** — Focus on human actions: `timestamp`, `operator_id`, `action_type`, `action_target`
- **system_state.csv** — Focus on metrics: `event_time`, `state_category`, `cpu_usage_pct`, `memory_mb`
- **guidance_events.csv** — Focus on recommendations: `guid_timestamp`, `guidance_type`, `confidence_level`, `applied_by`
- **faults_recovery.csv** — Focus on incidents: `fault_timestamp`, `incident_id`, `error_code`, `recovery_status`

This heterogeneity is **intentional** and represents the normalization challenge: real-world logs must be mapped to a common event model before analysis.

---

## Represented Incidents

### Incident 1: INC_001 (NODE_A Load Escalation → Guidance → Fault → Recovery)

**Timeline:**
1. **09:00:45** — Fault detected: `ERR_THRESHOLD_BREACH` on NODE_A
2. **09:01:30** — Guidance issued: `GUID_0005` recommends increasing secondary threshold
3. **09:15:00** — Fault escalated: `ERR_PERF_DEGRADATION` in control_system
4. **10:30:00** — Critical fault: `ERR_TRANSIENT_FAULT` in cooling_subsystem
5. **10:30:15** — Recovery action: Activate bypass per guidance
6. **12:45:00** — Recovery completed: Cooling subsystem restart finished
7. **13:36:15** — Recovery validated: Load returned to normal ranges

**Cross-Node Correlation:** Events on NODE_A, guidance from guidance_events, recovery tracked through faults_recovery.

### Incident 2: INC_002 (NODE_B Configuration Drift → Recovery)

**Timeline:**
1. **09:45:15** — Fault: `ERR_CONFIG_MISMATCH` detected (configuration drift)
2. **09:46:15** — Guidance: `GUID_0006` recommends loading backup configuration v2
3. **10:15:45** — Fault: `ERR_OSCILLATION` in control dynamics
4. **10:09:30** — Guidance: `GUID_0009` recommends damping factor adjustment
5. **12:15:00** — Fault: `ERR_NETWORK_SPIKE` in network stack
6. **12:19:45** — Guidance: `GUID_0018` recommends communication check
7. **12:35:00** — Recovery: All faults resolved

**Cross-Node Correlation:** Configuration issues propagate; corrective guidance applied.

### Incident 3: INC_003 (NODE_C Load Excursion → Sync Loss → Emergency Shutdown → Recovery)

**Timeline:**
1. **10:15:30** — Fault: `ERR_LOAD_EXCURSION` on NODE_C
2. **10:17:45** — Guidance: `GUID_0010` recommends continuous monitoring
3. **12:30:00** — Critical fault: `ERR_SYNC_LOSS` (inter-node communication failure)
4. **12:35:00** — Guidance: `GUID_0019` initiates emergency safe shutdown
5. **13:15:30** — Recovery initiated: `ERR_SYNC_LOSS` recovery active
6. **13:16:00** — Guidance: `GUID_0022` applies emergency protocol
7. **14:00:15** — Recovery completed: System returned to nominal state

**Cross-Node Correlation:** Sync loss across all nodes; coordinated recovery procedure; multi-node state changes.

---

## Temporal Correlation Strategy

Events can be correlated using:

- **Timestamp windows:** Events within 30-60 seconds typically belong to the same incident
- **Incident IDs:** `incident_id` field in faults_recovery.csv links to specific incidents
- **Node-to-node sequences:** NODE_A fault → guidance → recovery forms a causal chain
- **Operator acknowledgment:** `applied_by` field in guidance_events.csv traces human actions

---

## Data Quality Notes

- **No missing values** in required fields (intentionally clean for POC)
- **Timestamps are ISO 8601 format** (UTC)
- **Recovery durations:** Calculated field `recovery_duration_sec` (negative values indicate out-of-order logging)
- **Confidence levels:** Guidance events include `confidence_level` (0.65-0.98) to enable uncertainty representation
- **Status tracking:** `recovery_status` shows progression: `PENDING` → `IN_PROGRESS` → `COMPLETED`

---

## Next Steps

1. **Normalize** these heterogeneous schemas into a common event model
2. **Correlate** events across the four files using timestamps and IDs
3. **Reconstruct** incident timelines
4. **Generate** AI narratives with evidence links
5. **Visualize** at multiple levels (timeline, cascade, dependency graph, narrative)

---

## Disclaimer

This is a **synthetic dataset for development purposes only**. It does not represent real system behavior, real operational incidents, or official hackathon data.

When the official dataset is provided, replace these files and re-run the normalization pipeline.
