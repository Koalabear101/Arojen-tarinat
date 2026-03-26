from flask import Flask, jsonify, render_template, request
from GameBoard import GameBoard
from DiplomacySystem import DiplomacySystem
import math
import os
import random
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Game"))
from Factions import factions

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)

TURN_PHASES = [
    "Resurssivaihe",
    "Korttivaihe",
    "Liikevaihe",
    "Taisteluvaihe",
    "Hallintavaihe",
    "Vuoron lopetus",
]

PHASE_ACTIONS = {
    "Resurssivaihe": ["collect_resources", "next_phase", "end_turn"],
    "Korttivaihe": ["draw_card", "play_card", "next_phase", "end_turn"],
    "Liikevaihe": ["hex_click", "move", "next_phase", "end_turn"],
    "Taisteluvaihe": ["hex_click", "attack", "next_phase", "end_turn"],
    "Hallintavaihe": [
        "recruit_infantry",
        "recruit_cavalry",
        "recruit_merchant",
        "build_camp",
        "build_market",
        "build_fortress",
        "research",
        "next_phase",
        "end_turn",
    ],
    "Vuoron lopetus": ["end_turn", "next_phase"],
}

ACTION_LABELS = {
    "collect_resources": "Kerää resurssit",
    "draw_card": "Nosta kortti",
    "play_card": "Pelaa valittu kortti",
    "hex_click": "Valitse heksi",
    "recruit_infantry": "Rekrytoi jalkaväki",
    "recruit_cavalry": "Rekrytoi ratsuväki",
    "recruit_merchant": "Rekrytoi kauppias",
    "build_camp": "Rakenna leiri",
    "build_market": "Rakenna markkina",
    "build_fortress": "Rakenna linnoitus",
    "research": "Tutki teknologiaa",
    "next_phase": "Seuraava vaihe",
    "end_turn": "Lopeta vuoro",
    # Legacy aliases for compatibility
    "end_phase": "Lopeta vaihe",
    "move": "Liiku",
    "attack": "Hyökkää",
    "build": "Rakenna",
    "trade": "Käy kauppaa",
    "diplomacy": "Neuvottele",
    "draw_strategy": "Vedä strategiakortti",
}

VICTORY_GOALS = {
    "military_elimination": {"target": 1, "title": "Sotilaallinen voitto (vihollinen tuhottu)"},
    "military_control": {"target": 28, "title": "Sotilaallinen voitto (aluehallinta)"},
    "economic": {"target": 30, "title": "Talousvoitto"},
    "technology": {"target": 5, "title": "Teknologiavoitto"},
}

UNIT_RECRUIT_COSTS = {
    "infantry": {"gold": 1, "food": 1},
    "cavalry": {"gold": 1, "food": 1, "horses": 2},
    "merchant": {"gold": 2},
}

BUILDING_COSTS = {
    "camp": {"gold": 2, "food": 1, "artisans": 1},
    "market": {"gold": 2, "artisans": 1},
    "fortress": {"gold": 2, "artisans": 2},
}

BUILDING_LABELS = {
    "camp": "Leiri",
    "market": "Markkina",
    "fortress": "Linnoitus",
}

CARD_LIBRARY = [
    {"id": "str_1", "name": "Joenylitys", "kind": "strategy", "cost": {"gold": 1}, "effect": "ignore_river_penalty_turn", "desc": "Ohita jokirangaistus tällä vuorolla."},
    {"id": "str_2", "name": "Vuoristoreitit", "kind": "strategy", "cost": {"artisans": 1}, "effect": "mountain_move_discount_turn", "desc": "Vuoristoliikekustannus pienenee vuoron ajaksi."},
    {"id": "str_3", "name": "Mongolivyöry", "kind": "strategy", "cost": {"horses": 1}, "effect": "attack_bonus_3_turn", "desc": "+3 hyökkäys seuraavaan taisteluun."},
    {"id": "str_4", "name": "Sivustaisku", "kind": "strategy", "cost": {"gold": 1}, "effect": "cavalry_attack_bonus_2_turn", "desc": "Ratsuväelle +2 hyökkäys vuoron ajaksi."},
    {"id": "str_5", "name": "Kilpimuuri", "kind": "strategy", "cost": {"food": 1}, "effect": "infantry_defense_bonus_2_turn", "desc": "Jalkaväelle +2 puolustus vuoron ajaksi."},
    {"id": "dip_1", "name": "Kauppasopimus", "kind": "diplomacy", "cost": {"gold": 1}, "effect": "gold_per_turn_1_perm", "desc": "+1 kulta jokaisessa resurssivaiheessa."},
    {"id": "dip_2", "name": "Rajalupaus", "kind": "diplomacy", "cost": {"food": 1}, "effect": "ai_attack_penalty_turn", "desc": "AI:n hyökkäysvoima -1 vuoron ajaksi."},
    {"id": "dip_3", "name": "Karavaanireitti", "kind": "diplomacy", "cost": {"gold": 1}, "effect": "merchant_income_bonus_perm", "desc": "Kauppiaat tuottavat +1 kultaa vuorossa."},
    {"id": "dip_4", "name": "Liittouman lähettiläs", "kind": "diplomacy", "cost": {"artisans": 1}, "effect": "diplomacy_points_1", "desc": "+1 talouspiste ja +1 teknologiapiste."},
    {"id": "dip_5", "name": "Verovapaus", "kind": "diplomacy", "cost": {}, "effect": "free_market_build_turn", "desc": "Seuraava markkina ilman kultakustannusta."},
    {"id": "tech_1", "name": "Yhdistetty jousi", "kind": "technology", "cost": {"artisans": 1}, "effect": "cavalry_attack_bonus_1_perm", "desc": "Pysyvä +1 ratsuväen hyökkäys."},
    {"id": "tech_2", "name": "Rautakärjet", "kind": "technology", "cost": {"artisans": 1, "gold": 1}, "effect": "infantry_attack_bonus_1_perm", "desc": "Pysyvä +1 jalkaväen hyökkäys."},
    {"id": "tech_3", "name": "Piiritystekniikka", "kind": "technology", "cost": {"artisans": 1}, "effect": "fortress_defense_ignore_1_perm", "desc": "Hyökkäys sivuuttaa 1 pisteen linnoitusbonuksesta."},
    {"id": "tech_4", "name": "Arkistot", "kind": "technology", "cost": {"artisans": 1, "food": 1}, "effect": "tech_progress_1", "desc": "+1 teknologiapiste."},
    {"id": "tech_5", "name": "Universaali tiede", "kind": "technology", "cost": {"artisans": 2, "gold": 2}, "effect": "universal_science", "desc": "Laukaisee teknologiavoiton ehdon."},
    {"id": "res_1", "name": "Viljavarasto", "kind": "resource", "cost": {}, "effect": "gain_food_2", "desc": "+2 ruokaa."},
    {"id": "res_2", "name": "Hevoslauma", "kind": "resource", "cost": {}, "effect": "gain_horses_2", "desc": "+2 hevosta."},
    {"id": "res_3", "name": "Kaivoslöytö", "kind": "resource", "cost": {}, "effect": "gain_gold_3", "desc": "+3 kultaa."},
    {"id": "res_4", "name": "Käsityöpajat", "kind": "resource", "cost": {"gold": 1}, "effect": "gain_artisans_2", "desc": "+2 käsityöläistä."},
    {"id": "res_5", "name": "Sotasaalis", "kind": "resource", "cost": {}, "effect": "gain_mixed_2", "desc": "+1 kulta ja +1 ruoka."},
]

UNIT_TYPES = {
    "cavalry": {"label": "Ratsuväki", "token": "🐎", "strength": 6, "defense": 3, "hp": 7},
    "infantry": {"label": "Jalkaväki", "token": "🛡️", "strength": 4, "defense": 5, "hp": 8},
    "chief": {"label": "Heimopäällikkö", "token": "👑", "strength": 5, "defense": 6, "hp": 9},
    "merchant": {"label": "Kauppias", "token": "🧭", "strength": 2, "defense": 2, "hp": 5},
}

BOARD_WIDTH = 20
BOARD_HEIGHT = 20
TERRAIN_TYPES = ["water", "shore", "plains", "forest", "mountain", "desert", "river", "lake"]
SEA_LEVEL = 0.28
COAST_LEVEL = 0.35
HILL_LEVEL = 0.56
MOUNTAIN_LEVEL = 0.78

FACTION_LOADOUTS = {
    "Mongoli-heimo": ["cavalry", "cavalry", "infantry", "chief", "merchant"],              # paimentolaisheimo
    "Kiinan dynastia": ["infantry", "infantry", "cavalry", "chief", "merchant"],            # vuoristoheimo
    "Persialainen valtakunta": ["merchant", "cavalry", "infantry", "chief", "merchant"],    # kauppiasheimo
    "Venäläiset ruhtinaskunnat": ["infantry", "infantry", "cavalry", "chief", "merchant"],  # metsäheimo
}

FACTION_SYMBOLS = {
    "Mongoli-heimo": "🐺",
    "Kiinan dynastia": "🐉",
    "Persialainen valtakunta": "🦁",
    "Venäläiset ruhtinaskunnat": "🦅",
}

FACTION_ROLE_LABELS = {
    "Mongoli-heimo": "Paimentolaisheimo",
    "Kiinan dynastia": "Vuoristoheimo",
    "Persialainen valtakunta": "Kauppiasheimo",
    "Venäläiset ruhtinaskunnat": "Metsäheimo",
}

