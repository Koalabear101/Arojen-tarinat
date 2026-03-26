const resourceLabels = {
    horses: "Hevoset",
    gold: "Kulta",
    food: "Ruoka",
    artisans: "Käsityöläiset",
    cattle: "Karja",
};

const resourceIcons = {
    horses: "🐎",
    gold: "🪙",
    food: "🌾",
    artisans: "🛠️",
    cattle: "🐄",
};

const victoryLabels = {
    military: "Sotilaallinen",
    economic: "Taloudellinen",
    cultural: "Kulttuurinen",
    technology: "Teknologinen",
};

const victoryIcons = {
    military: "⚔️",
    economic: "💰",
    cultural: "🏛️",
    technology: "⚙️",
};

const elevationColors = {
    ocean: "#2f5f97",
    coast: "#74a9d8",
    plains: "#8dbb6f",
    hills: "#4f7f3f",
};

const factionSigil = {
    "Mongoli-heimo": "🐺",
    "Kiinan dynastia": "🐉",
    "Persialainen valtakunta": "🦁",
    "Venäläiset ruhtinaskunnat": "🦅",
};

const unitGlyphs = {
    cavalry: "🐎",
    infantry: "🛡️",
    chief: "🚩",
    merchant: "🧭",
};

const SVG_NS = "http://www.w3.org/2000/svg";
let boardZoom = 28;
let selectedHexKey = null;
let lastState = null;

function axialToPixel(q, r, size) {
    const x = size * Math.sqrt(3) * (q + r / 2);
    const y = size * 1.5 * r;
    return { x, y };
}

function hexPoints(cx, cy, size) {
    const points = [];
    for (let i = 0; i < 6; i += 1) {
        const angle = ((60 * i - 30) * Math.PI) / 180;
        points.push(`${cx + size * Math.cos(angle)},${cy + size * Math.sin(angle)}`);
    }
    return points.join(" ");
}

function flattenHexes(hexGrid) {
    if (!Array.isArray(hexGrid)) {
        return [];
    }
    const flattened = [];
    hexGrid.forEach((row) => {
        if (Array.isArray(row)) {
            row.forEach((hex) => {
                if (hex) {
                    flattened.push(hex);
                }
            });
        }
    });
    return flattened;
}

function coordKey(col, row) {
    return `${col},${row}`;
}

function offsetNeighbors(col, row) {
    const even = row % 2 === 0;
    const deltas = even
        ? [[-1, -1], [0, -1], [-1, 0], [1, 0], [-1, 1], [0, 1]]
        : [[0, -1], [1, -1], [-1, 0], [1, 0], [0, 1], [1, 1]];
    return deltas.map(([dx, dy]) => [col + dx, row + dy]);
}

function normalizeElevationBand(band) {
    if (band === "sea" || band === "ocean") {
        return "ocean";
    }
    if (band === "coast") {
        return "coast";
    }
    if (band === "highland" || band === "mountains") {
        return "mountains";
    }
    if (band === "upland" || band === "hills") {
        return "hills";
    }
    return "plains";
}

function isLandBand(band) {
    return band === "plains" || band === "hills" || band === "mountains";
}

function buildHexLookup(hexes) {
    const lookup = new Map();
    hexes.forEach((hex) => {
        lookup.set(coordKey(hex.col, hex.row), hex);
    });
    return lookup;
}

