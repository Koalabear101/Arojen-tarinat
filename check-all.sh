#!/bin/bash

echo "Running lint and tests for JSGame..."
cd JSGame
npm run lint
npm test

echo "Running lint and tests for PythonGame..."
cd ../PythonGame
make lint
make test

echo "Running lint and tests for Game..."
cd ../Game
make lint
make test

echo "Testing games..."
cd ../PythonGame
python main.py <<< "1
quit"  # Simuloi input

cd ../JSGame
node main.js

echo "All checks completed."