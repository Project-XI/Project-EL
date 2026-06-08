# ORACLE Backend Testing UI (Step 1)

Initial React dashboard scaffolding with:

- Agent Topology Graph (React Flow)
- Session Timeline (Gantt style)
- Live Event Feed (schema-shaped events)
- Alert Cards (SENTINEL + GATEKEEPER)

## Run

```bash
npm install
npm run dev
```

## Build check

```bash
npm run build
```

## Notes

- Agent topology uses required fixed layout:
  - ORACLE (top)
  - MAIN VIVA (middle)
  - GATEKEEPER + SENTINEL (bottom, side-by-side)
- Event objects follow the required schema fields:
  - event_id, timestamp, source_agent, target_agent, event_type, session_id, payload, duration_ms
- This is step 1 foundation; next step can connect these panels to live backend websocket streams.