FACTION_ENVIRONMENT_RULES = {
    "Mongoli-heimo": {"required": {"plains"}, "preferred_adjacent": {"plains", "forest", "river"}},
    "Kiinan dynastia": {"required": {"plains", "forest", "mountain"}, "preferred_adjacent": {"mountain", "river"}},
    "Persialainen valtakunta": {"required": {"shore", "river"}, "preferred_adjacent": {"shore", "river", "plains"}},
    "Venäläiset ruhtinaskunnat": {"required": {"forest"}, "preferred_adjacent": {"forest", "plains", "river"}},
}

ASIA_SPAWN_PRESETS = {
    # Historiallisesti: Mongolian ylängöt / steppi
    "Mongoli-heimo": (16, 6),
    # Pohjois-Kiina / Keltainen joki -alue
    "Kiinan dynastia": (18, 9),
    # Iranin ylänkö / Persian ydinalue
    "Persialainen valtakunta": (9, 8),
    # Itä-Euroopan metsä- ja jokialueet
    "Venäläiset ruhtinaskunnat": (4, 4),
}

RIVAL_FACTION = "Kiinan dynastia"

game_state = {
    "board": None,
    "diplomacy": None,
    "player_faction": None,
    "turn": 0,
    "phase_index": 0,
    "focus": "Valloitus",
    "resources": {},
    "victory_progress": {"military": 0, "economic": 0, "cultural": 0, "technology": 0},
    "winner": None,
    "event_index": 0,
    "battle": {"last": None, "history": []},
    "factions_state": {},
    "map": {"width": BOARD_WIDTH, "height": BOARD_HEIGHT, "hexes": [], "rivers": [], "continents": []},
    "spawn_points": {},
    "next_unit_id": 1,
    "battle_event_id": 0,
    "selected_unit": None,
    "selected_hex": None,
    "reachable_hexes": [],
    "attackable_hexes": [],
    "controlled_hexes": {},
    "buildings": [],
    "cards": {"deck": [], "hand": [], "discard": [], "last_played": None},
    "effects": {},
    "phase_flags": {},
    "log": {"battle": [], "event": []},
    "universal_science_unlocked": False,
}


def _starting_resources(faction_name):
    base = {"horses": 3, "gold": 3, "food": 4, "artisans": 2}
    if faction_name == "Mongoli-heimo":
        base["horses"] += 2
    elif faction_name == "Kiinan dynastia":
        base["artisans"] += 2
        base["gold"] += 1
    elif faction_name == "Persialainen valtakunta":
        base["gold"] += 2
    elif faction_name == "Venäläiset ruhtinaskunnat":
        base["food"] += 2
        base["horses"] -= 1
    return base


def _ensure_victory_progress_keys():
    for key in ["military", "economic", "cultural", "technology"]:
        if key not in game_state["victory_progress"]:
            game_state["victory_progress"][key] = 0


def _init_card_state():
    deck = [dict(card) for card in CARD_LIBRARY]
    random.shuffle(deck)
    return {"deck": deck, "hand": [], "discard": [], "last_played": None}


def _init_effects():
    return {
        "ignore_river_penalty_turn": False,
        "mountain_move_discount_turn": False,
        "attack_bonus_3_turn": False,
        "cavalry_attack_bonus_2_turn": False,
        "infantry_defense_bonus_2_turn": False,
        "gold_per_turn_1_perm": False,
        "ai_attack_penalty_turn": False,
        "merchant_income_bonus_perm": False,
        "free_market_build_turn": False,
        "cavalry_attack_bonus_1_perm": False,
        "infantry_attack_bonus_1_perm": False,
        "fortress_defense_ignore_1_perm": False,
    }


def _reset_runtime_selection():
    game_state["selected_unit"] = None
    game_state["selected_hex"] = None
    game_state["reachable_hexes"] = []
    game_state["attackable_hexes"] = []


def _sync_victory_progress_keys():
    for key in VICTORY_GOALS.keys():
        if key not in game_state["victory_progress"]:
            game_state["victory_progress"][key] = 0


def _clear_turn_temporary_effects():
    for key in [
        "ignore_river_penalty_turn",
        "mountain_move_discount_turn",
        "attack_bonus_3_turn",
        "cavalry_attack_bonus_2_turn",
        "infantry_defense_bonus_2_turn",
        "ai_attack_penalty_turn",
    ]:
        game_state["effects"][key] = False


def _current_phase():
    return TURN_PHASES[game_state["phase_index"]]


def _action_labels(actions):
    return {action: ACTION_LABELS[action] for action in actions}


def _next_unit_id():
    value = game_state["next_unit_id"]
    game_state["next_unit_id"] += 1
    return value


def _axial_neighbors(col, row):
    even = row % 2 == 0
    if even:
        candidates = [(-1, -1), (0, -1), (-1, 0), (1, 0), (-1, 1), (0, 1)]
    else:
        candidates = [(0, -1), (1, -1), (-1, 0), (1, 0), (0, 1), (1, 1)]
    return [(col + dx, row + dy) for dx, dy in candidates]


def _within(col, row, width, height):
    return 0 <= col < width and 0 <= row < height


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def _normalize_field(field):
    low = min(min(row) for row in field)
    high = max(max(row) for row in field)
    span = max(0.0001, high - low)
    return [[(cell - low) / span for cell in row] for row in field]


def _smooth_field(field, passes=1):
    current = [row[:] for row in field]
    width = len(current[0])
    height = len(current)
    for _ in range(max(0, passes)):
        nxt = [[current[row][col] for col in range(width)] for row in range(height)]
        for row in range(height):
            for col in range(width):
                total = current[row][col] * 2.2
                weight = 2.2
                for nc, nr in _axial_neighbors(col, row):
                    if not _within(nc, nr, width, height):
                        continue
                    total += current[nr][nc]
                    weight += 1.0
                nxt[row][col] = total / weight
        current = nxt
    return current


def _distance_to_water(height_map, col, row, sea_level=SEA_LEVEL):
    width = len(height_map[0])
    height = len(height_map)
    best = width + height
    for rr in range(height):
        for cc in range(width):
            if height_map[rr][cc] <= sea_level:
                dist = abs(cc - col) + abs(rr - row)
                if dist < best:
                    best = dist
    return best


def _base_height(col, row, width, height):
    nx = (col / max(1, width - 1)) * 2 - 1
    ny = (row / max(1, height - 1)) * 2 - 1
    return (
        math.sin(col * 0.35) * 0.22
        + math.cos(row * 0.27) * 0.18
        + math.sin((col + row) * 0.17) * 0.16
        - (abs(nx) * 0.1 + abs(ny) * 0.1)
    )


def _paint_ellipse(field, cx, cy, rx, ry, delta):
    height = len(field)
    width = len(field[0])
    for row in range(height):
        for col in range(width):
            dx = (col - cx) / max(0.01, rx)
            dy = (row - cy) / max(0.01, ry)
            d2 = dx * dx + dy * dy
            if d2 <= 1.0:
                field[row][col] += delta * (1.0 - d2)


