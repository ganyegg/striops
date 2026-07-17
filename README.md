# Helm

**Think Ahead.**

The Strategic Intelligence Operating System — an executive twin that continuously thinks about the future so leaders can act *before* problems happen.

> Version 0.1 — Strategic Twin for Cities. First customer: **City of Cape Town**.

Helm is not a chatbot and not a dashboard. It is a continuously-reasoning layer that sits above ERP / CRM / HR / Accounting / BI and answers the questions leadership actually cares about:

- What is changing?
- What is likely to happen?
- What risks are emerging?
- What opportunities exist?
- What should leadership do today?
- What happens if we choose Decision A instead of Decision B?

## What's in this slice (v0.1)

A runnable, intelligence-first vertical slice:

```
Cape Town Open Data ─▶ Ingestion ─▶ Postgres (+pgvector) + Neo4j Strategic Twin
                                        │
                          Forecast / Risk / Opportunity / Simulation engines
                                        │
                            Multi-agent reasoning (Gemini)
                                        │
                                 Executive Brief API
                                        │
                        Next.js executive homepage ("Good Morning, Cape Town")
```

Real data sources:

- **ArcGIS FeatureServer** — `https://citymaps.capetown.gov.za/agsext/rest/services/Theme_Based/Open_Data_Service/FeatureServer/{layer}/query` (wards `78`, refuse beats `136`, landfill/transfer `102`, public lighting, electricity districts `4`).
- **National Treasury Municipal Money API** — `https://municipaldata.treasury.gov.za/api` (Cape Town = `CPT`) for budget vs actual.

If the live sources are unreachable (offline / CI), ingestion transparently falls back to the bundled seed data in [`datasets/seed`](datasets/seed) so the whole system always runs.

## Quick start

```bash
cp .env.example .env          # add your GEMINI_API_KEY (optional; falls back to a deterministic mock)
docker compose up --build
```

Then open:

- Executive homepage: http://localhost:3000
- API docs: http://localhost:8000/docs

To (re)run ingestion on demand:

```bash
docker compose run --rm ingest
```

## Local development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn helm.api.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture

| Layer | Tech |
|-------|------|
| Frontend | Next.js (App Router), TypeScript, Tailwind, ECharts |
| Backend | FastAPI, Python 3.12 (async) |
| Facts + vectors | PostgreSQL 16 + pgvector |
| Strategic Twin | Neo4j 5 |
| Reasoning | Google **Gemini** behind a swappable `LLMProvider` (deterministic `MockProvider` for offline/tests) |
| Forecasting | Prophet / statsmodels |
| Orchestration | Docker Compose |

The domain packages live under [`backend/helm`](backend/helm): `ingestion`, `knowledge_graph`, `forecasting`, `risk_engine`, `opportunity_engine`, `recommendation_engine`, `simulation`, `agents`, `executive_brief`, `reasoning`, `api`, `core`.

## Product principles

- Never build dashboards first. Build intelligence first.
- Always provide recommendations, reasoning, confidence and evidence.
- Every prediction cites contributing factors. Every simulation compares scenarios.

## Roadmap

- **Phase 1 (this slice):** Executive Brief, Cape Town datasets, Risk Engine, Simulation MVP.
- **Phase 2:** Full Knowledge Graph, Strategic Memory, Forecast Engine, Infrastructure Intelligence.
- **Phase 3:** Multi-Agent System, Board Meeting Mode, Natural Language Strategy, Continuous Recommendations.
- **Phase 4:** Enterprise / Government / Utilities / Healthcare / Banking / Insurance / Manufacturing.

## License

Proprietary — Helm.
