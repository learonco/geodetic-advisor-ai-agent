# Objective
- Build an conversational app to support geodetic decisions

# Project structure
- `src/` - Application source code (including `src/webui/` for the WebUI)
- `tests/` - Unit and integration tests

# Coding style
- Follow PEP8 for Python

# Commands
- Run: `uv run`
- Test: `uv run pytest`
- Lint: `uv run ruff check`

## Boundaries
- Always: Create unit test before writing a funciont, follow naming conventions
- Ask first: Database schema changes, adding dependencies
- Never: Commit secrets or environment variables
