from flask import Flask, render_template, request, jsonify
from GameBoard import GameBoard
from AdvancedCombatRules import calculate_damage
from DiplomacySystem import DiplomacySystem
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Game"))
from Factions import factions

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)

TURN_PHASES = [
    "Suunnitteluvaihe",
    "Toimintavaihe",
    "Hallintovaihe",
    "Tapahtumavaihe",
]

PHASE_ACTIONS = {
    "Suunnitteluvaihe": ["draw_strategy", "set_focus_conquest", "set_focus_trade", "set_focus_diplomacy"],
    "Toimintavaihe": ["move", "attack", "build", "trade", "diplomacy"],
    "Hallintovaihe": ["collect_resources", "pay_upkeep", "research"],
    "Tapahtumavaihe": ["resolve_event"],
}

ACTION_LABELS = {
    "draw_strategy": "Vedä strategiakortti",
    "set_focus_conquest": "Painopiste: Valloitus",
    "set_focus_trade": "Painopiste: Kauppa",
    "set_focus_diplomacy": "Painopiste: Diplomatia",
    "move": "Liiku",
    "attack": "Hyökkää",
    "build": "Rakenna",
    "trade": "Käy kauppaa",
    "diplomacy": "Neuvottele",
    "collect_resources": "Kerää resurssit",
    "pay_upkeep": "Maksa ylläpito",
    "research": "Kehitä teknologiaa",
    "resolve_event": "Ratkaise tapahtuma",
    "end_phase": "Lopeta vaihe",
}

VICTORY_GOALS = {
    "military": {"target": 12, "title": "Sotilaallinen voitto"},
    "economic": {"target": 12, "title": "Ekonominen voitto"},
    "cultural": {"target": 10, "title": "Kulttuurinen voitto"},
    "technology": {"target": 10, "title": "Teknologinen voitto"},
}

EVENT_SEQUENCE = [
    "Silkkitien satokausi: +2 kultaa",
    "Klaanikokous: +1 kulttuuripiste",
    "Sepät keksivät uusia varusteita: +1 teknologiapiste",
    "Rajakahakka: +1 sotilaspiste",
]

# Globaali pelitila (yksinkertaistettu, käytä sessioita tuotannossa)
game_state = {
    "board": None,
    "diplomacy": None,
    "player_faction": None,
    "turn": 0,
    "phase_index": 0,
    "focus": "Valloitus",
    "resources": {},
    "victory_progress": {
        "military": 0,
        "economic": 0,
        "cultural": 0,
        "technology": 0,
    },
    "winner": None,
    "event_index": 0,
}


def _starting_resources(faction_name):
    base = {
        "horses": 3,
        "gold": 3,
        "food": 3,
        "artisans": 2,
        "cattle": 3,
    }
    if faction_name == "Mongoli-heimo":
        base["horses"] += 2
        base["cattle"] += 1
    elif faction_name == "Kiinan dynastia":
        base["artisans"] += 2
        base["gold"] += 1
        game_state["victory_progress"]["technology"] += 1
    elif faction_name == "Persialainen valtakunta":
        base["gold"] += 2
        base["cattle"] += 1
        game_state["victory_progress"]["economic"] += 1
    elif faction_name == "Venäläiset ruhtinaskunnat":
        base["food"] += 2
        base["horses"] -= 1
        game_state["victory_progress"]["military"] += 1
    return base


def _current_phase():
    return TURN_PHASES[game_state["phase_index"]]


def _action_labels(actions):
    return {action: ACTION_LABELS[action] for action in actions}


def _serialize_board():
    board_data = []
    board = game_state["board"]
    for y in range(board.height):
        row = []
        for x in range(board.width):
            unit = board.board[y][x]
            if unit:
                row.append({"faction": unit["faction"], "type": unit["type"]})
            else:
                row.append(None)
        board_data.append(row)
    return board_data


def _game_snapshot(message=""):
    actions = PHASE_ACTIONS[_current_phase()] + ["end_phase"]
    return {
        "status": "ok",
        "message": message,
        "turn": game_state["turn"],
        "phase": _current_phase(),
        "focus": game_state["focus"],
        "resources": game_state["resources"],
        "victory_progress": game_state["victory_progress"],
        "victory_goals": VICTORY_GOALS,
        "winner": game_state["winner"],
        "board": _serialize_board(),
        "available_actions": actions,
        "action_labels": _action_labels(actions),
        "faction": game_state["player_faction"]["name"],
    }


