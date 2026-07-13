# TripPilot Backend

FastAPI app that will host the LangGraph agent orchestrator and MCP client pool.

## Local dev

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
cp .env.example .env          # fill in secrets as needed
uv run uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Checks

```bash
uv run pytest      # tests
uv run ruff check  # lint
uv run mypy app    # types
```

## Layout

```
app/
  main.py          # FastAPI app factory + router wiring
  config.py        # pydantic-settings
  api/v1/          # versioned routes (health so far)
tests/             # pytest
```

See [`../PROJECT_PLAN.md`](../PROJECT_PLAN.md) §8 for the target structure
(agents/, mcp/, models/, schemas/, services/, db/) as it fills in.
