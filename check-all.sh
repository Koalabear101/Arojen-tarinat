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

echo "All checks completed."