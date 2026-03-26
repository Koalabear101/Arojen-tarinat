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

const terrainIcons = {
    plains: "🌿",
    forest: "🌲",
    mountain: "⛰",
    desert: "◌",
    water: "≈",
    lake: "≈",
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

    positioned.forEach((hex) => {
        const cx = hex.px - minX + margin;
        const cy = hex.py - minY + margin;
        const key = `${hex.q},${hex.r}`;

        const tileGroup = document.createElementNS(SVG_NS, "g");
        tileGroup.setAttribute("class", "hex-tile");
        tileGroup.dataset.key = key;
        if (selectedHexKey === key) {
            tileGroup.classList.add("selected");
        }
        if (hex.highlight === "attacker") {
            tileGroup.classList.add("highlight-attacker");
        } else if (hex.highlight === "defender") {
            tileGroup.classList.add("highlight-defender");
        }

        const polygon = document.createElementNS(SVG_NS, "polygon");
        polygon.setAttribute("points", hexPoints(cx, cy, size));
        polygon.setAttribute("class", `hex-shape biome-${hex.terrain}`);
        tileGroup.appendChild(polygon);

        const biomeIcon = document.createElementNS(SVG_NS, "text");
        biomeIcon.setAttribute("x", String(cx));
        biomeIcon.setAttribute("y", String(cy + 4));
        biomeIcon.setAttribute("class", "hex-biome-icon");
        biomeIcon.textContent = terrainIcons[hex.terrain] || "·";
        tileGroup.appendChild(biomeIcon);

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
