from flask import Flask, jsonify, render_template, request
from GameBoard import GameBoard
from DiplomacySystem import DiplomacySystem
import os
import random
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

UNIT_TYPES = {
    "cavalry": {"label": "Ratsuväki", "token": "🐎", "strength": 6, "defense": 3, "hp": 7},
    "infantry": {"label": "Jalkaväki", "token": "🛡️", "strength": 4, "defense": 5, "hp": 8},
    "chief": {"label": "Heimopäällikkö", "token": "👑", "strength": 5, "defense": 6, "hp": 9},
    "merchant": {"label": "Kauppias", "token": "🧭", "strength": 2, "defense": 2, "hp": 5},
}

FACTION_LOADOUTS = {
    "Mongoli-heimo": ["cavalry", "cavalry", "infantry", "chief", "merchant"],
    "Kiinan dynastia": ["infantry", "infantry", "cavalry", "chief", "merchant"],
    "Persialainen valtakunta": ["merchant", "cavalry", "infantry", "chief", "merchant"],
    "Venäläiset ruhtinaskunnat": ["infantry", "infantry", "cavalry", "chief", "merchant"],
}

FACTION_SPAWN_POINTS = {
    "Mongoli-heimo": [(1, 1), (2, 1), (1, 2), (2, 2), (3, 1)],
    "Kiinan dynastia": [(10, 1), (9, 1), (10, 2), (9, 2), (8, 1)],
    "Persialainen valtakunta": [(1, 10), (2, 10), (1, 9), (2, 9), (3, 10)],
    "Venäläiset ruhtinaskunnat": [(10, 10), (9, 10), (10, 9), (9, 9), (8, 10)],
}

RIVAL_FACTION = "Kiinan dynastia"

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
    "battle": {"last": None, "history": []},
    "factions_state": {},
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


def _create_unit(faction_name, unit_key, side):
    base = UNIT_TYPES[unit_key]
    return {
        "faction": faction_name,
        "unit_key": unit_key,
        "type": base["label"],
        "token": base["token"],
        "strength": base["strength"],
        "defense": base["defense"],
        "hp": base["hp"],
        "max_hp": base["hp"],
        "side": side,
    }


def _all_faction_names():
    return [faction["name"] for faction in factions]


def _init_factions_state(player_faction_name):
    faction_state = {}
    for faction in factions:
        name = faction["name"]
        loadout = FACTION_LOADOUTS.get(name, [])
        unit_counts = {unit_key: 0 for unit_key in UNIT_TYPES.keys()}
        for unit_key in loadout:
            unit_counts[unit_key] += 1
        faction_state[name] = {
            "name": name,
            "color": faction.get("color", "gray"),
            "is_player": name == player_faction_name,
            "unit_counts": unit_counts,
            "total_units": len(loadout),
        }
    return faction_state


def _serialize_factions_state():
    ordered = []
    for faction in factions:
        name = faction["name"]
        ordered.append(game_state["factions_state"].get(name))
    return ordered


def _serialize_board():
    board_data = []
    board = game_state["board"]
    for y in range(board.height):
        row = []
        for x in range(board.width):
            unit = board.board[y][x]
            if unit:
                row.append(
                    {
                        "faction": unit["faction"],
                        "type": unit["type"],
                        "unit_key": unit["unit_key"],
                        "token": unit["token"],
                        "hp": unit["hp"],
                        "max_hp": unit["max_hp"],
                        "side": unit["side"],
                    }
                )
            else:
                row.append(None)
        board_data.append(row)
    return board_data


def _recount_faction_units():
    fresh_counts = {
        name: {unit_key: 0 for unit_key in UNIT_TYPES.keys()}
        for name in _all_faction_names()
    }
    board = game_state["board"]
    for y in range(board.height):
        for x in range(board.width):
            unit = board.board[y][x]
            if not unit:
                continue
            fresh_counts[unit["faction"]][unit["unit_key"]] += 1

    for faction_name, state in game_state["factions_state"].items():
        counts = fresh_counts[faction_name]
        state["unit_counts"] = counts
        state["total_units"] = sum(counts.values())


def _list_units(faction_name=None, exclude_faction=None):
    board = game_state["board"]
    units = []
    for y in range(board.height):
        for x in range(board.width):
            unit = board.board[y][x]
            if not unit:
                continue
            if faction_name and unit["faction"] != faction_name:
                continue
            if exclude_faction and unit["faction"] == exclude_faction:
                continue
            units.append((x, y, unit))
    return units


def _place_initial_units(player_faction_name):
    board = game_state["board"]
    for faction_name in _all_faction_names():
        loadout = FACTION_LOADOUTS[faction_name]
        spawn_points = FACTION_SPAWN_POINTS[faction_name]
        side = "player" if faction_name == player_faction_name else "enemy"
        for idx, unit_key in enumerate(loadout):
            x, y = spawn_points[idx]
            board.place_unit(x, y, _create_unit(faction_name, unit_key, side))


def _find_unit_coordinates(faction_name):
    board = game_state["board"]
    for y in range(board.height):
        for x in range(board.width):
            cell = board.board[y][x]
            if cell and cell["faction"] == faction_name:
                return (x, y)
    return None


