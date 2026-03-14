// DiplomacySystem.js
// JavaScript implementation for diplomacy system

/**
 * Manages diplomatic relations between factions.
 */
class DiplomacySystem {
    /**
     * Creates a new diplomacy system.
     */
    constructor() {
        this.relations = {};
    }

    /**
     * Sets the relation value between two factions.
     * @param {string} faction1 - The first faction.
     * @param {string} faction2 - The second faction.
     * @param {number} relation - The relation value.
     */
    setRelation(faction1, faction2, relation) {
        if (!this.relations[faction1]) {
            this.relations[faction1] = {};
        }
        this.relations[faction1][faction2] = relation;
    }

    /**
     * Gets the relation value between two factions.
     * @param {string} faction1 - The first faction.
     * @param {string} faction2 - The second faction.
     * @returns {number} The relation value, default 0.
     */
    getRelation(faction1, faction2) {
        return this.relations[faction1]?.[faction2] || 0;
    }
}

module.exports = { DiplomacySystem };

console.log("Diplomacy System loaded");