# Terraform (placeholder)

Infrastructure-as-code for Helm AI's Azure deployment lands here in a later
phase. The v0.1 slice runs entirely on Docker Compose (see the repo root).

Planned modules:

- `network/` — VNet, subnets, private endpoints
- `data/` — Azure Database for PostgreSQL (pgvector), Neo4j (Aura or AKS)
- `app/` — Container Apps / AKS for the FastAPI backend and Next.js frontend
- `identity/` — Microsoft Entra ID app registrations and managed identities
- `observability/` — Log Analytics, Managed Grafana, OpenTelemetry collector

Keep state in a remote backend (Azure Storage) with locking before first apply.
