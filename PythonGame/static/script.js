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

const biomeTypes = ["steppe", "forest", "hills", "mountain", "river", "lake"];
const biomeIcons = {
    steppe: "·",
    forest: "🌲",
    hills: "⛰",
    mountain: "▲",
    river: "≈",
    lake: "◉",
};

let boardZoom = 30;

function biomeForHex(rowIndex, colIndex) {
    const value = (rowIndex * 7 + colIndex * 11 + rowIndex * colIndex) % biomeTypes.length;
    return biomeTypes[value];
}

function renderState(data) {
    document.getElementById("turn").textContent = data.turn;
    document.getElementById("phase").textContent = data.phase;
    document.getElementById("focus").textContent = data.focus;
    document.getElementById("player-faction").textContent = data.faction;
    document.getElementById("messages").textContent = data.message || "";

    renderBoard(data.board, data.faction);
    renderResources(data.resources);
    renderVictoryProgress(data.victory_progress, data.victory_goals, data.winner);
    renderFactionTokens(data.factions_state || {});
    renderBattleView(data.battle);
    renderControls(data.available_actions, data.action_labels, data.winner);
}

function renderBoard(boardData, playerFaction) {
    const boardDiv = document.getElementById("board");
    boardDiv.innerHTML = "";

    const boardRows = boardData.length;
    const boardCols = boardData[0]?.length ?? 0;
    const visibleRows = Math.max(18, boardRows + 8);
    const visibleCols = Math.max(24, boardCols + 14);

    boardDiv.style.setProperty("--hex-rows", String(visibleRows));
    boardDiv.style.setProperty("--hex-cols", String(visibleCols));
    boardDiv.style.setProperty("--hex-size", `${boardZoom}px`);

    for (let rowIndex = 0; rowIndex < visibleRows; rowIndex += 1) {
        for (let colIndex = 0; colIndex < visibleCols; colIndex += 1) {
            const cell = boardData[rowIndex]?.[colIndex] ?? null;
            const biome = biomeForHex(rowIndex, colIndex);
            const cellDiv = document.createElement("div");
            cellDiv.className = `hex biome-${biome}`;
            cellDiv.dataset.odd = rowIndex % 2 === 1 ? "true" : "false";

            if (cell) {
                const label = document.createElement("span");
                label.className = "hex-label";
                label.textContent = cell.faction[0];
                cellDiv.appendChild(label);
                if (cell.faction === playerFaction) {
                    cellDiv.classList.add("player-unit");
                } else {
                    cellDiv.classList.add("enemy-unit");
                }
            } else {
                const icon = document.createElement("span");
                icon.className = "hex-icon";
                icon.textContent = biomeIcons[biome] ?? "·";
                cellDiv.appendChild(icon);
            }

            boardDiv.appendChild(cellDiv);
        }
    }
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
    const container = document.getElementById("faction-tokens");
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
        card.className = `faction-token-card ${faction.is_player ? "player-faction" : ""}`;

        const title = document.createElement("h4");
        title.textContent = faction.name;
        card.appendChild(title);

        const counter = document.createElement("p");
        counter.className = "faction-counter";
        counter.textContent = `Yksiköt: ${faction.total_units}`;
        card.appendChild(counter);

        const units = document.createElement("div");
        units.className = "faction-units";
        Object.entries(faction.unit_counts || {}).forEach(([unitKey, count]) => {
            if (count <= 0) {
                return;
            }
            const unitMeta = (window.lastUnitTypes && window.lastUnitTypes[unitKey]) || {};
            const span = document.createElement("span");
            span.className = "unit-pill alive";
            span.textContent = `${unitMeta.token || "•"} ${unitMeta.label || unitKey} ×${count}`;
            span.title = `${unitMeta.label || unitKey}: ${count} kpl`;
            units.appendChild(span);
        });
        card.appendChild(units);

        container.appendChild(card);
    });
}

function renderBattleView(battle) {
    const panel = document.getElementById("battle-panel");
    const result = document.getElementById("battle-result");
    if (!panel || !result) {
        return;
    }
    const last = battle && battle.last ? battle.last : null;
    if (!last) {
        panel.style.display = "none";
        result.textContent = "Taistelua ei vielä käyty.";
        return;
    }
    panel.style.display = "grid";

    document.getElementById("battle-attacker-name").textContent = last.attacker_faction;
    document.getElementById("battle-attacker-unit").textContent = `${last.attacker_unit}`;
    document.getElementById("battle-attacker-power").textContent = last.attack_total;
    document.getElementById("battle-attack-die").textContent = last.attack_die;

    document.getElementById("battle-defender-name").textContent = last.defender_faction;
    document.getElementById("battle-defender-unit").textContent = `${last.defender_unit}`;
    document.getElementById("battle-defender-power").textContent = last.defense_total;
    document.getElementById("battle-defense-die").textContent = last.defense_die;

    document.getElementById("battle-damage").textContent = last.damage_to_defender;
    document.getElementById("battle-defense-after").textContent = `Vastahyökkäysvahinko hyökkääjälle: ${last.damage_to_attacker}`;
    result.textContent = `Tulos: ${last.outcome}`;
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

    boardZoom = Number(range.value || 30);
    value.textContent = `${boardZoom}px`;
    range.addEventListener("input", () => {
        boardZoom = Number(range.value || 30);
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