# Objective
- Build an conversational and map-based app to support geodetic decisions

# Project structure
- `src/` - Application source code (including `src/webui/` for the WebUI)
- `tests/` - Unit and integration tests

# Coding style
- Adhere to PEP8 for Python
- Use type hints for function signatures
- Add Google-Style docsting to classes, modules and functions
- Implement using the red/greed TDD pattern

# Git Workflow
- If you are asked to work on `main`, stop and request a new branch.

# Commands
- Run: `uv run`
- Run webui: `uv run streamlit run ./src/webui/app.py`
- Test: `uv run pytest`
- Lint: `uv run ruff check`

## Boundaries
- Always: Create unit test before writing a function, follow naming conventions
- Ask first: Database schema changes, adding dependencies
- Never: Commit secrets or environment variables
- Strictly forbidden hardcoding secrets
