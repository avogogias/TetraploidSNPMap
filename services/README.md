# TetraploidSNPMap Web Services

Web application version of TetraploidSNPMap, a genetic linkage mapping tool for autotetraploid organisms. The desktop Java/Fortran application has been re-architected as a microservices-based web application.

## Architecture

```
Browser → Frontend (React) → API Gateway (FastAPI) → Computation Service (FastAPI)
                                    ↓                        ↓
                               PostgreSQL              Celery Worker
                                    ↓                        ↓
                                  Redis ←──────────── Fortran/R backends
```

| Service | Port | Technology | Role |
|---------|------|------------|------|
| **frontend** | 3000 | React 18, TypeScript, Vite, TailwindCSS | Interactive web UI with Plotly visualizations |
| **api-gateway** | 8000 | FastAPI, SQLAlchemy, PostgreSQL | REST API, project/dataset/job management |
| **computation** | 8001 | FastAPI | Wraps Fortran binaries and R scripts |
| **worker** | - | Celery, Redis | Background execution of analysis tasks |

## Supported Analysis Types

All 8 analysis types from the desktop application are supported:

| Analysis | Desktop Binary | Web Handler | Python Fallback |
|----------|---------------|-------------|-----------------|
| Clustering | `cluster_chimatrixonly` + R `fastcluster` | `run_snp_cluster()` | scipy hierarchical clustering |
| Two-Point | `SNPcexp_noimsl_dupcheck` | `run_twopoint_snp()` | - |
| MDS | R `General_estimation.R` | `run_mds()` | scipy + numpy ordering |
| Phase | `phasev6_noimsl` | `run_phase()` | - |
| QTL | `SNP_QTL_newinput` / `simple_model` | `run_snp_qtl()` | - |
| ANOVA | Fortran `anova` | `run_anova()` | scipy `f_oneway` |
| Permutation | `SNP_QTLperm_noimsl` | `run_snp_perm()` | - |
| Linkage Map | Python | `generate_linkage_map()` | native |

## Project Modes

- **SNP** — SNP marker analysis (dosage-based)
- **QTL** — SNP + quantitative trait locus mapping
- **NONSNP** — RFLP/AFLP/SSR marker analysis

## File Formats

| Format | Extension | Content |
|--------|-----------|---------|
| SNPloc | `.SNPloc` | SNP marker dosage data |
| QUA | `.qua` | Quantitative trait phenotype data |
| LOC | `.loc` | Non-SNP marker location data |

## Quick Start

```bash
docker-compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000/api/v1
- API Docs: http://localhost:8000/docs

## Running Tests

```bash
# API Gateway (71 tests)
cd services/api-gateway && python -m pytest tests/ -v

# Computation Service (49 tests)
cd services/computation && python -m pytest tests/ -v

# Worker (32 tests)
cd services/worker && python -m pytest tests/ -v

# Frontend (26 tests)
cd services/frontend && npx vitest run

# Feature Parity (26 tests - verifies web matches desktop features)
python -m pytest tests/test_feature_parity.py -v
```

**Total: 204 tests** across all services.

## API Endpoints

### Projects
- `POST /api/v1/projects` — Create project (name, mode)
- `GET /api/v1/projects` — List projects (paginated)
- `GET /api/v1/projects/{id}` — Get project details
- `DELETE /api/v1/projects/{id}` — Delete project

### Datasets
- `POST /api/v1/projects/{id}/datasets` — Upload dataset file
- `GET /api/v1/projects/{id}/datasets` — List datasets
- `GET /api/v1/projects/{id}/datasets/{ds}/markers` — Browse markers (paginated)
- `PUT /api/v1/projects/{id}/datasets/{ds}/markers/selection` — Update marker selection
- `POST .../markers/select-all|select-none|select-invert` — Bulk selection

### Analyses
- `POST /api/v1/projects/{id}/analyses` — Submit analysis job
- `GET /api/v1/projects/{id}/analyses` — List jobs
- `GET /api/v1/projects/{id}/analyses/{job}` — Get job status
- `GET /api/v1/projects/{id}/analyses/{job}/results` — Get results
- `DELETE /api/v1/projects/{id}/analyses/{job}` — Cancel/remove job

## Configuration Limits

| Parameter | Value | Origin |
|-----------|-------|--------|
| MAX_MARKERS | 8,000 | `LinkageGroup.verify()` |
| MAX_INDIVIDUALS | 300 | `LinkageGroup.verify()` |
| MAX_PERMS | 500 | Desktop default |
| MAX_UPLOAD_SIZE | 100 MB | API Gateway config |
| SUBPROCESS_TIMEOUT | 3,600s | Fortran/R execution limit |
