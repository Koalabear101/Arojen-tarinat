/**
 * Main application controller — ties API, Board, and UI together.
 */
(function () {
    let gameState = null;
    let selectedFaction = null;
    let interactionMode = null; // "move_select_target", "attack_select_target", "heal_select", "recruit_select"
    let sourceCell = null;

    // ── Setup screen ──────────────────────────────────────
    document.querySelectorAll(".faction-card").forEach(card => {
        card.addEventListener("click", () => {
            document.querySelectorAll(".faction-card").forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
            selectedFaction = parseInt(card.dataset.index, 10);
            document.getElementById("start-btn").disabled = false;
        });
    });

    document.getElementById("start-btn").addEventListener("click", async () => {
        if (selectedFaction === null) return;
        const result = await GameAPI.startGame(selectedFaction);
        if (result.success) {
            document.getElementById("setup-screen").style.display = "none";
            document.getElementById("game-screen").style.display = "block";
            await refreshState();
        }
    });

    // ── Help modal ────────────────────────────────────────
    document.getElementById("help-btn").addEventListener("click", () => UI.showModal("help-modal"));
    document.getElementById("help-close").addEventListener("click", () => UI.hideModal("help-modal"));
    document.getElementById("help-modal").addEventListener("click", (e) => {
        if (e.target === e.currentTarget) UI.hideModal("help-modal");
    });

    // ── New game button ───────────────────────────────────
    document.getElementById("new-game-btn").addEventListener("click", () => {
        UI.hideModal("victory-modal");
        document.getElementById("game-screen").style.display = "none";
        document.getElementById("setup-screen").style.display = "flex";
        gameState = null;
        interactionMode = null;
        sourceCell = null;
    });

    // ── Board click handling ──────────────────────────────
    BoardRenderer.onCellClick = (x, y, cellData) => {
        if (!gameState || gameState.game_over) return;

        const playerId = gameState.player_faction.id;

        if (interactionMode === "move_select_target" && sourceCell) {
            performAction("move", {
                from_x: sourceCell.x, from_y: sourceCell.y,
                to_x: x, to_y: y,
            });
            interactionMode = null;
            sourceCell = null;
            return;
        }

        if (interactionMode === "attack_select_target" && sourceCell) {
            performAction("attack", {
                attacker_x: sourceCell.x, attacker_y: sourceCell.y,
                target_x: x, target_y: y,
            });
            BoardRenderer.flashCell(x, y);
            interactionMode = null;
            sourceCell = null;
            return;
        }

        if (interactionMode === "heal_select" && cellData && cellData.faction_id === playerId) {
            performAction("heal", { x, y });
            interactionMode = null;
            return;
        }

        if (interactionMode === "recruit_select") {
            if (!cellData) {
                const unitType = prompt("Yksikkötyyppi (warrior/cavalry/archer):");
                if (unitType) {
                    performAction("recruit", { unit_type: unitType, x, y });
                }
            }
            interactionMode = null;
            return;
        }

        // Default: select unit, show info
        if (cellData) {
            BoardRenderer.setSelected(x, y);
            UI.showUnitInfo(cellData);
            sourceCell = { x, y };
            rerender();
        } else {
            BoardRenderer.clearSelection();
            UI.hideUnitInfo();
            sourceCell = null;
            rerender();
        }
    };

    // ── Action handling ───────────────────────────────────
    function handleAction(action) {
        switch (action) {
            case "move":
                if (!sourceCell) {
                    alert("Valitse ensin yksikkö laudalta.");
                    return;
                }
                interactionMode = "move_select_target";
                break;
            case "attack":
                if (!sourceCell) {
                    alert("Valitse ensin hyökkäävä yksikkö laudalta.");
                    return;
                }
                interactionMode = "attack_select_target";
                break;
            case "heal":
                interactionMode = "heal_select";
                break;
            case "recruit":
                interactionMode = "recruit_select";
                break;
            case "diplomacy":
            case "collect":
            case "end_phase":
                performAction(action);
                break;
        }
    }

    async function performAction(action, params = {}) {
        const result = await GameAPI.performAction(action, params);
        if (result.success === false) {
            alert(result.error || "Toiminto epäonnistui.");
        }
        await refreshState();
    }

    // ── State refresh ─────────────────────────────────────
    async function refreshState() {
        const state = await GameAPI.getState();
        if (state.error) return;
        gameState = state;

        UI.updateHeader(state);
        UI.renderActions(state.allowed_actions, handleAction);

        if (state.events) {
            document.getElementById("event-log").innerHTML = "";
            state.events.forEach(ev => UI.addEvent(ev));
        }

        rerender();

        if (state.victory_check && state.victory_check.game_over) {
            setTimeout(() => {
                UI.showVictory(state.victory_check.winner, state.player_faction.id);
            }, 500);
        }
    }

    function rerender() {
        if (!gameState) return;
        BoardRenderer.render(gameState.board, gameState.player_faction.id);
    }
})();
