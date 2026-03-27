"""REST API routes for game actions."""
from __future__ import annotations

import logging
from flask import Blueprint, request, jsonify, Response

from backend.engine.game_engine import GameEngine
from backend.models.faction import FACTIONS

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__, url_prefix="/api")

_engines: dict[str, GameEngine] = {}


def _get_engine() -> GameEngine:
    """Get or create the session-scoped game engine."""
    session_id = request.cookies.get("session_id", "default")
    if session_id not in _engines:
        _engines[session_id] = GameEngine()
    return _engines[session_id]


@api.route("/factions", methods=["GET"])
def list_factions() -> Response:
    """Return available factions."""
    return jsonify({"factions": [f.to_dict() for f in FACTIONS]})


@api.route("/start_game", methods=["POST"])
def start_game() -> Response:
    """Start a new game with the chosen faction."""
    data = request.get_json(silent=True) or {}
    faction_index = data.get("faction")

    if faction_index is None:
        faction_index = request.form.get("faction")

    if faction_index is None:
        return jsonify({"success": False, "error": "Heimovalinta puuttuu."}), 400

    try:
        faction_index = int(faction_index)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Virheellinen heimovalinta."}), 400

    engine = _get_engine()
    result = engine.new_game(faction_index)

    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)


@api.route("/state", methods=["GET"])
def get_state() -> Response:
    """Return current full game state."""
    engine = _get_engine()
    result = engine.get_state()
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@api.route("/action", methods=["POST"])
def perform_action() -> Response:
    """Execute a game action (move, attack, diplomacy, etc.)."""
    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if not action:
        return jsonify({"success": False, "error": "Toiminto puuttuu."}), 400

    params = {k: v for k, v in data.items() if k != "action"}

    engine = _get_engine()
    result = engine.perform_action(action, **params)

    status = 200 if result.get("success", False) else 400
    return jsonify(result), status
