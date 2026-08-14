# Striops

<p align="center">
  <img src="docs/brand/coct-logo.svg" alt="City of Cape Town" width="280" />
</p>

**Trusted with foresight.**

The Strategic Intelligence Operating System — an executive twin that continuously thinks about the future so leaders can act *before* problems happen.

> Version **0.4** — Place-aware Ask, critical sectors, health-score provenance, and a command-first UI. First customer: **City of Cape Town**.

**Internal reference (product, data, pilot, pricing, security):** [`docs/STRIOPS.md`](docs/STRIOPS.md).  
**Cape Town pack (deck + mayoral meeting pack):** [`docs/pitch/index.html`](docs/pitch/index.html)

Striops is not a chatbot and not a dashboard. It is a continuously-reasoning layer that sits above ERP / CRM / HR / Accounting / BI and answers the questions leadership actually cares about:

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
uvicorn striops.api.main:app --reload

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

The domain packages live under [`backend/striops`](backend/striops): `ingestion`, `knowledge_graph`, `forecasting`, `risk_engine`, `opportunity_engine`, `recommendation_engine`, `simulation`, `agents`, `executive_brief`, `reasoning`, `api`, `core`.

## Product principles

- Never build dashboards first. Build intelligence first.
- Always provide recommendations, reasoning, confidence and evidence.
- Every prediction cites contributing factors. Every simulation compares scenarios.

## Why invest in Striops

Cities lose more to **slow decisions, blind spots, underspend, and audit findings** than any software fee. An analyst with a general-purpose AI can draft a brief once; they cannot be a 24/7 sentinel, a provenance system that survives council and media scrutiny, or institutional memory across staff and administration turnover.

| Objection | Answer |
|-----------|--------|
| "We have analysts + AI" | Continuity, re-verification at scale, and a decision ledger they cannot be while also doing their day job |
| "Why not Power BI / a chatbot?" | Dashboards wait to be noticed; chatbots invent. Striops ranks, cites, and proposes — with deterministic scores |
| "Is the fee worth it?" | Core (~R1.14m/yr) is priced against redeployable underspend surfaced, cost-of-delay avoided, and AGSA findings prevented — fee as rounding error vs one missed water or fiscal miss |

**Moat:** sustained live-data integration + governance posture (provenance, POPIA, audit packs) + multi-metro benchmarking over time. The LLM is a swappable narrator, not the product.

**Traction path:** 90-day pilot (R180k, binary success test) → value ledger → renewal / Command → other metros buy “what Cape Town has.”

Full investment case, pricing, and product-pivot roadmap: [`docs/STRIOPS.md`](docs/STRIOPS.md).

## Roadmap

- **Now (v0.4):** Executive brief, place-aware Ask, critical sectors, provenance, command-first UI.
- **Next (product pivot):** Sentinel alerting, cost-of-delay on open decisions, foresight backtest, Board Meeting Mode, AGSA audit packs, homepage collapsed to one decision screen.
- **Scale:** Multi-metro network effects; enterprise verticals after city proof.

## License

Proprietary — Striops.