function buildContinentIds(hexes, continents, lookup) {
    const explicit = new Map();
    hexes.forEach((hex) => {
        if (Number.isInteger(hex.continent_id) && isLandBand(normalizeElevationBand(hex.elevation_band))) {
            explicit.set(coordKey(hex.col, hex.row), hex.continent_id);
        }
    });
    if (explicit.size) {
        return explicit;
    }

    if (Array.isArray(continents) && continents.length) {
        const centroids = continents
            .filter((continent) => continent && continent.centroid)
            .map((continent, index) => ({
                id: Number.isInteger(continent.id) ? continent.id : index + 1,
                x: Number(continent.centroid.x ?? 0),
                y: Number(continent.centroid.y ?? 0),
            }));
        if (centroids.length) {
            const fromCentroid = new Map();
            hexes.forEach((hex) => {
                const band = normalizeElevationBand(hex.elevation_band);
                if (!isLandBand(band)) {
                    return;
                }
                const nearest = centroids.reduce((best, current) => {
                    const dist = (hex.col - current.x) ** 2 + (hex.row - current.y) ** 2;
                    if (!best || dist < best.dist) {
                        return { id: current.id, dist };
                    }
                    return best;
                }, null);
                if (nearest) {
                    fromCentroid.set(coordKey(hex.col, hex.row), nearest.id);
                }
            });
            if (fromCentroid.size) {
                return fromCentroid;
            }
        }
    }

    const continentIds = new Map();
    let nextId = 1;
    hexes.forEach((hex) => {
        const key = coordKey(hex.col, hex.row);
        if (continentIds.has(key)) {
            return;
        }
        const band = normalizeElevationBand(hex.elevation_band);
        if (!isLandBand(band)) {
            return;
        }
        const queue = [hex];
        continentIds.set(key, nextId);
        while (queue.length) {
            const current = queue.shift();
            offsetNeighbors(current.col, current.row).forEach(([nc, nr]) => {
                const nKey = coordKey(nc, nr);
                if (continentIds.has(nKey)) {
                    return;
                }
                const neighbor = lookup.get(nKey);
                if (!neighbor) {
                    return;
                }
                if (!isLandBand(normalizeElevationBand(neighbor.elevation_band))) {
                    return;
                }
                continentIds.set(nKey, nextId);
                queue.push(neighbor);
            });
        }
        nextId += 1;
    });
    return continentIds;
}

function buildRiverNetwork(rivers) {
    const network = new Map();
    if (!Array.isArray(rivers)) {
        return network;
    }
    rivers.forEach((riverPath) => {
        if (!Array.isArray(riverPath)) {
            return;
        }
        riverPath.forEach((point, index) => {
            const key = coordKey(point.x, point.y);
            if (!network.has(key)) {
                network.set(key, new Set());
            }
            if (index > 0) {
                const prev = riverPath[index - 1];
                network.get(key).add(coordKey(prev.x, prev.y));
            }
            if (index < riverPath.length - 1) {
                const next = riverPath[index + 1];
                network.get(key).add(coordKey(next.x, next.y));
            }
        });
    });
    return network;
}

