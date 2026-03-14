# Arojen-tarinat

A multi-language game project featuring implementations in JavaScript, Python, and TypeScript (removed). The project includes various game components like combat rules, diplomacy, and factions.

## Project Structure

- `Game/`: Contains Python files for game logic (e.g., Factions.py).
- `JSGame/`: JavaScript implementations of game components.
- `PythonGame/`: Python implementations of game components.

## Installation

### JavaScript (JSGame)
1. Ensure Node.js is installed.
2. Navigate to the project root.
3. Run `npm install` if package.json exists, or run files directly with Node.js.

### Python (PythonGame and Game)
1. Ensure Python 3.x is installed.
2. Install dependencies if any (none currently).
3. Run Python files directly: `python Factions.py`

## Usage

### Python Web Game
- Run the web game: `cd PythonGame && python app.py`
- Open browser at http://127.0.0.1:5000/
- Select faction, play on the visual board.

### JavaScript
- Run the game: `cd JSGame && npm start`
- Or directly: `node JSGame/main.js`
- Scripts: `cd JSGame && npm run lint`, `npm run test`

### Python Console Game
- Run the console game: `cd PythonGame && python main.py`

## Automation

- **CI/CD**: GitHub Actions runs linting and tests on push/PR (see `.github/workflows/ci.yml`).
- **Scripts**: Run `./check-all.sh` to lint and test all components.
- **IDE Extensions**: Install GitLens, Python, ESLint in VS Code for better development experience.

## Architecture

The project is organized into three language-specific folders for modularity. Each component (e.g., Combat, Diplomacy) has implementations in both JS and Python for cross-language compatibility.

- **Combat System**: Handles damage calculations.
- **Game Board**: Manages grid-based unit placement.
- **Diplomacy System**: Tracks relations between factions.
- **Factions**: Defines game factions with bonuses and starting units.

## API Documentation

### JavaScript (JSDoc)
- See inline JSDoc comments in JSGame/*.js files.

### Python (Docstrings)
- See inline docstrings in PythonGame/*.py and Game/*.py files.

## Contributing

- Follow coding standards: ESLint for JS, PEP 8 for Python.
- Write unit tests for new features (Jest for JS, unittest for Python).
- Update documentation as needed.
- Run `./check-all.sh` before committing.