const resourceLabels = {
    horses: "Hevoset",
    gold: "Kulta",
    food: "Ruoka",
    artisans: "Käsityöläiset",
    cattle: "Karja",
};

const victoryLabels = {
    military: "Sotilaallinen",
    economic: "Taloudellinen",
    cultural: "Kulttuurinen",
    technology: "Teknologinen",
};

function renderState(data) {
    document.getElementById("turn").textContent = data.turn;
    document.getElementById("phase").textContent = data.phase;
    document.getElementById("focus").textContent = data.focus;
    document.getElementById("player-faction").textContent = data.faction;
    document.getElementById("messages").textContent = data.message || "";

    renderBoard(data.board, data.faction);
    renderResources(data.resources);
    renderVictoryProgress(data.victory_progress, data.victory_goals, data.winner);
    renderControls(data.available_actions, data.action_labels, data.winner);
}

function renderBoard(boardData, playerFaction) {
    const boardDiv = document.getElementById("board");
    boardDiv.innerHTML = "";

    boardData.forEach((row) => {
        row.forEach((cell) => {
            const cellDiv = document.createElement("div");
            cellDiv.className = "cell";

            if (cell) {
                cellDiv.textContent = cell.faction[0];
                if (cell.faction === playerFaction) {
                    cellDiv.classList.add("player");
                } else {
                    cellDiv.classList.add("enemy");
                }
            } else {
                cellDiv.classList.add("empty");
            }

            boardDiv.appendChild(cellDiv);
        });
    });
}

function renderResources(resources) {
    const resourcesList = document.getElementById("resources");
    resourcesList.innerHTML = "";
    Object.keys(resourceLabels).forEach((key) => {
        const li = document.createElement("li");
        li.textContent = `${resourceLabels[key]}: ${resources[key] ?? 0}`;
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
        li.textContent = `${victoryLabels[key]}: ${current}/${target}`;
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
            renderState(data);
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
                renderState(data);
            }
        });
});

loadState();