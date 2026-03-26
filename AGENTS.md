# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Arojen-tarinat is a multi-language strategy game with three components:
- **JSGame/** — Node.js console game (CommonJS) with Jest tests and ESLint
- **PythonGame/** — Python console game + Flask web app with browser UI
- **Game/** — Shared Python module (Factions data) used by PythonGame

No databases, Docker, or external services are required. All state is in-memory.

### Running services

| Service | Command | Notes |
|---|---|---|
| Flask web game | `cd PythonGame && python app.py` | Serves at http://127.0.0.1:5000 |
| JS console game | `cd JSGame && node main.js` | Non-interactive; exits after one round |
| Python console game | `cd PythonGame && python main.py` | Interactive; needs stdin input |

### Lint and test commands

See `README.md` and `check-all.sh` for the full list. Summary:

| Component | Lint | Test |
|---|---|---|
| JSGame | `cd JSGame && npm run lint` | `cd JSGame && npm test` |
| PythonGame | `cd PythonGame && make lint` | `cd PythonGame && make test` |
| Game | `cd Game && make lint` | `cd Game && make test` |

Run all at once: `bash check-all.sh` (from repo root).

### Non-obvious caveats

- The ESLint config (`JSGame/eslint.config.mjs`) references plugins not listed in `package.json` (`@eslint/js`, `eslint-plugin-react`, `@eslint/json`, `@eslint/markdown`, `@eslint/css`). The update script installs them with `--legacy-peer-deps` due to a peer conflict between `eslint-plugin-react` and ESLint v10.
- ESLint reports ~49 `no-undef` errors for `module`, `require`, `console`, `process`, `test`, `expect` globals. These are pre-existing in the repo (CommonJS + Jest globals not configured in the ESLint config). ESLint runs but exits non-zero.
- pylint reports convention/style warnings (missing docstrings, snake_case names) and exits non-zero. This is expected — the repo code triggers these warnings.
- The Makefiles use `python` (not `python3`). The update script ensures `/usr/bin/python` symlink exists.
- The `Game/` module has no tests (unittest discover finds 0). This is expected.
