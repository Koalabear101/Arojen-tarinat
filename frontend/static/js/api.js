/**
 * API communication layer.
 */
const GameAPI = {
    async startGame(factionIndex) {
        const res = await fetch("/api/start_game", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ faction: factionIndex }),
        });
        return res.json();
    },

    async getState() {
        const res = await fetch("/api/state");
        return res.json();
    },

    async performAction(action, params = {}) {
        const res = await fetch("/api/action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action, ...params }),
        });
        return res.json();
    },

    async getHighlights(x, y) {
        const res = await fetch(`/api/highlights?x=${x}&y=${y}`);
        return res.json();
    },
};
