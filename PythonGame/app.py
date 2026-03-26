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

BOARD_WIDTH = 20
BOARD_HEIGHT = 20
TERRAIN_TYPES = ["water", "shore", "plains", "forest", "mountain", "desert", "river", "lake"]

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
}


def _starting_resources(faction_name):
    base = {"horses": 3, "gold": 3, "food": 3, "artisans": 2, "cattle": 3}
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


def _distance_to_water(height_map, col, row):
    width = len(height_map[0])
    height = len(height_map)
    best = width + height
    for rr in range(height):
        for cc in range(width):
            if height_map[rr][cc] <= 0.0:
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
    height_map = [[_base_height(col, row, width, height) for col in range(width)] for row in range(height)]

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
        _paint_ellipse(height_map, width * cx, height * cy, width * rx, height * ry, delta)

    # India peninsula + SE Asia
    _paint_ellipse(height_map, width * 0.76, height * 0.63, width * 0.10, height * 0.14, 0.93)
    _paint_ellipse(height_map, width * 0.89, height * 0.67, width * 0.10, height * 0.12, 0.80)

    # North Africa rim visible in south-west
    _paint_ellipse(height_map, width * 0.22, height * 0.60, width * 0.24, height * 0.13, 0.92)

    # Sea basins: Mediterranean, Arabian Sea, Bay of Bengal, Pacific edge
    _paint_ellipse(height_map, width * 0.28, height * 0.44, width * 0.11, height * 0.08, -0.78)  # Mediterranean
    _paint_ellipse(height_map, width * 0.59, height * 0.56, width * 0.10, height * 0.11, -0.68)  # Arabian Sea
    _paint_ellipse(height_map, width * 0.81, height * 0.58, width * 0.08, height * 0.10, -0.65)  # Bay of Bengal
    _paint_ellipse(height_map, width * 0.95, height * 0.46, width * 0.10, height * 0.22, -0.92)  # Pacific side

    # Carve west/south oceans
    for row in range(height):
        for col in range(width):
            west_ocean = max(0.0, (0.14 - (col / max(1, width - 1))))
            south_ocean = max(0.0, ((row / max(1, height - 1)) - 0.82))
            height_map[row][col] -= west_ocean * 1.3 + south_ocean * 1.0
    return height_map


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
    _add_mountain_chain(height_map, caucasus_himalaya, strength=0.64)
    _add_mountain_chain(height_map, ural, strength=0.46)
    _add_mountain_chain(height_map, tian_shan_altai, strength=0.50)


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
        neigh.sort(key=lambda p: height_map[p[1]][p[0]])
        next_cell = neigh[0]
        if height_map[next_cell[1]][next_cell[0]] >= height_map[row][col]:
            # fallback: kohti lähintä merta
            best = min(
                neigh,
                key=lambda p: _distance_to_water(height_map, p[0], p[1]) + height_map[p[1]][p[0]] * 0.2,
            )
            next_cell = best
        current = next_cell
    return path


def _carve_rivers(height_map, terrain):
    width = len(height_map[0])
    height = len(height_map)
    peaks = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if terrain[row][col] in {"mountain", "forest"} and height_map[row][col] > 1.35:
                peaks.append((col, row, height_map[row][col]))
    peaks.sort(key=lambda item: item[2], reverse=True)
    used = set()
    river_paths = []
    for col, row, _ in peaks[:6]:
        path = _trace_river(height_map, col, row, terrain)
        if len(path) < 4:
            continue
        # joen täytyy päätyä mereen/rantaan
        end_col, end_row = path[-1]
        if terrain[end_row][end_col] not in {"water", "shore"}:
            continue
        fresh = [p for p in path if p not in used]
        if len(fresh) < 4:
            continue
        for c, r in path[:-1]:
            if terrain[r][c] in {"plains", "forest", "desert"}:
                terrain[r][c] = "river"
                used.add((c, r))
        river_paths.append(path)
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


def _lake_pass(height_map, terrain):
    width = len(terrain[0])
    height = len(terrain)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if terrain[row][col] in {"water", "shore", "river"}:
                continue
            neigh = [terrain[nr][nc] for nc, nr in _axial_neighbors(col, row) if _within(nc, nr, width, height)]
            water_neighbors = sum(1 for t in neigh if t in {"water", "shore", "river"})
            if water_neighbors >= 3 and height_map[row][col] > 0.55:
                terrain[row][col] = "lake"


def _assign_biomes(height_map):
    width = len(height_map[0])
    height = len(height_map)
    terrain = [["water" for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            h = height_map[row][col]
            lat = abs((row / max(1, height - 1)) * 2 - 1)  # 0 equator, 1 poles
            inland = _distance_to_water(height_map, col, row)
            moisture = (
                math.sin(col * 0.29 + row * 0.11) * 0.35
                + math.cos(row * 0.23) * 0.25
                + (0.45 - lat * 0.4)
                - inland * 0.032
            )

            if h <= 0.02:
                terrain[row][col] = "water"
            elif h >= 1.40:
                terrain[row][col] = "mountain"
            elif moisture < -0.08 and inland > 4 and lat < 0.55:
                terrain[row][col] = "desert"
            elif moisture > 0.15:
                terrain[row][col] = "forest"
            else:
                terrain[row][col] = "plains"

    _coastline_pass(terrain)
    _lake_pass(height_map, terrain)
    river_paths = _carve_rivers(height_map, terrain)
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
    if elevation >= 1.45:
        return "high"
    if elevation >= 0.85:
        return "mid"
    if elevation >= 0.25:
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
    terrain, river_paths = _assign_biomes(height_map)
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
                units.append(
                    {
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
                    }
                )

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


def _game_snapshot(message=""):
    actions = PHASE_ACTIONS[_current_phase()] + ["end_phase"]
    factions_state = _serialize_factions_state()
    battle_payload = _serialize_battle()
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
        if board.board[ty][tx] is None and _cell_terrain(tx, ty) not in {"water", "lake"}:
            board.board[ty][tx] = board.board[sy][sx]
            board.board[sy][sx] = None
            _recount_faction_units()
            return "Yksikkö liikkui yhden alueen eteenpäin."
        return "Kohderuutu on varattu tai kulkukelvoton, liike epäonnistui."
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
    board = GameBoard(BOARD_WIDTH, BOARD_HEIGHT)
    diplomacy = DiplomacySystem()

    game_state["board"] = board
    game_state["diplomacy"] = diplomacy
    game_state["player_faction"] = player_faction
    game_state["turn"] = 1
    game_state["phase_index"] = 0
    game_state["focus"] = "Valloitus"
    game_state["victory_progress"] = {"military": 0, "economic": 0, "cultural": 0, "technology": 0}
    game_state["winner"] = None
    game_state["event_index"] = 0
    game_state["resources"] = _starting_resources(player_faction["name"])
    game_state["battle"] = {"last": None, "history": []}
    game_state["map"] = _init_hex_map(BOARD_WIDTH, BOARD_HEIGHT)
    game_state["spawn_points"] = _generate_spawn_points()
    game_state["factions_state"] = _init_factions_state(player_faction["name"])
    game_state["next_unit_id"] = 1
    game_state["battle_event_id"] = 0

    _place_initial_units(player_faction["name"])
    _recount_faction_units()
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
