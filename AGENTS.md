# Repository Guidelines

## Project Structure & Module Organization
Core automation sits in `src/`: `main.py` orchestrates scheduling, `github_client.py` talks to GitHub, `repo_manager.py` manages local clones, and `claude_executor.py` drives Claude Code. `health_server.py` exposes the readiness endpoint, while `config.py` loads `.env` settings. Logs stream to `logs/automator.log`. Container and platform configs (`Dockerfile`, `docker-compose.yml`, `railway.toml`, `nixpacks.toml`) live at the repo root. Place fixtures in `config/` and stage new tests under `tests/` mirroring the module layout.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` — install runtime dependencies for local execution.
- `python src/main.py` — start the scheduler that polls GitHub, invokes Claude Code, and updates issues.
- `docker-compose up --build` — run the service and health endpoint inside the provided container stack.
- `docker-compose logs -f` — stream application logs (same content as `logs/automator.log`).

## Coding Style & Naming Conventions
Target Python 3.11, follow PEP 8 with 4-space indentation, and prefer descriptive snake_case for functions, methods, and modules. Use PascalCase only for classes such as new managers or clients. Keep configuration constants uppercase in `config.py`, log via `logging.getLogger(__name__)`, and add type hints for new public functions. If you introduce formatting tools (e.g., `black`, `ruff`), note the command here.

## Testing Guidelines
No automated tests exist yet; add `pytest` suites for new code. Organize tests under `tests/<module_name>/test_<feature>.py` mirroring `src/`. Mock GitHub and Claude interactions, assert that failure paths update `IssueTracker` backoff state, and clean up temporary repositories. Run locally with `pytest` (after `pip install pytest`).

## Commit & Pull Request Guidelines
Write commit subjects in imperative mood (e.g., `Fix GitHub authentication for git operations`) and keep them concise. For pull requests, cover purpose and affected modules, verification steps with logs or CLI snippets, and linked GitHub issues (`Fixes #123`). Attach screenshots or transcripts when automation prompts or integrations change. Keep branches short-lived and rebase before merging.

## Security & Configuration Tips
Never commit `.env` or credentials; rely on environment variables loaded by `Config`. Rotate tokens regularly, scope GitHub PATs narrowly, and scrub secrets from shared logs. Prefer local `.env` overrides instead of editing tracked configuration files.