function addMapDefs(svg) {
    const defs = document.createElementNS(SVG_NS, "defs");

    const mountainGradient = document.createElementNS(SVG_NS, "linearGradient");
    mountainGradient.setAttribute("id", "elev-mountains-gradient");
    mountainGradient.setAttribute("x1", "0%");
    mountainGradient.setAttribute("y1", "100%");
    mountainGradient.setAttribute("x2", "0%");
    mountainGradient.setAttribute("y2", "0%");
    const mStopLow = document.createElementNS(SVG_NS, "stop");
    mStopLow.setAttribute("offset", "0%");
    mStopLow.setAttribute("stop-color", "#565f66");
    const mStopHigh = document.createElementNS(SVG_NS, "stop");
    mStopHigh.setAttribute("offset", "100%");
    mStopHigh.setAttribute("stop-color", "#bbc4cb");
    mountainGradient.appendChild(mStopLow);
    mountainGradient.appendChild(mStopHigh);
    defs.appendChild(mountainGradient);

    const forestPattern = document.createElementNS(SVG_NS, "pattern");
    forestPattern.setAttribute("id", "role-forest-pattern");
    forestPattern.setAttribute("width", "12");
    forestPattern.setAttribute("height", "12");
    forestPattern.setAttribute("patternUnits", "userSpaceOnUse");
    const forestTriangle = document.createElementNS(SVG_NS, "path");
    forestTriangle.setAttribute("d", "M2,10 L5,4 L8,10 Z");
    forestTriangle.setAttribute("fill", "rgba(25, 64, 27, 0.45)");
    const forestDot = document.createElementNS(SVG_NS, "circle");
    forestDot.setAttribute("cx", "10");
    forestDot.setAttribute("cy", "3");
    forestDot.setAttribute("r", "1.4");
    forestDot.setAttribute("fill", "rgba(34, 74, 38, 0.42)");
    forestPattern.appendChild(forestTriangle);
    forestPattern.appendChild(forestDot);
    defs.appendChild(forestPattern);

    const mountainPattern = document.createElementNS(SVG_NS, "pattern");
    mountainPattern.setAttribute("id", "role-mountain-pattern");
    mountainPattern.setAttribute("width", "8");
    mountainPattern.setAttribute("height", "8");
    mountainPattern.setAttribute("patternUnits", "userSpaceOnUse");
    const mLineA = document.createElementNS(SVG_NS, "path");
    mLineA.setAttribute("d", "M0,7 L7,0");
    mLineA.setAttribute("stroke", "rgba(48, 54, 60, 0.35)");
    mLineA.setAttribute("stroke-width", "1");
    const mLineB = document.createElementNS(SVG_NS, "path");
    mLineB.setAttribute("d", "M-2,8 L0,6 M6,2 L8,0");
    mLineB.setAttribute("stroke", "rgba(48, 54, 60, 0.25)");
    mLineB.setAttribute("stroke-width", "1");
    mountainPattern.appendChild(mLineA);
    mountainPattern.appendChild(mLineB);
    defs.appendChild(mountainPattern);

    const desertPattern = document.createElementNS(SVG_NS, "pattern");
    desertPattern.setAttribute("id", "role-desert-pattern");
    desertPattern.setAttribute("width", "10");
    desertPattern.setAttribute("height", "10");
    desertPattern.setAttribute("patternUnits", "userSpaceOnUse");
    const dDotA = document.createElementNS(SVG_NS, "circle");
    dDotA.setAttribute("cx", "2");
    dDotA.setAttribute("cy", "2");
    dDotA.setAttribute("r", "0.9");
    dDotA.setAttribute("fill", "rgba(143, 113, 63, 0.35)");
    const dDotB = document.createElementNS(SVG_NS, "circle");
    dDotB.setAttribute("cx", "7");
    dDotB.setAttribute("cy", "6");
    dDotB.setAttribute("r", "1.1");
    dDotB.setAttribute("fill", "rgba(143, 113, 63, 0.28)");
    desertPattern.appendChild(dDotA);
    desertPattern.appendChild(dDotB);
    defs.appendChild(desertPattern);

    svg.appendChild(defs);
}

function appendTerrainOverlay(tileGroup, points, terrainRole) {
    let patternId = null;
    if (terrainRole === "woodland" || terrainRole === "forest") {
        patternId = "role-forest-pattern";
    } else if (terrainRole === "high_peak" || terrainRole === "highland" || terrainRole === "mountain") {
        patternId = "role-mountain-pattern";
    } else if (terrainRole === "arid_zone" || terrainRole === "arid" || terrainRole === "desert") {
        patternId = "role-desert-pattern";
    }
    if (!patternId) {
        return;
    }
    const overlay = document.createElementNS(SVG_NS, "polygon");
    overlay.setAttribute("points", points);
    overlay.setAttribute("class", "terrain-role-overlay");
    overlay.setAttribute("fill", `url(#${patternId})`);
    tileGroup.appendChild(overlay);
}

function ensureTooltip() {
    return document.getElementById("unit-tooltip");
}

function showTooltip(content, event) {
    const tooltip = ensureTooltip();
    if (!tooltip) {
        return;
    }
    tooltip.innerHTML = content;
    tooltip.classList.remove("hidden");
    moveTooltip(event);
}

function moveTooltip(event) {
    const tooltip = ensureTooltip();
    if (!tooltip || tooltip.classList.contains("hidden")) {
        return;
    }
    tooltip.style.left = `${event.clientX + 10}px`;
    tooltip.style.top = `${event.clientY + 10}px`;
}

