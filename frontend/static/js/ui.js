/**
 * UI updates — phase bar, stats, panels, modals, event log.
 */
const UI = {
    updateHeader(state) {
        document.getElementById("turn-display").textContent = state.turn;
        document.getElementById("max-turn-display").textContent = `/ ${state.max_turns}`;

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

    updatePhaseBar(currentPhase) {
        PHASE_ORDER.forEach((phase, idx) => {
            const el = document.getElementById(`phase-step-${phase}`);
            if (!el) return;
            el.classList.remove("active", "completed");
            const currentIdx = PHASE_ORDER.indexOf(currentPhase);
            if (idx < currentIdx) el.classList.add("completed");
            if (idx === currentIdx) el.classList.add("active");
        });
        const label = document.getElementById("phase-label");
        const desc = document.getElementById("phase-desc");
        if (label) label.textContent = `${PHASE_ICONS[currentPhase] || ""} ${PHASE_LABELS[currentPhase] || currentPhase}`;
        if (desc && PHASE_ORDER.includes(currentPhase)) {
            const descriptions = {
                movement: "Siirrä yksiköitäsi laudalla.",
                combat: "Hyökkää vihollisyksiköitä vastaan.",
                diplomacy: "Neuvottele muiden heimojen kanssa.",
                resource: "Kerää resursseja ja paranna yksiköitä.",
            };
            desc.textContent = descriptions[currentPhase] || "";
        }
    },

    showPhaseBanner(phaseLabel) {
        const banner = document.getElementById("phase-banner");
        if (!banner) return;
        banner.textContent = phaseLabel;
        banner.classList.add("visible");
        setTimeout(() => banner.classList.remove("visible"), 1400);
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
            btn.title = config.hint || "";
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
            ${unit.has_acted ? '<div class="unit-acted-badge">Toiminut</div>' : ""}
        `;
    },

    hideUnitInfo() {
        document.getElementById("unit-info").style.display = "none";
    },

    renderFactionAbility(faction) {
        const el = document.getElementById("faction-ability");
        if (!el || !faction) return;
        el.style.display = "block";
        el.innerHTML = `
            <div class="ability-header" style="border-left: 3px solid ${faction.color}; padding-left: 0.6rem;">
                <strong>${faction.passive_name || ""}</strong>
            </div>
            <div class="ability-desc">${faction.passive_description || faction.bonus}</div>
        `;
    },

    addEvent(event) {
        const log = document.getElementById("event-log");
        const entry = document.createElement("div");
        entry.className = "event-entry";
        const icon = EVENT_ICONS[event.type] || "📌";
        entry.innerHTML = `<span class="event-icon">${icon}</span><span class="event-turn">V${event.turn}</span> ${event.message}`;
        log.prepend(entry);
        while (log.children.length > 30) {
            log.removeChild(log.lastChild);
        }
    },

    showVictory(winner, playerFactionId, victoryType) {
        const modal = document.getElementById("victory-modal");
        const isWin = winner === playerFactionId;

        document.getElementById("victory-icon").textContent = isWin ? "🏆" : "💀";
        document.getElementById("victory-title").textContent = isWin ? "Voitto!" : "Tappio!";

        const typeLabels = {
            military: isWin ? "Sotilaallinen voitto! Kaikki viholliset tuhottu." : "Yksikösi tuhottiin.",
            diplomacy: "Diplomaattinen voitto! Liittolaisuus saavutettu.",
            attrition: isWin ? "Voitto vuororajalla! Enemmän yksiköitä." : "Tappio vuororajalla.",
        };
        document.getElementById("victory-message").textContent =
            typeLabels[victoryType] || (isWin ? "Olet voittanut!" : "Olet hävinnyt.");

        modal.style.display = "flex";
    },

    showModal(id) { document.getElementById(id).style.display = "flex"; },
    hideModal(id) { document.getElementById(id).style.display = "none"; },

    showStatusMessage(text) {
        const bar = document.getElementById("status-bar");
        if (!bar) return;
        bar.textContent = text;
        bar.classList.add("visible");
        setTimeout(() => bar.classList.remove("visible"), 2500);
    },
};