def _nearest_enemy(attacker_x, attacker_y, player_name):
    enemies = _list_units(exclude_faction=player_name)
    if not enemies:
        return None
    return min(
        enemies,
        key=lambda entry: abs(entry[0] - attacker_x) + abs(entry[1] - attacker_y),
    )


def _record_battle(report):
    game_state["battle"]["last"] = report
    game_state["battle"]["history"].insert(0, report)
    game_state["battle"]["history"] = game_state["battle"]["history"][:6]


def _serialize_battle():
    battle = game_state.get("battle") or {"last": None, "history": []}
    last = battle.get("last")
    payload = {
        "history": battle.get("history", []),
        "last": last,
    }
    if last:
        payload.update(
            {
                "attack_die": last["attack_die"],
                "defense_die": last["defense_die"],
                "attack_total": last["attack_total"],
                "defense_total": last["defense_total"],
                "damage_to_defender": last["damage_to_defender"],
                "damage_to_attacker": last["damage_to_attacker"],
                "outcome": last["outcome"],
            }
        )
    return payload


def _battle_roll(attacker, defender):
    attack_die = random.randint(1, 6)
    defense_die = random.randint(1, 6)
    attack_total = attacker["strength"] + attack_die
    defense_total = defender["defense"] + defense_die
    return attack_die, defense_die, attack_total, defense_total


def _resolve_attack(player_name):
    player_units = _list_units(faction_name=player_name)
    if not player_units:
        return "Hyökkäys epäonnistui: pelaajan pelinappulat puuttuvat."

    attacker_x, attacker_y, attacker = max(player_units, key=lambda item: item[2]["strength"])
    defender_entry = _nearest_enemy(attacker_x, attacker_y, player_name)
    if not defender_entry:
        return "Vastustajan pelinappuloita ei löytynyt."

    defender_x, defender_y, defender = defender_entry
    attack_die, defense_die, attack_total, defense_total = _battle_roll(attacker, defender)

    result = {
        "attacker_faction": attacker["faction"],
        "defender_faction": defender["faction"],
        "attacker_unit": attacker["type"],
        "defender_unit": defender["type"],
        "attack_die": attack_die,
        "defense_die": defense_die,
        "attack_total": attack_total,
        "defense_total": defense_total,
        "damage_to_defender": 0,
        "damage_to_attacker": 0,
        "outcome": "torjunta",
    }

    board = game_state["board"]
    if attack_total > defense_total:
        damage = max(1, attack_die + attacker["strength"] // 3 - defender["defense"] // 4)
        defender["hp"] -= damage
        result["damage_to_defender"] = damage
        result["outcome"] = "osuma"
        game_state["victory_progress"]["military"] += 1
        if defender["hp"] <= 0:
            board.board[defender_y][defender_x] = None
            result["outcome"] = "yksikkö tuhottu"
            game_state["victory_progress"]["military"] += 2
    else:
        retaliation = max(0, defense_die - attack_die)
        if retaliation > 0:
            attacker["hp"] -= retaliation
            result["damage_to_attacker"] = retaliation
            if attacker["hp"] <= 0:
                board.board[attacker_y][attacker_x] = None
                result["outcome"] = "hyökkääjä kaatui"
        else:
            result["outcome"] = "torjunta ilman vahinkoa"

    _recount_faction_units()
    _record_battle(result)
    return (
        f"Taistelu: hyökkäysnoppa {attack_die}, puolustusnoppa {defense_die}. "
        f"Tulos: {result['outcome']}."
    )


def _game_snapshot(message=""):
    actions = PHASE_ACTIONS[_current_phase()] + ["end_phase"]
    factions_state = _serialize_factions_state()
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
        "factions_state": factions_state,
        "factions": factions_state,
        "unit_types": UNIT_TYPES,
        "battle": _serialize_battle(),
    }


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
        return _resolve_attack(player_name)

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
        relation = game_state["diplomacy"].get_relation(player_name, RIVAL_FACTION)
        game_state["diplomacy"].set_relation(player_name, RIVAL_FACTION, relation + 10)
        game_state["victory_progress"]["cultural"] += 1
        return f"Diplomatia vahvistui. Suhde {RIVAL_FACTION}-faktioon on nyt {relation + 10}."

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

    board = GameBoard(12, 12)
    diplomacy = DiplomacySystem()

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
    game_state["battle"] = {"last": None, "history": []}
    game_state["factions_state"] = _init_factions_state(player_faction["name"])

    _place_initial_units(player_faction["name"])
    _recount_faction_units()
    _set_winner_if_reached()

    snapshot = _game_snapshot(
        "Peli aloitettu: heimot, pelinappulat ja taistelunäkymä ovat käytössä."
    )
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


@app.route("/battle_roll", methods=["POST"])
def battle_roll():
    if not game_state["board"]:
        return jsonify({"error": "Game not started"}), 400
    if _current_phase() != "Toimintavaihe":
        return jsonify({"error": "Battle roll is only allowed during Toimintavaihe"}), 400
    message = _apply_action("attack")
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