function hideTooltip() {
    const tooltip = ensureTooltip();
    if (!tooltip) {
        return;
    }
    tooltip.classList.add("hidden");
}

function renderState(data) {
    lastState = data;
    document.getElementById("turn").textContent = data.turn;
    document.getElementById("phase").textContent = data.phase;
    document.getElementById("focus").textContent = data.focus;
    document.getElementById("player-faction").textContent = data.faction;
    document.getElementById("messages").textContent = data.message || "";

    renderHexBoard(data);
    renderResources(data.resources || {});
    renderVictoryProgress(data.victory_progress || {}, data.victory_goals || {}, data.winner);
    renderFactionTokens(data.factions_state || []);
    renderBattleView(data.battle || {});
    renderControls(data.available_actions || [], data.action_labels || {}, data.winner);
}

function renderHexBoard(data) {
    const board = document.getElementById("board");
    if (!board) {
        return;
    }
    board.innerHTML = "";

    const flatHexes = flattenHexes(data.hexes);
    if (!flatHexes.length) {
        board.textContent = "Kartta latautuu...";
        return;
    }

    const size = boardZoom;
    const margin = size * 2;
    const positioned = flatHexes.map((hex) => {
        const p = axialToPixel(hex.q, hex.r, size);
        return { ...hex, px: p.x, py: p.y };
    });

    const minX = Math.min(...positioned.map((hex) => hex.px));
    const minY = Math.min(...positioned.map((hex) => hex.py));
    const maxX = Math.max(...positioned.map((hex) => hex.px));
    const maxY = Math.max(...positioned.map((hex) => hex.py));
    const width = maxX - minX + margin * 2;
    const height = maxY - minY + margin * 2;

    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("id", "hex-map");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("width", String(width));
    svg.setAttribute("height", String(height));
    addMapDefs(svg);

    const hexLookup = buildHexLookup(positioned);
    const continentIds = buildContinentIds(positioned, data.continents || [], hexLookup);
    const riverNetwork = buildRiverNetwork(data.rivers || []);

    positioned.forEach((hex) => {
        const cx = hex.px - minX + margin;
        const cy = hex.py - minY + margin;
        const key = `${hex.q},${hex.r}`;
        const coord = coordKey(hex.col, hex.row);
        const elevationBand = normalizeElevationBand(hex.elevation_band);

        const tileGroup = document.createElementNS(SVG_NS, "g");
        tileGroup.setAttribute("class", "hex-tile");
        tileGroup.classList.add(`elev-${elevationBand}`);
        tileGroup.dataset.key = key;
        if (selectedHexKey === key) {
            tileGroup.classList.add("selected");
        }
        if (hex.highlight === "attacker") {
            tileGroup.classList.add("highlight-attacker");
        } else if (hex.highlight === "defender") {
            tileGroup.classList.add("highlight-defender");
        }
        if (hex.shoreline) {
            tileGroup.classList.add("shoreline");
        }

        const polygon = document.createElementNS(SVG_NS, "polygon");
        polygon.setAttribute("points", hexPoints(cx, cy, size));
        polygon.setAttribute("class", "hex-shape");
        if (elevationBand === "mountains") {
            polygon.setAttribute("fill", "url(#elev-mountains-gradient)");
        } else {
            polygon.setAttribute("fill", elevationColors[elevationBand] || elevationColors.plains);
        }
        tileGroup.appendChild(polygon);

        const currentContinentId = continentIds.get(coord);
        if (currentContinentId != null) {
            const borderEdges = offsetNeighbors(hex.col, hex.row).reduce((sum, [nc, nr]) => {
                const neighborId = continentIds.get(coordKey(nc, nr));
                return neighborId != null && neighborId !== currentContinentId ? sum + 1 : sum;
            }, 0);
            if (borderEdges > 0) {
                const continentBlend = document.createElementNS(SVG_NS, "polygon");
                continentBlend.setAttribute("points", hexPoints(cx, cy, size));
                continentBlend.setAttribute("class", "continent-edge-blend");
                continentBlend.setAttribute("opacity", String(Math.min(0.16, 0.05 + borderEdges * 0.02)));
                tileGroup.appendChild(continentBlend);
            }
        }

        appendTerrainOverlay(tileGroup, hexPoints(cx, cy, size), hex.terrain_role);

        const riverLinks = riverNetwork.get(coord);
        if (riverLinks && riverLinks.size > 0) {
            tileGroup.classList.add("river-segment");
            const linkedHexes = [...riverLinks]
                .map((neighborKey) => hexLookup.get(neighborKey))
                .filter(Boolean);
            if (linkedHexes.length) {
                linkedHexes.sort((a, b) => (b.elevation ?? 0) - (a.elevation ?? 0));
                const high = linkedHexes[0];
                const low = linkedHexes[linkedHexes.length - 1];
                const highPos = { x: high.px - minX + margin, y: high.py - minY + margin };
                const lowPos = { x: low.px - minX + margin, y: low.py - minY + margin };
                const riverLine = document.createElementNS(SVG_NS, "line");
                if (linkedHexes.length > 1) {
                    riverLine.setAttribute("x1", String((highPos.x + cx) / 2));
                    riverLine.setAttribute("y1", String((highPos.y + cy) / 2));
                    riverLine.setAttribute("x2", String((lowPos.x + cx) / 2));
                    riverLine.setAttribute("y2", String((lowPos.y + cy) / 2));
                } else {
                    riverLine.setAttribute("x1", String(cx));
                    riverLine.setAttribute("y1", String(cy));
                    riverLine.setAttribute("x2", String((highPos.x + cx) / 2));
                    riverLine.setAttribute("y2", String((highPos.y + cy) / 2));
                }
                riverLine.setAttribute("class", "river-flow");
                tileGroup.appendChild(riverLine);
            }
        }

        if (selectedHexKey === key) {
            const selectionRing = document.createElementNS(SVG_NS, "polygon");
            selectionRing.setAttribute("points", hexPoints(cx, cy, size * 1.01));
            selectionRing.setAttribute("class", "hex-selection-ring");
            tileGroup.appendChild(selectionRing);
        }

        if (hex.faction_marker) {
            const spawnBadge = document.createElementNS(SVG_NS, "circle");
            spawnBadge.setAttribute("cx", String(cx - size * 0.5));
            spawnBadge.setAttribute("cy", String(cy - size * 0.52));
            spawnBadge.setAttribute("r", String(size * 0.22));
            spawnBadge.setAttribute("class", "spawn-badge");
            tileGroup.appendChild(spawnBadge);

            const marker = document.createElementNS(SVG_NS, "text");
            marker.setAttribute("x", String(cx - size * 0.5));
            marker.setAttribute("y", String(cy - size * 0.45));
            marker.setAttribute("class", "hex-faction-label");
            marker.textContent = hex.faction_marker.symbol || factionSigil[hex.faction_marker.name] || "🏳️";
            tileGroup.appendChild(marker);

            const factionName = document.createElementNS(SVG_NS, "text");
            factionName.setAttribute("x", String(cx));
            factionName.setAttribute("y", String(cy - size * 0.74));
            factionName.setAttribute("class", "hex-faction-name");
            factionName.textContent = hex.faction_marker.name;
            tileGroup.appendChild(factionName);
        }

        if (Array.isArray(hex.units)) {
            hex.units.forEach((unit, index) => {
                const tokenGroup = document.createElementNS(SVG_NS, "g");
                tokenGroup.setAttribute("class", `unit-token ${unit.side === "player" ? "unit-player" : "unit-enemy"}`);

                const offsetX = cx - size * 0.3 + (index % 2) * size * 0.34;
                const offsetY = cy + size * 0.26 + Math.floor(index / 2) * size * 0.28;

                const shape = document.createElementNS(SVG_NS, "circle");
                shape.setAttribute("cx", String(offsetX));
                shape.setAttribute("cy", String(offsetY));
                shape.setAttribute("r", String(size * 0.2));
                shape.setAttribute("class", "unit-shape");
                tokenGroup.appendChild(shape);

                const glyph = document.createElementNS(SVG_NS, "text");
                glyph.setAttribute("x", String(offsetX));
                glyph.setAttribute("y", String(offsetY + 0.5));
                glyph.setAttribute("class", "unit-glyph");
                glyph.textContent = unitGlyphs[unit.unit_key] || unit.token || "•";
                tokenGroup.appendChild(glyph);

                tokenGroup.addEventListener("mouseenter", (event) => {
                    const content = `<strong>${unit.type}</strong><br>${unit.faction}<br>HP ${unit.hp}/${unit.max_hp} | ATK ${unit.strength} | DEF ${unit.defense}`;
                    showTooltip(content, event);
                });
                tokenGroup.addEventListener("mousemove", moveTooltip);
                tokenGroup.addEventListener("mouseleave", hideTooltip);
                tileGroup.appendChild(tokenGroup);
            });
        }

        tileGroup.addEventListener("click", () => {
            selectedHexKey = key;
            renderHexBoard(data);
        });
        svg.appendChild(tileGroup);
    });

    const battle = data.battle || {};
    const last = battle.last;
    if (last && last.battle_positions) {
        const attacker = last.battle_positions.attacker;
        const defender = last.battle_positions.defender;
        const start = axialToPixel(attacker.x, attacker.y, size);
        const end = axialToPixel(defender.x, defender.y, size);

        const path = document.createElementNS(SVG_NS, "line");
        path.setAttribute("x1", String(start.x - minX + margin));
        path.setAttribute("y1", String(start.y - minY + margin));
        path.setAttribute("x2", String(end.x - minX + margin));
        path.setAttribute("y2", String(end.y - minY + margin));
        path.setAttribute("class", "battle-path");
        svg.appendChild(path);

        const target = document.createElementNS(SVG_NS, "circle");
        target.setAttribute("cx", String(end.x - minX + margin));
        target.setAttribute("cy", String(end.y - minY + margin));
        target.setAttribute("r", String(size * 0.42));
        target.setAttribute("class", "battle-target");
        svg.appendChild(target);
    }

    board.appendChild(svg);
}

