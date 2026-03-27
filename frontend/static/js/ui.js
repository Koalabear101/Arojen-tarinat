/**
 * UI updates — stats, panels, modals, event log.
 */
const UI = {
    updateHeader(state) {
        document.getElementById("turn-display").textContent = state.turn;
        document.getElementById("max-turn-display").textContent = `/ ${state.max_turns}`;

        const phaseIcon = PHASE_ICONS[state.phase] || "";
        document.getElementById("phase-label").textContent = `${phaseIcon} ${state.phase_label}`;
        document.getElementById("phase-desc").textContent = state.phase_description;

        if (state.player_faction) {
            const badge = document.getElementById("player-badge");
            badge.textContent = state.player_faction.name;
            badge.style.background = state.player_faction.color;

            const fid = state.player_faction.id;
            document.getElementById("resources-display").textContent = state.resources[fid] || 0;

            const relKey = `${fid}:${state.enemy_faction ? state.enemy_faction.id : ""}`;
            document.getElementById("diplomacy-display").textContent = state.diplomacy[relKey] || 0;
        }
    },

    renderActions(allowedActions, onAction) {
        const container = document.getElementById("action-buttons");
        container.innerHTML = "";

        allowedActions.forEach(action => {
            const config = ACTION_CONFIG[action];
            if (!config) return;

            const btn = document.createElement("button");
            btn.className = `btn btn-action ${config.style}`;
            btn.innerHTML = `<span class="action-icon">${config.icon}</span> ${config.label}`;
            btn.addEventListener("click", () => onAction(action));
            container.appendChild(btn);
        });
    },

    showUnitInfo(unit) {
        const panel = document.getElementById("unit-info");
        panel.style.display = "block";
        const details = document.getElementById("unit-details");
        const label = UNIT_LABELS[unit.type] || unit.type;
        const hpPct = Math.round((unit.hp / unit.max_hp) * 100);
        const hpClass = hpPct > 60 ? "healthy" : hpPct > 30 ? "wounded" : "critical";

        details.innerHTML = `
            <div style="text-align:center;font-size:2rem;margin-bottom:0.5rem">${UNIT_ICONS[unit.type] || "?"}</div>
            <div class="unit-stat"><span class="label">Tyyppi</span><span>${label}</span></div>
            <div class="unit-stat"><span class="label">Voima</span><span>${unit.strength}</span></div>
            <div class="unit-stat"><span class="label">Puolustus</span><span>${unit.defense}</span></div>
            <div class="unit-stat"><span class="label">Nopeus</span><span>${unit.speed}</span></div>
            <div class="unit-stat"><span class="label">Kantama</span><span>${unit.range}</span></div>
            <div class="unit-stat"><span class="label">HP</span><span>${unit.hp} / ${unit.max_hp}</span></div>
            <div class="hp-bar"><div class="hp-fill ${hpClass}" style="width:${hpPct}%"></div></div>
        `;
    },

    hideUnitInfo() {
        document.getElementById("unit-info").style.display = "none";
    },

    addEvent(event) {
        const log = document.getElementById("event-log");
        const entry = document.createElement("div");
        entry.className = "event-entry";
        entry.innerHTML = `<span class="event-turn">V${event.turn}</span> ${event.message}`;
        log.prepend(entry);

        while (log.children.length > 20) {
            log.removeChild(log.lastChild);
        }
    },

    showVictory(winner, playerFactionId) {
        const modal = document.getElementById("victory-modal");
        const isWin = winner === playerFactionId;

        document.getElementById("victory-icon").textContent = isWin ? "🏆" : "💀";
        document.getElementById("victory-title").textContent = isWin ? "Voitto!" : "Tappio!";
        document.getElementById("victory-message").textContent = isWin
            ? "Olet saavuttanut voiton! Heimosi hallitsee aroja."
            : "Heimosi on kukistettu. Yritä uudelleen!";

        modal.style.display = "flex";
    },

    showModal(id) { document.getElementById(id).style.display = "flex"; },
    hideModal(id) { document.getElementById(id).style.display = "none"; },
};