def _find_unit_coordinates(faction_name):
    board = game_state["board"]
    for y in range(board.height):
        for x in range(board.width):
            cell = board.board[y][x]
            if cell and cell["faction"] == faction_name:
                return (x, y)
    return None


def _set_winner_if_reached():
    for key, goal in VICTORY_GOALS.items():
        if game_state["victory_progress"][key] >= goal["target"] and not game_state["winner"]:
            game_state["winner"] = goal["title"]
            return True
    return False


def _advance_phase():
    game_state["phase_index"] = (game_state["phase_index"] + 1) % len(TURN_PHASES)
    if game_state["phase_index"] == 0:
        game_state["turn"] += 1
    return f"Vaihe vaihdettu: {_current_phase()}."


def _apply_action(action):
    phase = _current_phase()
    player_name = game_state["player_faction"]["name"]
    board = game_state["board"]

    if action == "end_phase":
        return _advance_phase()

    if action not in PHASE_ACTIONS[phase]:
        return "Toiminto ei ole sallittu tässä vaiheessa."

    if action == "draw_strategy":
        game_state["victory_progress"]["technology"] += 1
        return "Strategiakortti vedetty (+1 teknologiapiste)."

    if action == "set_focus_conquest":
        game_state["focus"] = "Valloitus"
        return "Vuoron painopiste asetettu: Valloitus."

    if action == "set_focus_trade":
        game_state["focus"] = "Kauppa"
        return "Vuoron painopiste asetettu: Kauppa."

    if action == "set_focus_diplomacy":
        game_state["focus"] = "Diplomatia"
        return "Vuoron painopiste asetettu: Diplomatia."

    if action == "move":
        source = _find_unit_coordinates(player_name)
        if not source:
            return "Yksikköä ei löytynyt liikkumiseen."
        sx, sy = source
        tx, ty = min(sx + 1, board.width - 1), min(sy + 1, board.height - 1)
        if board.board[ty][tx] is None:
            board.board[ty][tx] = board.board[sy][sx]
            board.board[sy][sx] = None
            return "Yksikkö liikkui yhden alueen eteenpäin."
        return "Kohderuutu on varattu, liike epäonnistui."

    if action == "attack":
        attacker_position = _find_unit_coordinates(player_name)
        if not attacker_position:
            return "Hyökkäys epäonnistui: hyökkääjää ei löytynyt."
        attacker = board.board[attacker_position[1]][attacker_position[0]]
        defender = board.board[board.height - 1][board.width - 1]
        if not defender:
            return "Raja-alue on jo vallattu."
        damage = calculate_damage(attacker, defender)
        defender["defense"] -= damage
        game_state["victory_progress"]["military"] += 1
        if defender["defense"] <= 0:
            board.board[board.height - 1][board.width - 1] = None
            game_state["victory_progress"]["military"] += 3
            return f"Hyökkäys onnistui ({damage} vahinkoa) ja raja-alue vallattiin!"
        return f"Hyökkäys aiheutti {damage} vahinkoa puolustajalle."

    if action == "build":
        if game_state["resources"]["artisans"] < 1 or game_state["resources"]["gold"] < 1:
            return "Rakentaminen epäonnistui: resurssit eivät riitä."
        game_state["resources"]["artisans"] -= 1
        game_state["resources"]["gold"] -= 1
        game_state["victory_progress"]["cultural"] += 2
        return "Linnoitus ja kulttuurirakennus pystytetty (+2 kulttuuripistettä)."

    if action == "trade":
        if game_state["resources"]["cattle"] > 0:
            game_state["resources"]["cattle"] -= 1
            game_state["resources"]["gold"] += 2
        else:
            game_state["resources"]["gold"] += 1
        game_state["victory_progress"]["economic"] += 2
        return "Kauppa toteutettu (+2 talouspistettä)."

    if action == "diplomacy":
        relation = game_state["diplomacy"].get_relation(player_name, "Vihollinen")
        game_state["diplomacy"].set_relation(player_name, "Vihollinen", relation + 10)
        game_state["victory_progress"]["cultural"] += 1
        return f"Diplomatia vahvistui. Suhde viholliseen on nyt {relation + 10}."

    if action == "collect_resources":
        game_state["resources"]["horses"] += 1
        game_state["resources"]["food"] += 1
        game_state["resources"]["cattle"] += 1
        bonus_resource = "gold"
        if game_state["focus"] == "Kauppa":
            bonus_resource = "gold"
            game_state["victory_progress"]["economic"] += 1
        elif game_state["focus"] == "Diplomatia":
            bonus_resource = "artisans"
            game_state["victory_progress"]["cultural"] += 1
        elif game_state["focus"] == "Valloitus":
            bonus_resource = "horses"
            game_state["victory_progress"]["military"] += 1
        game_state["resources"][bonus_resource] += 1
        return "Resurssit kerätty hallituilta alueilta."

    if action == "pay_upkeep":
        if game_state["resources"]["food"] <= 0:
            game_state["victory_progress"]["military"] = max(0, game_state["victory_progress"]["military"] - 1)
            return "Ylläpito epäonnistui: ruoka loppui, armeijan moraali laski."
        game_state["resources"]["food"] -= 1
        return "Armeijan ylläpito maksettu."

    if action == "research":
        game_state["victory_progress"]["technology"] += 2
        if game_state["resources"]["artisans"] > 0:
            game_state["resources"]["artisans"] -= 1
        return "Teknologia kehittyi (+2 teknologiapistettä)."

    if action == "resolve_event":
        event_message = EVENT_SEQUENCE[game_state["event_index"] % len(EVENT_SEQUENCE)]
        game_state["event_index"] += 1
        if "kultaa" in event_message:
            game_state["resources"]["gold"] += 2
            game_state["victory_progress"]["economic"] += 1
        elif "kulttuuripiste" in event_message:
            game_state["victory_progress"]["cultural"] += 1
        elif "teknologiapiste" in event_message:
            game_state["victory_progress"]["technology"] += 1
        elif "sotilaspiste" in event_message:
            game_state["victory_progress"]["military"] += 1
        return f"Tapahtuma: {event_message}"

    return "Tuntematon toiminto."