function renderResources(resources) {
    const resourcesList = document.getElementById("resources");
    resourcesList.innerHTML = "";
    Object.keys(resourceLabels).forEach((key) => {
        const li = document.createElement("li");
        li.innerHTML = `<span class="item-label"><span class="icon">${resourceIcons[key] ?? "•"}</span>${resourceLabels[key]}</span><span class="item-value">${resources[key] ?? 0}</span>`;
        resourcesList.appendChild(li);
    });
}

function renderVictoryProgress(progress, goals, winner) {
    const victoryList = document.getElementById("victory-progress");
    const winnerBanner = document.getElementById("winner-banner");
    victoryList.innerHTML = "";
    Object.keys(victoryLabels).forEach((key) => {
        const li = document.createElement("li");
        const current = progress[key] ?? 0;
        const target = goals[key]?.target ?? 0;
        li.innerHTML = `<span class="item-label"><span class="icon">${victoryIcons[key] ?? "•"}</span>${victoryLabels[key]}</span><span class="item-value">${current}/${target}</span>`;
        victoryList.appendChild(li);
    });
    if (winner) {
        winnerBanner.classList.remove("hidden");
        winnerBanner.textContent = `Voitto saavutettu: ${winner}`;
    } else {
        winnerBanner.classList.add("hidden");
        winnerBanner.textContent = "";
    }
}

