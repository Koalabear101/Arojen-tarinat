# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Arojen-tarinat is a turn-based strategy web game with a production-grade architecture:

- **`backend/`** — Flask app factory with blueprints, game engine classes, domain models, and pytest suite
- **`frontend/`** — Jinja2 templates + modular JS (api, board, ui, constants, app) + professional CSS
- **`JSGame/`** — Standalone Node.js console game with Jest tests (unchanged)
- **`PythonGame/`** — Legacy Python console + web game (preserved, not used by new backend)
- **`Game/`** — Legacy shared factions module (preserved)

No databases, Docker, or external services are required. All state is in-memory.

### Running services

| Service | Command | Notes |
|---|---|---|
| Dev server (new) | `python run.py` | Flask at http://127.0.0.1:5000 |
| Production server | `gunicorn --bind 0.0.0.0:8000 wsgi:app` | Gunicorn |
| JS console game | `cd JSGame && node main.js` | Standalone |
| Legacy Flask game | `cd PythonGame && python app.py` | Legacy, port 5000 |

### Lint, test, and build commands

Use `make check` to run everything, or individually:

| What | Command |
|---|---|
| Backend tests | `make test` or `python -m pytest backend/tests/ -v` |
| Backend lint | `make lint` |
| JS tests | `make test-js` |
| All checks | `make check` |
| Dev server | `make run` |

### Non-obvious caveats

- The new backend uses an app factory (`backend/app.py`) with blueprints. The entry point is `run.py` (dev) or `wsgi.py` (prod).
- Game state is per-session in memory via cookie-based session ID. No database needed.
- The ESLint config for JSGame references plugins not in `package.json` — the update script installs them with `--legacy-peer-deps`.
- Legacy `PythonGame/` Makefiles use `python` (not `python3`). The update script ensures the symlink exists.
- pylint is run with several convention checks disabled (`C0114,C0115,C0116,C0103,R0903`) and `--fail-under=7` for the new backend.
