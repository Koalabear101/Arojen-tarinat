#!/bin/bash
set -e

echo "═══════════════════════════════════════════"
echo "  Arojen-tarinat — Full Check Suite"
echo "═══════════════════════════════════════════"

echo ""
echo "▶ Backend lint..."
python -m pylint backend/ --disable=C0114,C0115,C0116,C0103,R0903 --fail-under=7

echo ""
echo "▶ Backend tests..."
python -m pytest backend/tests/ -v

echo ""
echo "▶ JSGame tests..."
cd JSGame
npm test
cd ..

echo ""
echo "▶ Legacy PythonGame tests..."
cd PythonGame
python -m unittest discover .
cd ..

echo ""
echo "═══════════════════════════════════════════"
echo "  All checks passed!"
echo "═══════════════════════════════════════════"
