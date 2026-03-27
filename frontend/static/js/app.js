/**
 * Main application controller — ties API, Board, and UI together.
 */
(function () {
    let gameState = null;
    let selectedFaction = null;
    let interactionMode = null;
    let sourceCell = null;
    let lastPhase = null;

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
        lastPhase = null;
    });

    // ── Board click handling ──────────────────────────────
    BoardRenderer.onCellClick = async (x, y, cellData) => {
        if (!gameState || gameState.game_over) return;

        const playerId = gameState.player_faction.id;

        // Target selection for move
        if (interactionMode === "move_select_target" && sourceCell) {
            await performAction("move", {
                from_x: sourceCell.x, from_y: sourceCell.y,
                to_x: x, to_y: y,
            });
            clearInteraction();
            return;
        }

        // Target selection for attack
        if (interactionMode === "attack_select_target" && sourceCell) {
            const result = await GameAPI.performAction("attack", {
                attacker_x: sourceCell.x, attacker_y: sourceCell.y,
                target_x: x, target_y: y,
            });
            if (result.success) {
                BoardRenderer.flashCell(x, y, "damage-flash");
                BoardRenderer.showFloatingText(x, y, `-${result.damage}`, "#ff4444");
                if (result.destroyed) {
                    BoardRenderer.showFloatingText(x, y, "💀", "#ff0000");
                }
            } else {
                UI.showStatusMessage(result.error || "Hyökkäys epäonnistui.");
            }
            clearInteraction();
            await refreshState();
            return;
        }

        // Heal selection
        if (interactionMode === "heal_select" && cellData && cellData.faction_id === playerId) {
            await performAction("heal", { x, y });
            clearInteraction();
            return;
        }

        // Recruit selection
        if (interactionMode === "recruit_select") {
            if (!cellData) {
                const unitType = prompt("Yksikkötyyppi (warrior / cavalry / archer):");
                if (unitType) {
                    await performAction("recruit", { unit_type: unitType.trim().toLowerCase(), x, y });
                }
            } else {
                UI.showStatusMessage("Ruutu on varattu. Valitse tyhjä ruutu.");
            }
            clearInteraction();
            return;
        }

        // Default: select a unit and fetch its highlights
        if (cellData && cellData.faction_id === playerId) {
            BoardRenderer.setSelected(x, y);
            sourceCell = { x, y };
            UI.showUnitInfo(cellData);

            const highlights = await GameAPI.getHighlights(x, y);
            BoardRenderer.setHighlights(highlights.move, highlights.attack);
            rerender();
        } else {
            clearInteraction();
            UI.hideUnitInfo();
            rerender();
        }
    };

    function clearInteraction() {
        interactionMode = null;
        sourceCell = null;
        BoardRenderer.clearSelection();
    }

    // ── Action handling ───────────────────────────────────
    function handleAction(action) {
        switch (action) {
            case "move":
                if (!sourceCell) {
                    UI.showStatusMessage("Valitse ensin yksikkö laudalta.");
                    return;
                }
                interactionMode = "move_select_target";
                UI.showStatusMessage("Valitse kohderuutu siirrolle.");
                break;
            case "attack":
                if (!sourceCell) {
                    UI.showStatusMessage("Valitse ensin hyökkäävä yksikkö.");
                    return;
                }
                interactionMode = "attack_select_target";
                UI.showStatusMessage("Valitse kohde hyökkäykselle.");
                break;
            case "heal":
                interactionMode = "heal_select";
                UI.showStatusMessage("Valitse parannettava yksikkö.");
                break;
            case "recruit":
                interactionMode = "recruit_select";
                UI.showStatusMessage("Valitse tyhjä ruutu uudelle yksikölle.");
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
            UI.showStatusMessage(result.error || "Toiminto epäonnistui.");
        }
        await refreshState();
    }

    // ── State refresh ─────────────────────────────────────
    async function refreshState() {
        const state = await GameAPI.getState();
        if (state.error) return;
        gameState = state;

        UI.updateHeader(state);
        UI.updatePhaseBar(state.phase);
        UI.renderActions(state.allowed_actions, handleAction);
        UI.renderFactionAbility(state.player_faction);
        UI.renderVictoryProgress(state);

        // Phase transition banner
        if (lastPhase !== null && lastPhase !== state.phase) {
            UI.showPhaseBanner(state.phase_label);
        }
        lastPhase = state.phase;

        if (state.events) {
            document.getElementById("event-log").innerHTML = "";
            state.events.forEach(ev => UI.addEvent(ev));
        }

        rerender();

        if (state.victory_check && state.victory_check.game_over) {
            setTimeout(() => {
                UI.showVictory(
                    state.victory_check.winner,
                    state.player_faction.id,
                    state.victory_check.type,
                );
            }, 500);
        }
    }

    function rerender() {
        if (!gameState) return;
        BoardRenderer.render(gameState.board, gameState.player_faction.id);
    }
})();
