# Backend rules

Read this file before backend work. The [root instructions](../AGENTS.md) also apply, including
code style, language, file limits and the requirement to use real logic and storage.

## Read by task

| Before | Read |
| --- | --- |
| Any backend implementation or refactor | [ARCHITECTURE.md](ARCHITECTURE.md): layers, imports, ports and composition |
| Changing routes, schemas, errors or authentication | [API.md](API.md): HTTP contracts and permission handling |
| Changing persistence, repositories, migrations, transactions or seed data | [DATABASE.md](DATABASE.md): storage choice, SQL repositories, Unit of Work |
| Adding or changing tests, or reporting validation | [TESTING.md](TESTING.md): test scope and checks |

Read every matching document when a task spans several areas. These four files are internal working
instructions removed at submission. Product documentation lives in `docs/` and describes the
implemented system; product files must not link to these internal instructions.

## Architecture contract

- Use `src/app/{domain,usecase,repository,adapter,controller}` and a `main.py` composition root.
  `app` is the template's default package name. If renamed during kickoff, update paths, imports,
  startup commands and package configuration together.
- `domain` owns business rules; `usecase` owns use cases and ports. Neither imports framework,
  persistence or provider code. `repository` implements storage ports (`repository/<storage>/`),
  `adapter` implements external providers, `controller` owns HTTP. These three never import each
  other.
- Supply dependencies through use case constructors. Concrete implementations are selected at
  startup in `main.py`; controllers call use cases rather than storage or provider SDKs.
- Type hints are required. Explain any necessary `Any` in `docs/design-decisions.md`.
- External providers have a deterministic implementation for the main offline scenario. It computes
  from the input and real stored data. Missing implementations produce an honest error.
- Secrets come from environment variables, with safe defaults in `.env.example`. The stand starts
  without `.env` and releases resources at shutdown.

## Default stack

Unless the task or an explicit project decision chooses otherwise: Python 3.12+, FastAPI,
Pydantic only for HTTP schemas in `controller/`, standard `dataclasses` everywhere else, uv, Ruff
with line length 100, mypy strict and pytest.

Persistence has fixed rules, detailed in [DATABASE.md](DATABASE.md): ask the user whether storage is
in-memory only or a database (SQLite or PostgreSQL 16) before the first repository; no ORM, only
SQL through the driver; SQL migrations applied by dbmate in a one-shot Compose service; dataclass DTOs
at repository ports; Unit of Work for transactions.

The backend contains `pyproject.toml` with `uv.lock`, a read-only atlas API and no model
providers. The `AtlasRepository` port in `usecase/interface.py` (DTOs in `usecase/dto.py`) is
implemented by `repository/files/atlas.py`, which reads the exported JSON from `DATA_DIR`
(default: repository `frontend/atlas/public`). Use cases live in `usecase/{regions,links,
settlements,search,overview,reference,index_status}.py`; projection and season rules in
`domain/{projection,transport,text}.py`. The `Logger` port takes an event name and `LogValue`
fields; `adapter/log/stdlib.py` implements it over `logging`. Modules outside `adapter/log/`,
`main.py` included, do not import `logging`; the import check enforces it. Other implementations
go to `adapter/<provider>/`; empty layer folders keep `.gitkeep`.

`main.py` exposes `create_app()` (run as `uvicorn app.main:create_app --factory`). It reads
`Settings` from `settings.py` (`DATA_DIR`), builds `JsonAtlasRepository`, the use cases and their
routers, and a `StdlibLogger` passed to `ErrorHandlers`. `controller/errors.py` owns the error
envelope and `STATUS_BY_ERROR`; `controller/router.py` exposes `build_api_router(*features)` with
the `/api/v1` prefix and the health route; feature routers carry no prefix. `controller/health/`
is the Compose healthcheck. `backend/openapi.json` is generated from `create_app().openapi()`.
Add new dependencies with
`uv add`; the Dockerfile installs strictly from `uv.lock`. When bootstrapping a project, add migrations, the storage service and the real first
scenario together. Remove a folder's `.gitkeep` when it gains source files. Follow
the dependency rules from the first implementation; validation commands apply once those tools
and files exist.
