/**
 * Board rendering — tooltips, selection, move/attack highlights.
 */
const BoardRenderer = {
    selectedCell: null,
    moveTargets: [],
    attackTargets: [],
    onCellClick: null,
    _tooltip: null,

    render(boardData, playerFactionId) {
        const boardEl = document.getElementById("board");
        boardEl.innerHTML = "";

        boardData.forEach((row, y) => {
            row.forEach((cell, x) => {
                const div = document.createElement("div");
                div.className = "cell";
                div.dataset.x = x;
                div.dataset.y = y;

                if (cell) {
                    const icon = UNIT_ICONS[cell.type] || "?";
                    const hpPct = Math.round((cell.hp / cell.max_hp) * 100);
                    const hpClass = hpPct > 60 ? "healthy" : hpPct > 30 ? "wounded" : "critical";
                    div.innerHTML =
                        `<span class="unit-icon">${icon}</span>` +
                        `<div class="cell-hp-bar"><div class="cell-hp-fill ${hpClass}" style="width:${hpPct}%"></div></div>`;

                    if (cell.faction_id === playerFactionId) {
                        div.classList.add("player-unit");
                        if (cell.has_acted) div.classList.add("acted");
                    } else {
                        div.classList.add("enemy-unit");
                    }
                }

                if (this.selectedCell && this.selectedCell.x === x && this.selectedCell.y === y) {
                    div.classList.add("selected");
                }

                if (this._isInList(x, y, this.moveTargets)) {
                    div.classList.add("highlight-move");
                }
                if (this._isInList(x, y, this.attackTargets)) {
                    div.classList.add("highlight-attack");
                }

                div.addEventListener("click", () => this._handleClick(x, y, cell));

                if (cell) {
                    div.addEventListener("mouseenter", (e) => this._showTooltip(e, cell));
                    div.addEventListener("mouseleave", () => this._hideTooltip());
                }

                boardEl.appendChild(div);
            });
        });
    },

    _handleClick(x, y, cellData) {
        if (this.onCellClick) {
            this.onCellClick(x, y, cellData);
        }
    },

    _isInList(x, y, list) {
        return list.some(([cx, cy]) => cx === x && cy === y);
    },

    setSelected(x, y) {
        this.selectedCell = { x, y };
    },

    clearSelection() {
        this.selectedCell = null;
        this.moveTargets = [];
        this.attackTargets = [];
    },

    setHighlights(moveTargets, attackTargets) {
        this.moveTargets = moveTargets || [];
        this.attackTargets = attackTargets || [];
    },

    flashCell(x, y, className = "damage-flash") {
        const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
        if (cell) {
            cell.classList.add(className);
            setTimeout(() => cell.classList.remove(className), 400);
        }
    },

    showFloatingText(x, y, text, color = "#fff") {
        const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
        if (!cell) return;
        const span = document.createElement("span");
        span.className = "floating-text";
        span.textContent = text;
        span.style.color = color;
        cell.appendChild(span);
        setTimeout(() => span.remove(), 900);
    },

    _showTooltip(event, cell) {
        this._hideTooltip();
        const label = UNIT_LABELS[cell.type] || cell.type;
        const tt = document.createElement("div");
        tt.className = "board-tooltip";
        tt.innerHTML =
            `<strong>${label}</strong><br>` +
            `HP: ${cell.hp}/${cell.max_hp}<br>` +
            `⚔ ${cell.strength} &nbsp; 🛡 ${cell.defense}<br>` +
            `🏃 ${cell.speed} &nbsp; 🎯 ${cell.range}`;
        document.body.appendChild(tt);
        const rect = event.target.closest(".cell").getBoundingClientRect();
        tt.style.left = rect.left + rect.width / 2 + "px";
        tt.style.top = rect.top - 4 + "px";
        this._tooltip = tt;
    },

    _hideTooltip() {
        if (this._tooltip) {
            this._tooltip.remove();
            this._tooltip = null;
        }
    },
};
