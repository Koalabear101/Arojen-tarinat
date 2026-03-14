// DiplomacySystem.js
// JavaScript implementation for diplomacy system

class DiplomacySystem {
    constructor() {
        this.relations = {};
    }

    setRelation(faction1, faction2, relation) {
        if (!this.relations[faction1]) {
            this.relations[faction1] = {};
        }
        this.relations[faction1][faction2] = relation;
    }

    getRelation(faction1, faction2) {
        return this.relations[faction1]?.[faction2] || 0;
    }
}

console.log("Diplomacy System loaded");