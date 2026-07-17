# Helm AI — Architecture (v0.1 slice)

Helm AI is intelligence-first: the reasoning core (graph + engines + agents) is
the product; the LLM is a narrator over it, and the UI is the last mile.

## Component map

```
                 ┌──────────────────────────────────────────────┐
                 │                Ingestion                      │
   ArcGIS  ─────▶│  arcgis.py · treasury.py · pipeline.py        │
   Treasury ────▶│  (live first, seed fallback, raw cache)       │
                 └───────────────┬──────────────────────────────┘
                                 │ writes
             ┌───────────────────┴────────────────────┐
             ▼                                         ▼
   ┌───────────────────┐                    ┌────────────────────────┐
   │ Postgres + pgvector│                   │  Neo4j Strategic Twin   │
   │  (facts, metrics)  │                   │ (entities+relationships)│
   └─────────┬──────────┘                   └────────────┬───────────┘
             │ Repository (seed fallback)                │ GraphStore
             ▼                                           ▼
   ┌───────────────────────────────────────────────────────────────┐
   │                        Reasoning core                          │
   │  forecasting · risk_engine · opportunity_engine · simulation   │
   │  recommendation_engine                                         │
   └───────────────────────────┬───────────────────────────────────┘
                               │ used by
                               ▼
   ┌───────────────────────────────────────────────────────────────┐
   │  Multi-agent layer (Gemini | Mock)                             │
   │  Finance · Infrastructure · Risk · Forecast · Citizen          │
   │            └─────────▶ Executive Agent (merge)                 │
   └───────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
                     FastAPI  (/brief /risks /opportunities
                               /simulate /entities /agents /health)
                               │
                               ▼
                   Next.js executive homepage
```

## Design decisions

- **Swappable providers.** `LLMProvider` (Gemini/Mock) and `GraphStore`
  (Neo4j/InMemory) are interfaces; the platform degrades gracefully and stays
  testable offline.
- **Seed fallback.** The `Repository` prefers Postgres but serves committed seed
  data when the DB is empty/unreachable, so a brief is always produced.
- **Explainability by construction.** Risks carry the full
  `Likelihood × Impact × Trend × Confidence` breakdown plus evidence; forecasts
  cite contributing factors; simulations always compare scenario vs baseline.
- **Engines decide, the LLM narrates.** Scores, deltas and recommendations come
  from deterministic engines; the LLM only phrases them.

## Risk score

`score = Likelihood × Impact × Trend × Confidence × 100`

- Likelihood: derived from forecast confidence.
- Impact: per-metric domain weight (water > roads > refuse > lighting …).
- Trend: 0.5–2.0 multiplier from the forecast slope (worsening > 1).
- Confidence: forecast goodness-of-fit blended with sample size.

## Data sources

- City of Cape Town ArcGIS FeatureServer (`Theme_Based/Open_Data_Service`):
  wards (78), refuse beats (136), landfill (102), electricity districts (4).
- National Treasury Municipal Money API (`CPT`) for budget vs actual.

## Extending

- New scenario types: add to `_FUNCTION_MODEL` / new handler in `simulation/engine.py`.
- New agents: subclass `Agent`, register in `agents/__init__.py`.
- New metrics/risks: add a `_METRIC_PROFILE` entry in `risk_engine/engine.py`.