function renderFactionTokens(factionsState) {
    const container = document.getElementById("faction-pieces");
    container.innerHTML = "";
    if (!Array.isArray(factionsState) || !factionsState.length) {
        container.innerHTML = "<p>Heimot latautuvat...</p>";
        return;
    }
    factionsState.forEach((faction) => {
        if (!faction) {
            return;
        }
        const card = document.createElement("div");
        card.className = `faction-troop-card ${faction.is_player ? "player-faction" : ""}`;
        const title = document.createElement("h4");
        title.textContent = `${faction.symbol || factionSigil[faction.name] || "🏳️"} ${faction.name}`;
        card.appendChild(title);

        const spawnPos = faction.spawn_position || { x: "?", y: "?" };
        const spawn = document.createElement("p");
        spawn.className = "faction-counter";
        spawn.textContent = `Aloitushex: (${spawnPos.x}, ${spawnPos.y}) | Yksiköt: ${faction.total_units}`;
        card.appendChild(spawn);

        const list = document.createElement("ul");
        list.className = "troop-list";
        Object.entries(faction.unit_counts || {}).forEach(([unitKey, count]) => {
            if (!count) {
                return;
            }
            const meta = (window.lastUnitTypes && window.lastUnitTypes[unitKey]) || {};
            const li = document.createElement("li");
            li.innerHTML = `<span><span class="troop-token">${meta.token || unitGlyphs[unitKey] || "•"}</span>${meta.label || unitKey}</span><strong>×${count}</strong>`;
            list.appendChild(li);
        });
        card.appendChild(list);
        container.appendChild(card);
    });
}

