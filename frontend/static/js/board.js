/**
 * Board rendering and cell interaction.
 */
const BoardRenderer = {
    selectedCell: null,
    onCellClick: null,

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
                    div.innerHTML = `<span class="unit-icon">${icon}</span><span class="unit-hp">${cell.hp}</span>`;

                    if (cell.faction_id === playerFactionId) {
                        div.classList.add("player-unit");
                    } else {
                        div.classList.add("enemy-unit");
                    }
                }

                if (this.selectedCell && this.selectedCell.x === x && this.selectedCell.y === y) {
                    div.classList.add("selected");
                }

                div.addEventListener("click", () => this._handleClick(x, y, cell));
                boardEl.appendChild(div);
            });
        });
    },

    _handleClick(x, y, cellData) {
        if (this.onCellClick) {
            this.onCellClick(x, y, cellData);
        }
    },

    setSelected(x, y) {
        this.selectedCell = { x, y };
    },

    clearSelection() {
        this.selectedCell = null;
    },

    highlightCells(coords, className) {
        coords.forEach(([cx, cy]) => {
            const cell = document.querySelector(`.cell[data-x="${cx}"][data-y="${cy}"]`);
            if (cell) cell.classList.add(className);
        });
    },

    flashCell(x, y) {
        const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
        if (cell) {
            cell.classList.add("damage-flash");
            setTimeout(() => cell.classList.remove("damage-flash"), 300);
        }
    },
};
