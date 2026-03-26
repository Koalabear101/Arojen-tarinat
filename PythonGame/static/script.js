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
    lake: "≈",
};

const unitSvg = {
    cavalry: "🐎",
    infantry: "🛡️",
    chief: "🚩",
    merchant: "🧭",
};

const factionSigil = {
    "Mongoli-heimo": "🟨",
    "Kiinan dynastia": "🟥",
    "Persialainen valtakunta": "🟦",
    "Venäläiset ruhtinaskunnat": "🟩",
};

let boardZoom = 34;
let selectedHexKey = null;

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

function renderState(data) {
    document.getElementById("turn").textContent = data.turn;
    document.getElementById("phase").textContent = data.phase;
    document.getElementById("focus").textContent = data.focus;
    document.getElementById("player-faction").textContent = data.faction;
    document.getElementById("messages").textContent = data.message || "";

    renderHexBoard(data);
    renderResources(data.resources);
    renderVictoryProgress(data.victory_progress, data.victory_goals, data.winner);
    renderFactionTokens(data.factions_state || []);
    renderBattleView(data.battle);
    renderControls(data.available_actions, data.action_labels, data.winner);
}

function renderHexBoard(data) {
    const boardDiv = document.getElementById("board");
    boardDiv.innerHTML = "";
    const hexes = Array.isArray(data.hexes) ? data.hexes : [];
    if (!hexes.length) {
        boardDiv.textContent = "Kartta latautuu...";
        return;
    }

    const size = boardZoom;
    const margin = size * 2;
    let minX = Number.POSITIVE_INFINITY;
    let minY = Number.POSITIVE_INFINITY;
    let maxX = Number.NEGATIVE_INFINITY;
    let maxY = Number.NEGATIVE_INFINITY;

    const positioned = hexes.map((hex) => {
        const p = axialToPixel(hex.q, hex.r, size);
        minX = Math.min(minX, p.x);
        minY = Math.min(minY, p.y);
        maxX = Math.max(maxX, p.x);
        maxY = Math.max(maxY, p.y);
        return { ...hex, px: p.x, py: p.y };
    });

    const width = maxX - minX + margin * 2;
    const height = maxY - minY + margin * 2;
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("class", "hex-map-svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("width", `${width}`);
    svg.setAttribute("height", `${height}`);

    positioned.forEach((hex) => {
        const cx = hex.px - minX + margin;
        const cy = hex.py - minY + margin;
        const g = document.createElementNS(svgNS, "g");
        const key = `${hex.q},${hex.r}`;
        g.setAttribute("class", `hex-tile biome-${hex.terrain}`);
        if (selectedHexKey === key) {
            g.classList.add("selected");
        }
        if (hex.highlight) {
            g.classList.add(`highlight-${hex.highlight}`);
        }
        g.dataset.key = key;
        g.dataset.q = String(hex.q);
        g.dataset.r = String(hex.r);

        const poly = document.createElementNS(svgNS, "polygon");
        poly.setAttribute("points", hexPoints(cx, cy, size));
        poly.setAttribute("class", "hex-shape");
        g.appendChild(poly);

        const icon = document.createElementNS(svgNS, "text");
        icon.setAttribute("x", String(cx));
        icon.setAttribute("y", String(cy + 6));
        icon.setAttribute("class", "terrain-icon");
        icon.setAttribute("text-anchor", "middle");
        icon.textContent = terrainIcons[hex.terrain] || "·";
        g.appendChild(icon);

        const factionMarker = hex.faction_marker;
        if (factionMarker) {
            const marker = document.createElementNS(svgNS, "text");
            marker.setAttribute("x", String(cx - size * 0.48));
            marker.setAttribute("y", String(cy - size * 0.35));
            marker.setAttribute("class", "faction-marker");
            marker.textContent = `${factionSigil[factionMarker.name] || "🏳️"} ${factionMarker.short}`;
            g.appendChild(marker);

            const nameLabel = document.createElementNS(svgNS, "text");
            nameLabel.setAttribute("x", String(cx));
            nameLabel.setAttribute("y", String(cy - size * 0.62));
            nameLabel.setAttribute("class", "faction-name-label");
            nameLabel.setAttribute("text-anchor", "middle");
            nameLabel.textContent = factionMarker.name;
            g.appendChild(nameLabel);
        }

        if (Array.isArray(hex.units)) {
            hex.units.forEach((unit, idx) => {
                const unitToken = document.createElementNS(svgNS, "g");
                unitToken.setAttribute("class", `unit-token ${unit.side === "player" ? "player" : "enemy"}`);
                const tokenX = cx - size * 0.32 + (idx % 2) * size * 0.34;
                const tokenY = cy + size * 0.22 + Math.floor(idx / 2) * size * 0.24;

                const circle = document.createElementNS(svgNS, "circle");
                circle.setAttribute("cx", String(tokenX));
                circle.setAttribute("cy", String(tokenY));
                circle.setAttribute("r", String(size * 0.17));
                circle.setAttribute("class", "unit-dot");
                unitToken.appendChild(circle);

                const text = document.createElementNS(svgNS, "text");
                text.setAttribute("x", String(tokenX));
                text.setAttribute("y", String(tokenY + 4));
                text.setAttribute("text-anchor", "middle");
                text.setAttribute("class", "unit-dot-label");
                text.textContent = unitSvg[unit.unit_key] || unit.token || "•";
                unitToken.appendChild(text);

                const title = document.createElementNS(svgNS, "title");
                title.textContent = `${unit.type} (${unit.faction}) HP ${unit.hp}/${unit.max_hp} | ATK ${unit.strength} | DEF ${unit.defense}`;
                unitToken.appendChild(title);
                g.appendChild(unitToken);
            });
        }

        const tileTitle = document.createElementNS(svgNS, "title");
        tileTitle.textContent = `Hex ${key} - ${hex.terrain}`;
        g.appendChild(tileTitle);
        g.addEventListener("click", () => {
            selectedHexKey = key;
            renderHexBoard(data);
        });

        svg.appendChild(g);
    });

    boardDiv.appendChild(svg);
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
    if (!container) {
        return;
    }
    container.innerHTML = "";
    if (!Array.isArray(factionsState) || factionsState.length === 0) {
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
        title.textContent = `${factionSigil[faction.name] || "🏳️"} ${faction.name}`;
        card.appendChild(title);

        const spawn = document.createElement("p");
        const spawnPos = faction.spawn_position || { x: "?", y: "?" };
        spawn.className = "faction-counter";
        spawn.textContent = `Aloitushex: (${spawnPos.x}, ${spawnPos.y}) | Yksiköt: ${faction.total_units}`;
        card.appendChild(spawn);

        const list = document.createElement("ul");
        list.className = "troop-list";
        Object.entries(faction.unit_counts || {}).forEach(([unitKey, count]) => {
            if (count <= 0) {
                return;
            }
            const meta = (window.lastUnitTypes && window.lastUnitTypes[unitKey]) || {};
            const li = document.createElement("li");
            li.innerHTML = `<span><span class="troop-token">${meta.token || unitSvg[unitKey] || "•"}</span>${meta.label || unitKey}</span><strong>×${count}</strong>`;
            list.appendChild(li);
        });
        card.appendChild(list);
        container.appendChild(card);
    });
}

function renderBattleView(battle) {
    const panel = document.getElementById("battle-view");
    const result = document.getElementById("battle-result");
    if (!panel || !result) {
        return;
    }
    const last = battle && battle.last ? battle.last : null;
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

    // quick battle animation cue
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

    boardZoom = Number(range.value || 34);
    value.textContent = `${boardZoom}px`;
    range.addEventListener("input", () => {
        boardZoom = Number(range.value || 34);
        value.textContent = `${boardZoom}px`;
        loadState();
    });
}

document.getElementById("faction-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    fetch("/start_game", {
        method: "POST",
        body: formData,
    })
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

loadState();
setupBoardZoom();