function renderBattleView(battle) {
    const panel = document.getElementById("battle-view");
    const result = document.getElementById("battle-result");
    const last = battle && battle.last ? battle.last : null;
    if (!panel || !result) {
        return;
    }
    if (!last) {
        result.textContent = "Ei taistelua vielä.";
        return;
    }
    document.getElementById("battle-attacker-name").textContent = last.attacker_faction;
    document.getElementById("battle-attack-rolls").textContent = `🎲 ${last.attack_die}`;
    document.getElementById("battle-attack-total").textContent = `${last.attack_total} (${last.attacker_unit})`;
    document.getElementById("battle-defender-name").textContent = last.defender_faction;
    document.getElementById("battle-defense-rolls").textContent = `🎲 ${last.defense_die}`;
    document.getElementById("battle-defense-total").textContent = `${last.defense_total} (${last.defender_unit})`;
    result.textContent = `Tulos: ${last.outcome} | Vahinko puolustajalle: ${last.damage_to_defender} | Vastahyökkäys: ${last.damage_to_attacker}`;

    panel.classList.remove("battle-animate");
    void panel.offsetWidth;
    panel.classList.add("battle-animate");
}

function renderControls(actions, actionLabels, winner) {
    const controls = document.getElementById("controls");
    controls.innerHTML = "";
    actions.forEach((action) => {
        const button = document.createElement("button");
        button.textContent = actionLabels[action] || action;
        button.disabled = Boolean(winner);
        button.addEventListener("click", () => performAction(action));
        controls.appendChild(button);
    });
}

function performAction(action) {
    fetch("/take_action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.error) {
                document.getElementById("messages").textContent = data.error;
                return;
            }
            renderState(data);
        });
}

function loadState() {
    fetch("/get_state")
        .then((response) => response.json())
        .then((data) => {
            if (data.error) {
                return;
            }
            window.lastUnitTypes = data.unit_types || {};
            renderState(data);
        });
}

function setupBoardZoom() {
    const range = document.getElementById("board-zoom-range");
    const value = document.getElementById("board-zoom-value");
    if (!range || !value) {
        return;
    }
    boardZoom = Number(range.value || 28);
    value.textContent = `${boardZoom}px`;
    range.addEventListener("input", () => {
        boardZoom = Number(range.value || 28);
        value.textContent = `${boardZoom}px`;
        if (lastState) {
            renderHexBoard(lastState);
        }
    });
}

document.getElementById("faction-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    fetch("/start_game", { method: "POST", body: formData })
        .then((response) => response.json())
        .then((data) => {
            if (data.status === "started") {
                document.getElementById("setup").style.display = "none";
                document.getElementById("game").style.display = "block";
                window.lastUnitTypes = data.unit_types || {};
                renderState(data);
            }
        });
});

document.addEventListener("mousemove", moveTooltip);
loadState();
setupBoardZoom();
