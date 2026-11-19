# API documentation

The live OpenAPI schema is served by FastAPI at `/docs` when the backend is running.

Phase 1 implements:

| Method | Path | Status |
| --- | --- | --- |
| GET | `/api/health` | implemented |
| GET | `/api/datasets` | implemented (registry only) |

Planned (not implemented until the corresponding phase):

| Method | Path | Phase |
| --- | --- | --- |
| POST | `/api/datasets/validate` | 2 |
| POST | `/api/comfort/train` | 3 |
| POST | `/api/comfort/predict` | 3 |
| POST | `/api/occupancy/train` | 3 |
| POST | `/api/occupancy/predict` | 3 |
| POST | `/api/experiments` | 5–8 |
| GET | `/api/experiments` | 8 |
| GET | `/api/experiments/{id}` | 8 |
| POST | `/api/training/start` | 8 (async job) |
| GET | `/api/training/{id}/status` | 8 |
| POST | `/api/training/{id}/stop` | 8 |
| GET | `/api/results/{id}` | 8 |
| GET | `/api/reports/{id}` | 8 |

Training endpoints must return a job id immediately. They must not block on RL.

Validation errors use HTTP 422 with Pydantic details. Domain errors use problem-style JSON: `code`, `message`, `details`.
