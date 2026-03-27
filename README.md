# Arojen-tarinat — Mongolien Valtakunta

A turn-based strategy web game set in the steppes of Central Asia. Choose your faction, command units on a grid-based board, engage in combat, diplomacy, and resource management to achieve victory.

## Architecture

```
backend/              Flask application (app factory + blueprints)
  ├── models/         Domain models: Unit, Board, Faction, GameState
  ├── engine/         Game logic: Combat, Diplomacy, Resources, Turns, Victory
  ├── routes/         API + page-serving blueprints
  ├── tests/          Pytest test suite
  ├── app.py          App factory
  └── config.py       Environment configurations
frontend/             Browser client
  ├── templates/      Jinja2 HTML templates
  └── static/         CSS + modular JS (api, board, ui, constants, app)
JSGame/               Node.js console game (standalone)
Game/                 Legacy shared factions data
PythonGame/           Legacy Python console + web game (preserved)
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements-dev.txt
cd JSGame && npm install && cd ..

# Run development server
python run.py
# Open http://localhost:5000

# Run all tests
make check
```

## Commands

| Command           | Description                      |
|-------------------|----------------------------------|
| `make dev`        | Install dev dependencies         |
| `make run`        | Start dev server (port 5000)     |
| `make test`       | Run backend pytest suite         |
| `make lint`       | Lint backend with pylint         |
| `make test-js`    | Run JSGame Jest tests            |
| `make check`      | Run all lints + tests            |
| `make run-prod`   | Run with Gunicorn                |
| `make docker-build` | Build Docker image             |

## Game Overview

### Factions
- **Mongoli-heimo** — Cavalry bonus, fast movement
- **Kiinan dynastia** — Fortifications, technology
- **Persialainen valtakunta** — Trade skills, cultural resources
- **Venäläiset ruhtinaskunnat** — Winter tactics, forest resources

### Turn Phases
1. **Movement** — Move your units on the board
2. **Combat** — Attack enemy units in range
3. **Diplomacy** — Improve relations with other factions
4. **Resources** — Collect resources, heal or recruit units

### Victory Conditions
- **Military** — Destroy all enemy units
- **Diplomatic** — Reach alliance threshold (50)
- **Attrition** — Have more units when turn limit is reached

## Deployment

```bash
# Docker
docker build -t arojen-tarinat .
docker run -p 8000:8000 arojen-tarinat

# Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
```

## Contributing

- Run `make check` before committing
- Write tests for new features
- Follow PEP 8 for Python, ESLint for JS
