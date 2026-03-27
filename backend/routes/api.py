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


@api.route("/highlights", methods=["GET"])
def get_highlights() -> Response:
    """Return valid move and attack targets for a unit at (x, y)."""
    engine = _get_engine()
    if engine.state is None:
        return jsonify({"error": "Peliä ei ole aloitettu."}), 400

    try:
        x = int(request.args.get("x", -1))
        y = int(request.args.get("y", -1))
    except (ValueError, TypeError):
        return jsonify({"error": "Virheelliset koordinaatit."}), 400

    state = engine.state
    unit = state.board.get_unit(x, y)
    if unit is None:
        return jsonify({"move": [], "attack": []})

    move_targets: list[list[int]] = []
    attack_targets: list[list[int]] = []

    is_player = unit.faction_id == state.player_faction.faction_id

    if is_player and not unit.has_acted:
        for ty in range(state.board.height):
            for tx in range(state.board.width):
                dist = state.board.distance(x, y, tx, ty)
                if dist == 0:
                    continue
                occupant = state.board.get_unit(tx, ty)
                if occupant is None and dist <= unit.speed:
                    move_targets.append([tx, ty])
                if (occupant is not None
                        and occupant.faction_id != unit.faction_id
                        and dist <= unit.attack_range):
                    attack_targets.append([tx, ty])

    return jsonify({
        "move": move_targets,
        "attack": attack_targets,
        "unit": unit.to_dict(),
    })