def _generate_continents(width, height):
    land_potential = [[_base_height(col, row, width, height) for col in range(width)] for row in range(height)]

    # Eurasian "old world" mass: Europe -> Middle East -> Central/East Asia
    old_world_masses = [
        (0.14, 0.18, 0.17, 0.14, 1.05),  # Europe
        (0.24, 0.30, 0.19, 0.17, 1.05),  # Balkans/Black Sea zone
        (0.37, 0.33, 0.22, 0.20, 1.18),  # Anatolia/Caucasus
        (0.50, 0.36, 0.24, 0.23, 1.20),  # Iran/Central Asia west
        (0.66, 0.36, 0.26, 0.23, 1.22),  # Central Asia
        (0.83, 0.36, 0.21, 0.20, 1.15),  # North China / Mongolia east
        (0.90, 0.46, 0.15, 0.16, 0.98),  # Korea / coastal east Asia
        (0.72, 0.52, 0.16, 0.16, 0.88),  # South China continuation
    ]
    for cx, cy, rx, ry, delta in old_world_masses:
        _paint_ellipse(land_potential, width * cx, height * cy, width * rx, height * ry, delta)

    # India peninsula + SE Asia
    _paint_ellipse(land_potential, width * 0.76, height * 0.63, width * 0.10, height * 0.14, 0.93)
    _paint_ellipse(land_potential, width * 0.89, height * 0.67, width * 0.10, height * 0.12, 0.80)

    # North Africa rim visible in south-west
    _paint_ellipse(land_potential, width * 0.22, height * 0.60, width * 0.24, height * 0.13, 0.92)

    # Sea basins: Mediterranean, Arabian Sea, Bay of Bengal, Pacific edge
    _paint_ellipse(land_potential, width * 0.28, height * 0.44, width * 0.11, height * 0.08, -0.78)  # Mediterranean
    _paint_ellipse(land_potential, width * 0.59, height * 0.56, width * 0.10, height * 0.11, -0.68)  # Arabian Sea
    _paint_ellipse(land_potential, width * 0.81, height * 0.58, width * 0.08, height * 0.10, -0.65)  # Bay of Bengal
    _paint_ellipse(land_potential, width * 0.95, height * 0.46, width * 0.10, height * 0.22, -0.92)  # Pacific side

    # Carve west/south oceans
    for row in range(height):
        for col in range(width):
            west_ocean = max(0.0, (0.14 - (col / max(1, width - 1))))
            south_ocean = max(0.0, ((row / max(1, height - 1)) - 0.82))
            coast_detail = (
                math.sin(col * 0.82 + row * 0.37) * 0.07
                + math.cos(col * 0.41 - row * 0.63) * 0.05
                + math.sin((col + row) * 0.53) * 0.03
            )
            land_potential[row][col] -= west_ocean * 1.3 + south_ocean * 1.0
            # Jagged coastlines instead of perfect ellipses.
            land_potential[row][col] += coast_detail * (0.5 + west_ocean * 0.6 + south_ocean * 0.5)

    land_potential = _normalize_field(land_potential)
    land_potential = _smooth_field(land_potential, passes=2)

    height_map = [[0.0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            # Multi-frequency relief to avoid monochrome/noisy single-step biome painting.
            relief = (
                math.sin(col * 0.54 + row * 0.22) * 0.16
                + math.cos(col * 0.19 - row * 0.45) * 0.14
                + math.sin((col + row) * 0.31) * 0.10
            )
            relief = 0.5 + relief
            macro = land_potential[row][col]
            combined = macro * 0.80 + relief * 0.20
            height_map[row][col] = _clamp(combined, 0.0, 1.0)
    return _smooth_field(height_map, passes=1)


def _add_mountain_chain(height_map, points, strength=0.52):
    height = len(height_map)
    width = len(height_map[0])
    for row in range(height):
        for col in range(width):
            best = 999.0
            for idx in range(len(points) - 1):
                x1, y1 = points[idx]
                x2, y2 = points[idx + 1]
                dx = x2 - x1
                dy = y2 - y1
                seg_len2 = dx * dx + dy * dy
                if seg_len2 == 0:
                    t = 0.0
                else:
                    t = max(0.0, min(1.0, ((col - x1) * dx + (row - y1) * dy) / seg_len2))
                proj_x = x1 + t * dx
                proj_y = y1 + t * dy
                dist = math.sqrt((col - proj_x) ** 2 + (row - proj_y) ** 2)
                if dist < best:
                    best = dist
            ridge = max(0.0, 1.0 - (best / 2.1))
            if ridge > 0:
                height_map[row][col] += ridge * strength


def _add_mountain_ranges(height_map, width, height):
    # Real-world inspired mountain systems
    caucasus_himalaya = [
        (width * 0.35, height * 0.30),
        (width * 0.45, height * 0.32),
        (width * 0.57, height * 0.34),
        (width * 0.69, height * 0.36),
        (width * 0.82, height * 0.40),
    ]
    ural = [
        (width * 0.33, height * 0.10),
        (width * 0.35, height * 0.20),
        (width * 0.37, height * 0.30),
        (width * 0.39, height * 0.42),
    ]
    tian_shan_altai = [
        (width * 0.58, height * 0.24),
        (width * 0.67, height * 0.24),
        (width * 0.76, height * 0.26),
    ]
    _add_mountain_chain(height_map, caucasus_himalaya, strength=0.26)
    _add_mountain_chain(height_map, ural, strength=0.18)
    _add_mountain_chain(height_map, tian_shan_altai, strength=0.20)
    for row in range(height):
        for col in range(width):
            ridge_noise = abs(math.sin(col * 0.42 + row * 0.26) * math.cos(col * 0.21 - row * 0.39))
            if ridge_noise > 0.72:
                height_map[row][col] += (ridge_noise - 0.72) * 0.12
            height_map[row][col] = _clamp(height_map[row][col], 0.0, 1.0)


def _trace_river(height_map, start_col, start_row, terrain):
    width = len(height_map[0])
    height = len(height_map)
    current = (start_col, start_row)
    path = []
    visited = set()
    for _ in range(width * height):
        col, row = current
        if not _within(col, row, width, height):
            break
        if (col, row) in visited:
            break
        visited.add((col, row))
        path.append((col, row))
        if terrain[row][col] in {"water", "shore"}:
            break
        neigh = [p for p in _axial_neighbors(col, row) if _within(p[0], p[1], width, height)]
        if not neigh:
            break
        neigh.sort(
            key=lambda p: (
                height_map[p[1]][p[0]]
                + (0.22 if terrain[p[1]][p[0]] == "mountain" else 0.0)
                + _distance_to_water(height_map, p[0], p[1]) * 0.03
            )
        )
        next_cell = neigh[0]
        if height_map[next_cell[1]][next_cell[0]] >= height_map[row][col]:
            # fallback: kohti lähintä merta
            best = min(
                neigh,
                key=lambda p: _distance_to_water(height_map, p[0], p[1]) + height_map[p[1]][p[0]] * 0.4,
            )
            next_cell = best
        current = next_cell
    return path


def _asia_river_sources(height_map, terrain, moisture_map):
    width = len(height_map[0])
    height = len(height_map)
    anchor_points = [
        (0.73, 0.37),  # Himalaya / Tibetan plateau
        (0.66, 0.33),  # Pamir/Tian Shan
        (0.56, 0.29),  # Central Asia
        (0.41, 0.28),  # Caucasus/Anatolia
        (0.32, 0.18),  # Ural foothills
    ]
    sources = []
    for ax, ay in anchor_points:
        cx = int(round(width * ax))
        cy = int(round(height * ay))
        best = None
        best_score = -999.0
        for row in range(max(0, cy - 2), min(height, cy + 3)):
            for col in range(max(0, cx - 2), min(width, cx + 3)):
                if terrain[row][col] in {"water", "shore", "lake"}:
                    continue
                h = height_map[row][col]
                m = moisture_map[row][col]
                score = h * 1.8 + m * 0.8 - _distance_to_water(height_map, col, row) * 0.03
                if score > best_score:
                    best_score = score
                    best = (col, row)
        if best:
            sources.append(best)
    return sources


def _carve_rivers(height_map, terrain, moisture_map):
    width = len(height_map[0])
    height = len(height_map)
    peaks = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if terrain[row][col] in {"mountain", "forest", "plains"} and height_map[row][col] > 0.68:
                peaks.append((col, row, height_map[row][col]))
    peaks.sort(key=lambda item: item[2], reverse=True)
    used = set()
    river_paths = []
    source_cells = _asia_river_sources(height_map, terrain, moisture_map)
    source_cells.extend((col, row) for col, row, _ in peaks[:4])
    for col, row in source_cells:
        path = _trace_river(height_map, col, row, terrain)
        if len(path) < 5:
            continue
        # joen täytyy päätyä mereen/rantaan
        end_col, end_row = path[-1]
        if terrain[end_row][end_col] not in {"water", "shore"}:
            continue
        fresh = [p for p in path if p not in used]
        if len(fresh) < 5:
            continue
        for c, r in path[:-1]:
            if terrain[r][c] in {"plains", "forest", "desert", "mountain"}:
                terrain[r][c] = "river"
                used.add((c, r))
        river_paths.append(path)
        if len(river_paths) >= 7:
            break
    return river_paths


def _coastline_pass(terrain):
    width = len(terrain[0])
    height = len(terrain)
    for row in range(height):
        for col in range(width):
            if terrain[row][col] != "water":
                continue
            for nc, nr in _axial_neighbors(col, row):
                if _within(nc, nr, width, height) and terrain[nr][nc] not in {"water", "shore"}:
                    terrain[row][col] = "shore"
                    break


def _lake_pass(height_map, terrain, moisture_map, river_paths):
    width = len(terrain[0])
    height = len(terrain)
    river_cells = {(c, r) for path in river_paths for c, r in path}
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if terrain[row][col] in {"water", "shore", "river"}:
                continue
            if not (COAST_LEVEL + 0.03 <= height_map[row][col] <= 0.62):
                continue
            if moisture_map[row][col] < 0.60:
                continue
            neigh_coords = [(nc, nr) for nc, nr in _axial_neighbors(col, row) if _within(nc, nr, width, height)]
            neigh_heights = [height_map[nr][nc] for nc, nr in neigh_coords]
            local_basin = sum(1 for h in neigh_heights if h >= height_map[row][col] + 0.02) >= 3
            receives_flow = any((nc, nr) in river_cells for nc, nr in neigh_coords)
            if local_basin and (receives_flow or moisture_map[row][col] > 0.73):
                terrain[row][col] = "lake"


def _generate_temperature_map(height_map):
    width = len(height_map[0])
    height = len(height_map)
    temperature = [[0.0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        lat = row / max(1, height - 1)
        # Warm belt lower-mid map (India / south China), colder north.
        lat_heat = 1.0 - abs((lat - 0.62) * 1.55)
        for col in range(width):
            noise = (
                math.sin(col * 0.22 + row * 0.19) * 0.09
                + math.cos(col * 0.11 - row * 0.28) * 0.06
            )
            altitude_cooling = height_map[row][col] * 0.42
            temperature[row][col] = _clamp(lat_heat + noise - altitude_cooling, 0.0, 1.0)
    return _smooth_field(temperature, passes=2)


def _generate_moisture_map(height_map):
    width = len(height_map[0])
    height = len(height_map)
    moisture = [[0.0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            sea_dist = _distance_to_water(height_map, col, row)
            sea_influence = _clamp(1.0 - sea_dist / 8.0, 0.0, 1.0) * 0.33
            noise = (
                math.sin(col * 0.31 - row * 0.17) * 0.17
                + math.cos(col * 0.15 + row * 0.37) * 0.12
            )
            # Central Asian arid belt.
            arid_core = math.exp(
                -(((col - width * 0.66) ** 2) / (width * 0.32) + ((row - height * 0.34) ** 2) / (height * 0.26))
            )
            mountain_lift = 0.10 if height_map[row][col] >= HILL_LEVEL else 0.0
            moisture[row][col] = _clamp(0.44 + sea_influence + noise + mountain_lift - arid_core * 0.36, 0.0, 1.0)
    return _smooth_field(moisture, passes=2)


def _denoise_land_biomes(terrain):
    width = len(terrain[0])
    height = len(terrain)
    updated = [row[:] for row in terrain]
    mutable = {"plains", "forest", "desert"}
    for row in range(height):
        for col in range(width):
            current = terrain[row][col]
            if current not in mutable:
                continue
            neigh = [terrain[nr][nc] for nc, nr in _axial_neighbors(col, row) if _within(nc, nr, width, height)]
            similar = sum(1 for t in neigh if t == current)
            if similar >= 2:
                continue
            counts = {}
            for t in neigh:
                if t in mutable:
                    counts[t] = counts.get(t, 0) + 1
            if counts:
                dominant, amount = max(counts.items(), key=lambda item: item[1])
                if amount >= 3:
                    updated[row][col] = dominant
    return updated


def _assign_biomes(height_map, temperature_map, moisture_map):
    width = len(height_map[0])
    height = len(height_map)
    terrain = [["water" for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            h = height_map[row][col]
            temp = temperature_map[row][col]
            moist = moisture_map[row][col]
            inland = _distance_to_water(height_map, col, row)

            if h < SEA_LEVEL:
                terrain[row][col] = "water"
            elif h < COAST_LEVEL:
                terrain[row][col] = "shore"
            elif h >= MOUNTAIN_LEVEL:
                terrain[row][col] = "mountain"
            elif temp > 0.54 and moist < 0.30 and inland > 3:
                terrain[row][col] = "desert"
            elif moist > 0.56:
                terrain[row][col] = "forest"
            else:
                terrain[row][col] = "plains"

    _coastline_pass(terrain)
    river_paths = _carve_rivers(height_map, terrain, moisture_map)
    _lake_pass(height_map, terrain, moisture_map, river_paths)
    terrain = _denoise_land_biomes(terrain)
    return terrain, river_paths


def _continent_clusters(terrain):
    width = len(terrain[0])
    height = len(terrain)
    land = {"plains", "forest", "mountain", "desert", "river", "lake"}
    visited = set()
    continents = []
    for row in range(height):
        for col in range(width):
            if (col, row) in visited or terrain[row][col] not in land:
                continue
            stack = [(col, row)]
            cells = []
            visited.add((col, row))
            while stack:
                cc, rr = stack.pop()
                cells.append((cc, rr))
                for nc, nr in _axial_neighbors(cc, rr):
                    if not _within(nc, nr, width, height):
                        continue
                    if (nc, nr) in visited:
                        continue
                    if terrain[nr][nc] not in land:
                        continue
                    visited.add((nc, nr))
                    stack.append((nc, nr))
            if cells:
                cx = round(sum(c for c, _ in cells) / len(cells), 2)
                cy = round(sum(r for _, r in cells) / len(cells), 2)
                continents.append({"size": len(cells), "centroid": {"x": cx, "y": cy}})
    continents.sort(key=lambda c: c["size"], reverse=True)
    for idx, continent in enumerate(continents, start=1):
        continent["id"] = idx
    return continents


def _elevation_band(elevation):
    if elevation >= 0.72:
        return "high"
    if elevation >= HILL_LEVEL:
        return "mid"
    if elevation >= COAST_LEVEL:
        return "low"
    return "sea"


def _terrain_role(terrain):
    if terrain in {"water", "lake"}:
        return "waterbody"
    if terrain in {"shore", "river"}:
        return "hydrology"
    if terrain == "mountain":
        return "highland"
    if terrain == "forest":
        return "woodland"
    if terrain == "desert":
        return "arid"
    return "land"


def _init_hex_map(width, height):
    height_map = _generate_continents(width, height)
    _add_mountain_ranges(height_map, width, height)
    height_map = _smooth_field(_normalize_field(height_map), passes=1)
    temperature_map = _generate_temperature_map(height_map)
    moisture_map = _generate_moisture_map(height_map)
    terrain, river_paths = _assign_biomes(height_map, temperature_map, moisture_map)
    continents = _continent_clusters(terrain)

    hexes = []
    for row in range(height):
        line = []
        for col in range(width):
            q = col - (row // 2)
            r = row
            terrain_key = terrain[row][col]
            line.append(
                {
                    "col": col,
                    "row": row,
                    "q": q,
                    "r": r,
                    "cube_x": q,
                    "cube_z": r,
                    "cube_y": -q - r,
                    "elevation": round(height_map[row][col], 3),
                    "terrain": terrain_key if terrain_key in TERRAIN_TYPES else "plains",
                }
            )
        hexes.append(line)
    return {
        "width": width,
        "height": height,
        "hexes": hexes,
        "rivers": [[{"x": c, "y": r} for c, r in path] for path in river_paths],
        "continents": continents[:6],
    }


def _cell_terrain(col, row):
    return game_state["map"]["hexes"][row][col]["terrain"]


def _score_spawn(col, row, required, preferred_adjacent):
    terrain = _cell_terrain(col, row)
    score = 0.0
    if terrain in required:
        score += 2.0
    if terrain in {"plains", "forest", "shore", "river"}:
        score += 1.0

    neighbors = [(c, r) for c, r in _axial_neighbors(col, row) if _within(c, r, BOARD_WIDTH, BOARD_HEIGHT)]
    for nc, nr in neighbors:
        n_terrain = _cell_terrain(nc, nr)
        if n_terrain in preferred_adjacent:
            score += 0.6
        if n_terrain == terrain:
            score += 0.2
        if n_terrain in {"water", "shore"} and terrain in {"shore", "river", "plains"}:
            score += 0.15
    return score


def _terrain_walkable(col, row):
    return _cell_terrain(col, row) not in {"water", "lake"}


def _generate_spawn_points():
    spawn_points = {}
    used = set()
    for faction_name in [f["name"] for f in factions]:
        rule = FACTION_ENVIRONMENT_RULES[faction_name]
        required = rule["required"]
        preferred_adjacent = rule["preferred_adjacent"]
        candidates = []
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                if not _terrain_walkable(col, row):
                    continue
                if (col, row) in used:
                    continue
                terrain = _cell_terrain(col, row)
                if terrain not in required and terrain not in {"plains", "forest", "shore", "river", "mountain"}:
                    continue
                score = _score_spawn(col, row, required, preferred_adjacent)
                candidates.append((score, col, row))
        candidates.sort(reverse=True)

        # Prefer historical preset region if compatible.
        preset = ASIA_SPAWN_PRESETS.get(faction_name)
        if preset and _within(preset[0], preset[1], BOARD_WIDTH, BOARD_HEIGHT):
            pcol, prow = preset
            if _terrain_walkable(pcol, prow):
                preset_score = _score_spawn(pcol, prow, required, preferred_adjacent)
                if preset_score >= 1.0:
                    center = (pcol, prow)
                else:
                    center = None
            else:
                center = None
        else:
            center = None

        if not candidates:
            fallback = (BOARD_WIDTH // 2, BOARD_HEIGHT // 2)
            spawn_points[faction_name] = [fallback]
            used.add(fallback)
            continue

        if center is None:
            center = (candidates[0][1], candidates[0][2])
        points = [center]
        used.add(center)

        # etsi lisäspawnit lähiympäristöstä
        frontier = [center]
        seen = {center}
        while frontier and len(points) < len(FACTION_LOADOUTS[faction_name]):
            col, row = frontier.pop(0)
            for nc, nr in _axial_neighbors(col, row):
                if not _within(nc, nr, BOARD_WIDTH, BOARD_HEIGHT):
                    continue
                if (nc, nr) in seen:
                    continue
                seen.add((nc, nr))
                if (nc, nr) in used:
                    continue
                if not _terrain_walkable(nc, nr):
                    continue
                # pidä spawnit heimon ympäristöön sopivina
                if _score_spawn(nc, nr, required, preferred_adjacent) < 1.2:
                    frontier.append((nc, nr))
                    continue
                points.append((nc, nr))
                used.add((nc, nr))
                if len(points) >= len(FACTION_LOADOUTS[faction_name]):
                    break
                frontier.append((nc, nr))

        # viimeistele jos paikalliset ruudut eivät riittäneet
        if len(points) < len(FACTION_LOADOUTS[faction_name]):
            for _, col, row in candidates[1:]:
                if (col, row) in used:
                    continue
                points.append((col, row))
                used.add((col, row))
                if len(points) >= len(FACTION_LOADOUTS[faction_name]):
                    break

        spawn_points[faction_name] = points
    return spawn_points


def _create_unit(faction_name, unit_key, side):
    base = UNIT_TYPES[unit_key]
    return {
        "id": _next_unit_id(),
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
        spawn = game_state["spawn_points"][name][0]
        faction_state[name] = {
            "name": name,
            "color": faction.get("color", "gray"),
            "symbol": FACTION_SYMBOLS.get(name, "🏳️"),
            "spawn_role": FACTION_ROLE_LABELS.get(name, "Heimo"),
            "is_player": name == player_faction_name,
            "unit_counts": unit_counts,
            "total_units": len(loadout),
            "spawn_position": {"x": spawn[0], "y": spawn[1]},
            "units": [],
        }
    return faction_state


def _serialize_factions_state():
    return [game_state["factions_state"].get(faction["name"]) for faction in factions]


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
                        "id": unit["id"],
                        "faction": unit["faction"],
                        "type": unit["type"],
                        "unit_key": unit["unit_key"],
                        "token": unit["token"],
                        "hp": unit["hp"],
                        "max_hp": unit["max_hp"],
                        "side": unit["side"],
                        "strength": unit["strength"],
                        "defense": unit["defense"],
                    }
                )
            else:
                row.append(None)
        board_data.append(row)
    return board_data


def _recount_faction_units():
    fresh_counts = {name: {unit_key: 0 for unit_key in UNIT_TYPES.keys()} for name in _all_faction_names()}
    faction_units = {name: [] for name in _all_faction_names()}
    board = game_state["board"]
    for y in range(board.height):
        for x in range(board.width):
            unit = board.board[y][x]
            if not unit:
                continue
            fresh_counts[unit["faction"]][unit["unit_key"]] += 1
            faction_units[unit["faction"]].append(
                {
                    "id": unit["id"],
                    "x": x,
                    "y": y,
                    "unit_key": unit["unit_key"],
                    "type": unit["type"],
                    "token": unit["token"],
                    "hp": unit["hp"],
                    "max_hp": unit["max_hp"],
                    "strength": unit["strength"],
                    "defense": unit["defense"],
                    "side": unit["side"],
                }
            )
    for faction_name, state in game_state["factions_state"].items():
        counts = fresh_counts[faction_name]
        state["unit_counts"] = counts
        state["total_units"] = sum(counts.values())
        state["units"] = faction_units[faction_name]


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
        spawn_points = game_state["spawn_points"][faction_name]
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
    return min(enemies, key=lambda entry: abs(entry[0] - attacker_x) + abs(entry[1] - attacker_y))


def _record_battle(report):
    game_state["battle"]["last"] = report
    game_state["battle"]["history"].insert(0, report)
    game_state["battle"]["history"] = game_state["battle"]["history"][:8]


def _serialize_battle():
    battle = game_state.get("battle") or {"last": None, "history": []}
    last = battle.get("last")
    payload = {"history": battle.get("history", []), "last": last}
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
                "battle_positions": last.get("battle_positions"),
                "event_id": last.get("event_id"),
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
    game_state["battle_event_id"] += 1
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
        "event_id": game_state["battle_event_id"],
        "battle_positions": {"attacker": {"x": attacker_x, "y": attacker_y}, "defender": {"x": defender_x, "y": defender_y}},
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
    return f"Taistelu: hyökkäysnoppa {attack_die}, puolustusnoppa {defense_die}. Tulos: {result['outcome']}."


def _serialize_hexes():
    board = game_state["board"]
    if not board:
        return []
    hexes = []
    for row in range(game_state["map"]["height"]):
        line = []
        for col in range(game_state["map"]["width"]):
            base_hex = game_state["map"]["hexes"][row][col]
            unit = board.board[row][col] if row < board.height and col < board.width else None
            faction_marker = None
            for faction_name, points in game_state["spawn_points"].items():
                if points and points[0] == (col, row):
                    faction_marker = {
                        "name": faction_name,
                        "short": faction_name.split(" ")[0][0],
                        "symbol": FACTION_SYMBOLS.get(faction_name, "🏳️"),
                    }
                    break

            units = []
            if unit:
                units.append(_serialize_unit_for_hex(unit, col, row))

            highlight = None
            last = game_state["battle"].get("last")
            if last:
                apos = last["battle_positions"]["attacker"]
                dpos = last["battle_positions"]["defender"]
                if apos["x"] == col and apos["y"] == row:
                    highlight = "attacker"
                elif dpos["x"] == col and dpos["y"] == row:
                    highlight = "defender"

            line.append(
                {
                    "col": col,
                    "row": row,
                    "q": base_hex["q"],
                    "r": base_hex["r"],
                    "elevation": base_hex["elevation"],
                    "terrain": base_hex["terrain"],
                    "shoreline": base_hex["terrain"] in {"shore", "water"} or any(
                        _within(nc, nr, game_state["map"]["width"], game_state["map"]["height"])
                        and game_state["map"]["hexes"][nr][nc]["terrain"] in {"shore", "water"}
                        for nc, nr in _axial_neighbors(col, row)
                    ),
                    "elevation_band": (
                        "highland"
                        if base_hex["elevation"] >= 1.25
                        else "upland"
                        if base_hex["elevation"] >= 0.78
                        else "lowland"
                        if base_hex["elevation"] >= 0.22
                        else "coast"
                        if base_hex["elevation"] >= -0.02
                        else "sea"
                    ),
                    "terrain_role": (
                        "high_peak"
                        if base_hex["terrain"] == "mountain"
                        else "inland_river"
                        if base_hex["terrain"] == "river"
                        else "coastal_water"
                        if base_hex["terrain"] in {"shore", "water"}
                        else "fertile_plain"
                        if base_hex["terrain"] == "plains"
                        else "woodland"
                        if base_hex["terrain"] == "forest"
                        else "arid_zone"
                        if base_hex["terrain"] == "desert"
                        else "lake_basin"
                        if base_hex["terrain"] == "lake"
                        else "land"
                    ),
                    "faction_marker": faction_marker,
                    "units": units,
                    "highlight": highlight,
                }
            )
        hexes.append(line)
    return hexes


def _serialize_unit_for_hex(unit, x, y):
    if not unit:
        return None
    role = "Perusyksikkö"
    move = 2
    if unit["unit_key"] == "cavalry":
        role = "Nopea hyökkäys, vahva tasangolla"
        move = 3
    elif unit["unit_key"] == "infantry":
        role = "Kestävä puolustaja"
        move = 2
    elif unit["unit_key"] == "chief":
        role = "Johtajayksikkö, menettäminen kriittinen"
        move = 2
    elif unit["unit_key"] == "merchant":
        role = "Heikko taistelussa, vahva taloudessa"
        move = 2
    return {
        "id": unit["id"],
        "faction": unit["faction"],
        "unit_key": unit["unit_key"],
        "type": unit["type"],
        "token": unit["token"],
        "hp": unit["hp"],
        "max_hp": unit["max_hp"],
        "strength": unit["strength"],
        "defense": unit["defense"],
        "side": unit["side"],
        "move": move,
        "role": role,
        "owner": unit["faction"],
        "location": {"x": x, "y": y},
    }


def _phase_default_action_done(phase):
    if phase == "Resurssivaihe":
        return bool(game_state["phase_flags"].get("resource_collected"))
    return False


def _control_owner_for_hex(col, row):
    board = game_state["board"]
    unit = board.board[row][col]
    if unit:
        return unit["faction"]
    for building in game_state.get("buildings", []):
        if building["x"] == col and building["y"] == row and building["type"] == "camp":
            return building["faction"]
    return None


def _refresh_controlled_hexes():
    control = {}
    for row in range(BOARD_HEIGHT):
        for col in range(BOARD_WIDTH):
            owner = _control_owner_for_hex(col, row)
            if owner:
                control[f"{col},{row}"] = owner
    game_state["controlled_hexes"] = control


def _unit_move_points(unit):
    if unit["unit_key"] == "cavalry":
        return 3
    return 2


def _reachable_cells(start_x, start_y, unit):
    board = game_state["board"]
    max_steps = _unit_move_points(unit)
    seen = {(start_x, start_y): 0}
    queue = [(start_x, start_y, 0)]
    reach = []
    while queue:
        cx, cy, steps = queue.pop(0)
        for nx, ny in _axial_neighbors(cx, cy):
            if not _within(nx, ny, board.width, board.height):
                continue
            if _cell_terrain(nx, ny) in {"water", "lake"}:
                continue
            cost = 1
            if _cell_terrain(nx, ny) == "mountain" and not game_state["effects"].get("mountain_move_discount_turn"):
                cost = 2
            next_steps = steps + cost
            if next_steps > max_steps:
                continue
            occupant = board.board[ny][nx]
            if occupant and occupant["faction"] != unit["faction"]:
                continue
            if (nx, ny) in seen and seen[(nx, ny)] <= next_steps:
                continue
            seen[(nx, ny)] = next_steps
            queue.append((nx, ny, next_steps))
            if not occupant:
                reach.append((nx, ny))
    return reach


def _attackable_cells(start_x, start_y, unit):
    board = game_state["board"]
    cells = []
    for nx, ny in _axial_neighbors(start_x, start_y):
        if not _within(nx, ny, board.width, board.height):
            continue
        occupant = board.board[ny][nx]
        if occupant and occupant["faction"] != unit["faction"]:
            cells.append((nx, ny))
    return cells


def _select_unit(col, row):
    board = game_state["board"]
    unit = board.board[row][col]
    if not unit:
        return "Hexissä ei ole yksikköä."
    if unit["faction"] != game_state["player_faction"]["name"]:
        return "Voit valita vain oman heimon yksikön."
    game_state["selected_unit"] = {"x": col, "y": row, "id": unit["id"]}
    game_state["selected_hex"] = {"x": col, "y": row}
    game_state["reachable_hexes"] = [{"x": x, "y": y} for x, y in _reachable_cells(col, row, unit)]
    game_state["attackable_hexes"] = [{"x": x, "y": y} for x, y in _attackable_cells(col, row, unit)]
    return f"Valittu yksikkö: {unit['type']} ({col},{row})."


def _execute_move(target_x, target_y):
    selected = game_state.get("selected_unit")
    if not selected:
        return "Valitse ensin yksikkö."
    sx, sy = selected["x"], selected["y"]
    board = game_state["board"]
    unit = board.board[sy][sx]
    if not unit:
        return "Valittu yksikkö puuttuu."
    legal = {(entry["x"], entry["y"]) for entry in game_state.get("reachable_hexes", [])}
    if (target_x, target_y) not in legal:
        return "Laiton liike: kohde ei ole sallittu."
    if board.board[target_y][target_x] is not None:
        return "Kohdeheksi on varattu."
    board.board[target_y][target_x] = unit
    board.board[sy][sx] = None
    _recount_faction_units()
    _refresh_controlled_hexes()
    game_state["selected_unit"] = {"x": target_x, "y": target_y, "id": unit["id"]}
    game_state["selected_hex"] = {"x": target_x, "y": target_y}
    game_state["reachable_hexes"] = [{"x": x, "y": y} for x, y in _reachable_cells(target_x, target_y, unit)]
    game_state["attackable_hexes"] = [{"x": x, "y": y} for x, y in _attackable_cells(target_x, target_y, unit)]
    return f"{unit['type']} liikkui heksiin ({target_x},{target_y})."


def _defense_bonus_at(col, row):
    bonus = 0
    terrain = _cell_terrain(col, row)
    if terrain in {"forest", "mountain"}:
        bonus += 1
    for building in game_state.get("buildings", []):
        if building["x"] == col and building["y"] == row and building["type"] == "fortress":
            bonus += 2
    return bonus


def _resolve_targeted_attack(attacker_x, attacker_y, defender_x, defender_y):
    board = game_state["board"]
    attacker = board.board[attacker_y][attacker_x]
    defender = board.board[defender_y][defender_x]
    if not attacker or not defender:
        return "Taistelu epäonnistui: yksiköt puuttuvat."
    if defender["faction"] == attacker["faction"]:
        return "Et voi hyökätä omaan yksikköön."

    attack_bonus = 0
    defense_bonus = _defense_bonus_at(defender_x, defender_y)
    if game_state["effects"].get("attack_bonus_3_turn"):
        attack_bonus += 3
        game_state["effects"]["attack_bonus_3_turn"] = False
    if game_state["effects"].get("cavalry_attack_bonus_2_turn") and attacker["unit_key"] == "cavalry":
        attack_bonus += 2
    if game_state["effects"].get("cavalry_attack_bonus_1_perm") and attacker["unit_key"] == "cavalry":
        attack_bonus += 1
    if game_state["effects"].get("infantry_attack_bonus_1_perm") and attacker["unit_key"] == "infantry":
        attack_bonus += 1
    if game_state["effects"].get("fortress_defense_ignore_1_perm") and defense_bonus > 0:
        defense_bonus = max(0, defense_bonus - 1)
    if game_state["effects"].get("infantry_defense_bonus_2_turn") and defender["unit_key"] == "infantry":
        defense_bonus += 2
    if _cell_terrain(attacker_x, attacker_y) == "plains" and attacker["unit_key"] == "cavalry":
        attack_bonus += 1

    attack_die = random.randint(1, 6)
    defense_die = random.randint(1, 6)
    attack_total = attacker["strength"] + attack_bonus + attack_die
    defense_total = defender["defense"] + defense_bonus + defense_die
    game_state["battle_event_id"] += 1
    report = {
        "attacker_faction": attacker["faction"],
        "defender_faction": defender["faction"],
        "attacker_unit": attacker["type"],
        "defender_unit": defender["type"],
        "attack_die": attack_die,
        "defense_die": defense_die,
        "attack_total": attack_total,
        "defense_total": defense_total,
        "attack_modifier": attack_bonus,
        "defense_modifier": defense_bonus,
        "terrain_bonus_defender": _defense_bonus_at(defender_x, defender_y),
        "damage_to_defender": 0,
        "damage_to_attacker": 0,
        "outcome": "torjunta",
        "event_id": game_state["battle_event_id"],
        "battle_positions": {"attacker": {"x": attacker_x, "y": attacker_y}, "defender": {"x": defender_x, "y": defender_y}},
    }
    if attack_total > defense_total:
        damage = max(1, attack_total - defense_total)
        defender["hp"] -= damage
        report["damage_to_defender"] = damage
        report["outcome"] = "osuma"
        game_state["victory_progress"]["military"] += 1
        if defender["hp"] <= 0:
            board.board[defender_y][defender_x] = None
            report["outcome"] = "yksikkö tuhottu"
            game_state["victory_progress"]["military"] += 2
    else:
        retaliation = max(0, defense_total - attack_total)
        if retaliation > 0:
            attacker["hp"] -= retaliation
            report["damage_to_attacker"] = retaliation
            if attacker["hp"] <= 0:
                board.board[attacker_y][attacker_x] = None
                report["outcome"] = "hyökkääjä kaatui"
    _record_battle(report)
    game_state["log"]["battle"].insert(0, report)
    game_state["log"]["battle"] = game_state["log"]["battle"][:16]
    _recount_faction_units()
    _refresh_controlled_hexes()
    if _cell_terrain(attacker_x, attacker_y) == "river":
        game_state["effects"]["ignore_river_penalty_turn"] = False
    return f"Taistelu: {report['outcome']} (ATK {attack_total} vs DEF {defense_total})."


def _resolve_hex_click(col, row):
    board = game_state["board"]
    if not _within(col, row, board.width, board.height):
        return "Klikattu heksi on kartan ulkopuolella."
    phase = _current_phase()
    game_state["selected_hex"] = {"x": col, "y": row}
    unit = board.board[row][col]
    if unit and unit["faction"] == game_state["player_faction"]["name"]:
        return _select_unit(col, row)
    if phase == "Liikevaihe":
        return _execute_move(col, row)
    if phase == "Taisteluvaihe":
        selected = game_state.get("selected_unit")
        if not selected:
            return "Valitse ensin hyökkäävä yksikkö."
        return _resolve_targeted_attack(selected["x"], selected["y"], col, row)
    return "Heksi valittu."


def _draw_cards_for_player(count=1):
    drawn = []
    for _ in range(count):
        if not game_state["cards"]["deck"]:
            game_state["cards"]["deck"] = game_state["cards"]["discard"][:]
            random.shuffle(game_state["cards"]["deck"])
            game_state["cards"]["discard"] = []
        if not game_state["cards"]["deck"]:
            break
        card = game_state["cards"]["deck"].pop()
        game_state["cards"]["hand"].append(card)
        drawn.append(card["name"])
    return drawn


def _can_afford(cost):
    for key, val in cost.items():
        if game_state["resources"].get(key, 0) < val:
            return False
    return True


def _pay_cost(cost):
    for key, val in cost.items():
        game_state["resources"][key] -= val


def _apply_card_effect(card):
    effect = card["effect"]
    if effect == "ignore_river_penalty_turn":
        game_state["effects"]["ignore_river_penalty_turn"] = True
    elif effect == "mountain_move_discount_turn":
        game_state["effects"]["mountain_move_discount_turn"] = True
    elif effect == "attack_bonus_3_turn":
        game_state["effects"]["attack_bonus_3_turn"] = True
    elif effect == "cavalry_attack_bonus_2_turn":
        game_state["effects"]["cavalry_attack_bonus_2_turn"] = True
    elif effect == "infantry_defense_bonus_2_turn":
        game_state["effects"]["infantry_defense_bonus_2_turn"] = True
    elif effect == "gold_per_turn_1_perm":
        game_state["effects"]["gold_per_turn_1_perm"] = True
    elif effect == "ai_attack_penalty_turn":
        game_state["effects"]["ai_attack_penalty_turn"] = True
    elif effect == "merchant_income_bonus_perm":
        game_state["effects"]["merchant_income_bonus_perm"] = True
    elif effect == "diplomacy_points_1":
        game_state["victory_progress"]["economic"] += 1
        game_state["victory_progress"]["technology"] += 1
    elif effect == "free_market_build_turn":
        game_state["effects"]["free_market_build_turn"] = True
    elif effect == "cavalry_attack_bonus_1_perm":
        game_state["effects"]["cavalry_attack_bonus_1_perm"] = True
    elif effect == "infantry_attack_bonus_1_perm":
        game_state["effects"]["infantry_attack_bonus_1_perm"] = True
    elif effect == "fortress_defense_ignore_1_perm":
        game_state["effects"]["fortress_defense_ignore_1_perm"] = True
    elif effect == "tech_progress_1":
        game_state["victory_progress"]["technology"] += 1
    elif effect == "universal_science":
        game_state["universal_science_unlocked"] = True
    elif effect == "gain_food_2":
        game_state["resources"]["food"] += 2
    elif effect == "gain_horses_2":
        game_state["resources"]["horses"] += 2
    elif effect == "gain_gold_3":
        game_state["resources"]["gold"] += 3
    elif effect == "gain_artisans_2":
        game_state["resources"]["artisans"] += 2
    elif effect == "gain_mixed_2":
        game_state["resources"]["gold"] += 1
        game_state["resources"]["food"] += 1


def _play_card(card_id):
    hand = game_state["cards"]["hand"]
    card = next((c for c in hand if c["id"] == card_id), None)
    if not card:
        return "Korttia ei löytynyt kädestä."
    if not _can_afford(card.get("cost", {})):
        return "Kortin pelaaminen epäonnistui: resurssit eivät riitä."
    _pay_cost(card.get("cost", {}))
    _apply_card_effect(card)
    hand.remove(card)
    game_state["cards"]["discard"].append(card)
    game_state["cards"]["last_played"] = card
    game_state["log"]["event"].insert(0, {"type": "card", "name": card["name"], "desc": card["desc"]})
    game_state["log"]["event"] = game_state["log"]["event"][:20]
    return f"Kortti pelattu: {card['name']}."


def _collect_income(faction_name):
    control_count = sum(1 for owner in game_state["controlled_hexes"].values() if owner == faction_name)
    food = max(1, control_count // 6)
    gold = max(1, control_count // 7)
    horses = max(0, control_count // 10)
    artisans = max(1, control_count // 9)
    if game_state["effects"].get("gold_per_turn_1_perm"):
        gold += 1
    merchant_units = len([u for _, _, u in _list_units(faction_name=faction_name) if u["unit_key"] == "merchant"])
    if merchant_units:
        gold += merchant_units
        if game_state["effects"].get("merchant_income_bonus_perm"):
            gold += merchant_units
    game_state["resources"]["food"] += food
    game_state["resources"]["gold"] += gold
    game_state["resources"]["horses"] += horses
    game_state["resources"]["artisans"] += artisans
    return {"food": food, "gold": gold, "horses": horses, "artisans": artisans}


def _selected_or_spawn_hex():
    if game_state.get("selected_hex"):
        return game_state["selected_hex"]["x"], game_state["selected_hex"]["y"]
    player = game_state["player_faction"]["name"]
    pos = game_state["factions_state"][player]["spawn_position"]
    return pos["x"], pos["y"]


def _build_structure(structure_type):
    col, row = _selected_or_spawn_hex()
    owner = _control_owner_for_hex(col, row)
    player = game_state["player_faction"]["name"]
    if owner != player:
        return "Rakennus vaatii pelaajan hallitsemalle heksille."
    for building in game_state["buildings"]:
        if building["x"] == col and building["y"] == row and building["type"] == structure_type:
            return "Rakennus on jo tässä heksissä."
    cost = BUILDING_COSTS[structure_type].copy()
    if structure_type == "market" and game_state["effects"].get("free_market_build_turn"):
        cost["gold"] = 0
        game_state["effects"]["free_market_build_turn"] = False
    if not _can_afford(cost):
        return "Rakennuksen rakentaminen epäonnistui: resurssit eivät riitä."
    _pay_cost(cost)
    game_state["buildings"].append({"type": structure_type, "faction": player, "x": col, "y": row})
    game_state["log"]["event"].insert(0, {"type": "build", "name": BUILDING_LABELS[structure_type], "x": col, "y": row})
    game_state["log"]["event"] = game_state["log"]["event"][:20]
    _refresh_controlled_hexes()
    return f"Rakennettu: {BUILDING_LABELS[structure_type]} ({col},{row})."


def _recruit_unit(unit_key):
    cost = UNIT_RECRUIT_COSTS[unit_key]
    if not _can_afford(cost):
        return "Rekrytointi epäonnistui: resurssit eivät riitä."
    player = game_state["player_faction"]["name"]
    spawn = game_state["factions_state"][player]["spawn_position"]
    board = game_state["board"]
    candidates = [(spawn["x"], spawn["y"])]
    candidates.extend(_axial_neighbors(spawn["x"], spawn["y"]))
    target = None
    for x, y in candidates:
        if not _within(x, y, board.width, board.height):
            continue
        if _cell_terrain(x, y) in {"water", "lake"}:
            continue
        if board.board[y][x] is None:
            target = (x, y)
            break
    if not target:
        return "Rekrytointi epäonnistui: spawn-alue täynnä."
    _pay_cost(cost)
    board.board[target[1]][target[0]] = _create_unit(player, unit_key, "player")
    _recount_faction_units()
    _refresh_controlled_hexes()
    return f"Rekrytoitu {UNIT_TYPES[unit_key]['label']} heksiin ({target[0]},{target[1]})."


def _run_simple_ai_turn():
    player = game_state["player_faction"]["name"]
    ai_factions = [name for name in _all_faction_names() if name != player]
    board = game_state["board"]
    for faction_name in ai_factions:
        ai_units = _list_units(faction_name=faction_name)
        random.shuffle(ai_units)
        # attack if adjacent weak enemy
        for x, y, unit in ai_units:
            targets = []
            for nx, ny in _axial_neighbors(x, y):
                if not _within(nx, ny, board.width, board.height):
                    continue
                enemy = board.board[ny][nx]
                if enemy and enemy["faction"] == player:
                    targets.append((nx, ny, enemy["hp"]))
            if targets:
                targets.sort(key=lambda t: t[2])
                _resolve_targeted_attack(x, y, targets[0][0], targets[0][1])
                return
        # else move toward player spawn
        player_spawn = game_state["factions_state"][player]["spawn_position"]
        for x, y, unit in ai_units:
            best = None
            for nx, ny in _axial_neighbors(x, y):
                if not _within(nx, ny, board.width, board.height):
                    continue
                if _cell_terrain(nx, ny) in {"water", "lake"}:
                    continue
                if board.board[ny][nx] is not None:
                    continue
                score = abs(nx - player_spawn["x"]) + abs(ny - player_spawn["y"])
                if best is None or score < best[0]:
                    best = (score, nx, ny)
            if best:
                board.board[best[2]][best[1]] = unit
                board.board[y][x] = None
                _recount_faction_units()
                _refresh_controlled_hexes()
                return


def _normalized_victory_view():
    goals = {}
    progress = {}
    mapping = {
        "military": "military_control",
        "economic": "economic",
        "cultural": "military_elimination",
        "technology": "technology",
    }
    for legacy_key, source_key in mapping.items():
        goals[legacy_key] = {
            "target": VICTORY_GOALS[source_key]["target"],
            "title": VICTORY_GOALS[source_key]["title"],
        }
        progress[legacy_key] = int(game_state["victory_progress"].get(source_key, 0))
    return goals, progress


def _game_snapshot(message=""):
    phase = _current_phase()
    actions = PHASE_ACTIONS[phase]
    factions_state = _serialize_factions_state()
    battle_payload = _serialize_battle()
    board = game_state["board"]
    selected_unit_payload = None
    selected_hex_payload = game_state.get("selected_hex")
    selected_hex_info = None
    if game_state.get("selected_unit") and board:
        sx, sy = game_state["selected_unit"]["x"], game_state["selected_unit"]["y"]
        if _within(sx, sy, board.width, board.height):
            selected_unit_payload = _serialize_unit_for_hex(board.board[sy][sx], sx, sy)
    if selected_hex_payload:
        hx, hy = selected_hex_payload["x"], selected_hex_payload["y"]
        if board and _within(hx, hy, board.width, board.height):
            selected_hex_info = {
                "x": hx,
                "y": hy,
                "terrain": _cell_terrain(hx, hy),
                "elevation": game_state["map"]["hexes"][hy][hx]["elevation"],
                "owner": game_state["controlled_hexes"].get(f"{hx},{hy}"),
                "building": next(
                    (b for b in game_state["buildings"] if b["x"] == hx and b["y"] == hy),
                    None,
                ),
            }
    victory_goals_view, victory_progress_view = _normalized_victory_view()
    return {
        "status": "ok",
        "message": message,
        "turn": game_state["turn"],
        "phase": phase,
        "focus": game_state["focus"],
        "resources": game_state["resources"],
        "victory_progress": victory_progress_view,
        "victory_goals": victory_goals_view,
        "winner": game_state["winner"],
        "board": _serialize_board(),
        "hexes": _serialize_hexes(),
        "map_size": {"width": game_state["map"]["width"], "height": game_state["map"]["height"]},
        "rivers": game_state["map"].get("rivers", []),
        "continents": game_state["map"].get("continents", []),
        "terrain_types": TERRAIN_TYPES,
        "available_actions": actions,
        "action_labels": _action_labels(actions),
        "faction": game_state["player_faction"]["name"] if game_state["player_faction"] else "",
        "factions_state": factions_state,
        "factions": factions_state,
        "unit_types": UNIT_TYPES,
        "battle": battle_payload,
        "battle_positions": battle_payload.get("battle_positions"),
        "selected_unit": selected_unit_payload,
        "selected_hex": selected_hex_info,
        "reachable_hexes": game_state.get("reachable_hexes", []),
        "attackable_hexes": game_state.get("attackable_hexes", []),
        "controlled_hexes": game_state.get("controlled_hexes", {}),
        "buildings": game_state.get("buildings", []),
        "cards": game_state.get("cards", {}),
        "effects": game_state.get("effects", {}),
        "logs": game_state.get("log", {"battle": [], "event": []}),
        "current_turn_owner": game_state["player_faction"]["name"] if game_state["player_faction"] else "",
        "phase_help": {
            "Resurssivaihe": "Kerää tulot ja ylläpidä armeija.",
            "Korttivaihe": "Nosta ja pelaa kortteja.",
            "Liikevaihe": "Valitse oma yksikkö ja siirrä sallittuun heksiin.",
            "Taisteluvaihe": "Hyökkää valitulla yksiköllä viereiseen viholliseen.",
            "Hallintavaihe": "Rekrytoi, rakenna ja tutki.",
            "Vuoron lopetus": "Lopeta vuoro ja anna AI:n pelata.",
        }.get(phase, ""),
    }


def _set_winner_if_reached():
    if game_state["winner"]:
        return True
    player = game_state["player_faction"]["name"] if game_state["player_faction"] else None
    if not player:
        return False
    enemy_units = [u for _, _, u in _list_units(exclude_faction=player)]
    if not enemy_units:
        game_state["winner"] = VICTORY_GOALS["military_elimination"]["title"]
        return True
    player_control = sum(1 for owner in game_state["controlled_hexes"].values() if owner == player)
    if player_control >= VICTORY_GOALS["military_control"]["target"]:
        game_state["winner"] = VICTORY_GOALS["military_control"]["title"]
        return True
    if game_state["resources"]["gold"] >= VICTORY_GOALS["economic"]["target"]:
        game_state["winner"] = VICTORY_GOALS["economic"]["title"]
        return True
    if game_state["victory_progress"]["technology"] >= VICTORY_GOALS["technology"]["target"] or game_state["universal_science_unlocked"]:
        game_state["winner"] = VICTORY_GOALS["technology"]["title"]
        return True
    player_units = [u for _, _, u in _list_units(faction_name=player)]
    player_has_chief = any(u["unit_key"] == "chief" for u in player_units)
    if (not player_units and player_control == 0) or (not player_has_chief and player_control == 0):
        game_state["winner"] = "Häviö: heimosi hajosi."
        return True
    return False


def _phase_for_action(action):
    if action in {"attack"}:
        return "Taisteluvaihe"
    if action in {"move", "hex_click"}:
        return "Liikevaihe"
    if action in {"draw_card", "play_card"}:
        return "Korttivaihe"
    if action in {
        "recruit_infantry",
        "recruit_cavalry",
        "recruit_merchant",
        "build_camp",
        "build_market",
        "build_fortress",
        "research",
    }:
        return "Hallintavaihe"
    return None


def _jump_to_phase_for_action(action):
    target_phase = _phase_for_action(action)
    if target_phase and _current_phase() != target_phase:
        game_state["phase_index"] = TURN_PHASES.index(target_phase)
        return True
    return False


def _advance_phase():
    game_state["phase_index"] = (game_state["phase_index"] + 1) % len(TURN_PHASES)
    if _current_phase() == "Resurssivaihe":
        game_state["turn"] += 1
    return f"Vaihe vaihdettu: {_current_phase()}."


def _apply_action(action, payload=None):
    payload = payload or {}
    phase = _current_phase()
    player_name = game_state["player_faction"]["name"]
    if action in {"next_phase", "end_phase"}:
        if action == "next_phase" and phase == "Resurssivaihe" and not _phase_default_action_done(phase):
            msg = _apply_action("collect_resources", payload)
            _advance_phase()
            return f"{msg} Vaihe vaihdettu: {_current_phase()}."
        return _advance_phase()
    if action == "end_turn":
        game_state["phase_index"] = TURN_PHASES.index("Vuoron lopetus")
        _run_simple_ai_turn()
        _clear_turn_temporary_effects()
        game_state["phase_index"] = TURN_PHASES.index("Resurssivaihe")
        game_state["turn"] += 1
        return "Vuoro päättyi. AI teki siirtonsa."
    if action not in PHASE_ACTIONS.get(phase, []):
        return "Toiminto ei ole sallittu tässä vaiheessa."

    if action == "collect_resources":
        gains = _collect_income(player_name)
        upkeep_cost = max(1, len(_list_units(faction_name=player_name)) // 5)
        game_state["resources"]["food"] = max(0, game_state["resources"]["food"] - upkeep_cost)
        game_state["phase_flags"]["resource_collected"] = True
        game_state["log"]["event"].insert(0, {"type": "income", "gains": gains, "upkeep": upkeep_cost})
        game_state["log"]["event"] = game_state["log"]["event"][:20]
        return f"Resurssit kerätty: +{gains['gold']} kulta, +{gains['food']} ruoka."

    if action == "draw_card":
        drawn = _draw_cards_for_player(1)
        if not drawn:
            return "Korttipakka on tyhjä."
        return f"Nostit kortin: {drawn[0]}."

    if action == "play_card":
        card_id = payload.get("card_id")
        if not card_id:
            return "Valitse kortti pelattavaksi."
        return _play_card(card_id)

    if action == "hex_click":
        try:
            col = int(payload.get("x"))
            row = int(payload.get("y"))
        except (TypeError, ValueError):
            return "Virheellinen heksivalinta."
        return _resolve_hex_click(col, row)

    if action == "recruit_infantry":
        return _recruit_unit("infantry")
    if action == "recruit_cavalry":
        return _recruit_unit("cavalry")
    if action == "recruit_merchant":
        return _recruit_unit("merchant")

    if action == "build_camp":
        return _build_structure("camp")
    if action == "build_market":
        return _build_structure("market")
    if action == "build_fortress":
        return _build_structure("fortress")

    if action == "research":
        if game_state["resources"]["artisans"] < 1:
            return "Tutkimus epäonnistui: käsityöläisiä tarvitaan."
        game_state["resources"]["artisans"] -= 1
        game_state["victory_progress"]["technology"] += 1
        return "Teknologia kehittyi (+1)."

    # Legacy API compatibility
    if action == "move":
        selected = game_state.get("selected_unit")
        if not selected:
            source = _find_unit_coordinates(player_name)
            if source:
                _select_unit(source[0], source[1])
                selected = game_state.get("selected_unit")
        if not selected or not game_state["reachable_hexes"]:
            return "Liike ei onnistunut: valittua yksikköä tai kohteita ei ole."
        target = game_state["reachable_hexes"][0]
        return _execute_move(target["x"], target["y"])
    if action == "attack":
        selected = game_state.get("selected_unit")
        if not selected:
            source = _find_unit_coordinates(player_name)
            if source:
                _select_unit(source[0], source[1])
                selected = game_state.get("selected_unit")
        if not selected:
            return "Hyökkäys ei onnistunut: valittua yksikköä ei ole."
        if not game_state["attackable_hexes"]:
            # Legacy behavior: auto-target nearest enemy if no adjacent target.
            return _resolve_attack(player_name)
        target = game_state["attackable_hexes"][0]
        return _resolve_targeted_attack(selected["x"], selected["y"], target["x"], target["y"])

    return "Tuntematon toiminto."


def _reset_mvp_runtime_state():
    game_state["selected_unit"] = None
    game_state["selected_hex"] = None
    game_state["reachable_hexes"] = []
    game_state["attackable_hexes"] = []
    game_state["controlled_hexes"] = {}
    game_state["buildings"] = []
    game_state["cards"] = _init_card_state()
    game_state["effects"] = _init_effects()
    game_state["phase_flags"] = {"resource_collected": False, "card_drawn": False}
    game_state["log"] = {"battle": [], "event": []}
    game_state["universal_science_unlocked"] = False


@app.route("/")
def index():
    return render_template("index.html", factions=factions)


@app.route("/start_game", methods=["POST"])
def start_game():
    faction_choice = int(request.form["faction"])
    player_faction = factions[faction_choice]
    board = GameBoard(BOARD_WIDTH, BOARD_HEIGHT)
    diplomacy = DiplomacySystem()

    game_state["board"] = board
    game_state["diplomacy"] = diplomacy
    game_state["player_faction"] = player_faction
    game_state["turn"] = 1
    game_state["phase_index"] = 0
    game_state["focus"] = "Valloitus"
    game_state["victory_progress"] = {"military": 0, "economic": 0, "cultural": 0, "technology": 0}
    _sync_victory_progress_keys()
    game_state["winner"] = None
    game_state["event_index"] = 0
    game_state["resources"] = _starting_resources(player_faction["name"])
    game_state["battle"] = {"last": None, "history": []}
    game_state["map"] = _init_hex_map(BOARD_WIDTH, BOARD_HEIGHT)
    game_state["spawn_points"] = _generate_spawn_points()
    game_state["factions_state"] = _init_factions_state(player_faction["name"])
    game_state["next_unit_id"] = 1
    game_state["battle_event_id"] = 0
    _reset_mvp_runtime_state()

    _place_initial_units(player_faction["name"])
    _recount_faction_units()
    _refresh_controlled_hexes()
    _draw_cards_for_player(3)
    _set_winner_if_reached()

    snapshot = _game_snapshot("Peli aloitettu: maantieteellisesti realistinen heksamaailma luotu.")
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
    message = _apply_action(action, payload)
    _set_winner_if_reached()
    return jsonify(_game_snapshot(message))


@app.route("/battle_roll", methods=["POST"])
def battle_roll():
    if not game_state["board"]:
        return jsonify({"error": "Game not started"}), 400
    if _current_phase() != "Taisteluvaihe":
        return jsonify({"error": "Battle roll is only allowed during Taisteluvaihe"}), 400
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