@app.route("/")
def index():
    return render_template("index.html", factions=factions)


@app.route("/start_game", methods=["POST"])
def start_game():
    faction_choice = int(request.form["faction"])
    player_faction = factions[faction_choice]

    board = GameBoard(10, 10)
    diplomacy = DiplomacySystem()

    board.place_unit(0, 0, {"type": "warrior", "strength": 10, "defense": 5, "faction": player_faction["name"]})
    board.place_unit(9, 9, {"type": "warrior", "strength": 8, "defense": 6, "faction": "Vihollinen"})

    game_state["board"] = board
    game_state["diplomacy"] = diplomacy
    game_state["player_faction"] = player_faction
    game_state["turn"] = 1
    game_state["phase_index"] = 0
    game_state["focus"] = "Valloitus"
    game_state["victory_progress"] = {
        "military": 0,
        "economic": 0,
        "cultural": 0,
        "technology": 0,
    }
    game_state["winner"] = None
    game_state["event_index"] = 0
    game_state["resources"] = _starting_resources(player_faction["name"])
    _set_winner_if_reached()

    snapshot = _game_snapshot("Peli aloitettu lautapelin mukaisella vuororakenteella.")
    snapshot["status"] = "started"
    return jsonify(snapshot)


@app.route("/get_state")
def get_state():
    if not game_state["board"]:
        return jsonify({"error": "Game not started"}), 400
    return jsonify(_game_snapshot())


@app.route("/get_board")
def get_board():
    if not game_state["board"]:
        return jsonify({"error": "Game not started"}), 400
    return jsonify(_game_snapshot())


@app.route("/take_action", methods=["POST"])
def take_action():
    if not game_state["board"]:
        return jsonify({"error": "Game not started"}), 400

    payload = request.get_json(silent=True) or {}
    action = payload.get("action", "").strip()
    if not action:
        return jsonify({"error": "Action is required"}), 400

    message = _apply_action(action)
    _set_winner_if_reached()
    return jsonify(_game_snapshot(message))


@app.route("/attack", methods=["POST"])
def attack():
    if not game_state["board"]:
        return jsonify({"error": "Game not started"}), 400
    message = _apply_action("attack")
    _set_winner_if_reached()
    return jsonify(_game_snapshot(message))


@app.route("/diplomacy", methods=["POST"])
def diplomacy_action():
    if not game_state["board"]:
        return jsonify({"error": "Game not started"}), 400
    message = _apply_action("diplomacy")
    _set_winner_if_reached()
    return jsonify(_game_snapshot(message))


if __name__ == "__main__":
    app.run(debug=True)