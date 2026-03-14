// AdvancedCombatRules.js
// Basic JavaScript implementation for advanced combat rules

/**
 * Calculates the damage dealt from attacker to defender.
 * @param {Object} attacker - The attacking unit with strength property.
 * @param {Object} defender - The defending unit with defense property.
 * @returns {number} The calculated damage, minimum 0.
 */
function calculateDamage(attacker, defender) {
    // Simple damage calculation: strength minus defense
    let damage = attacker.strength - defender.defense;
    return Math.max(0, damage);
}

module.exports = { calculateDamage };

console.log("Advanced Combat Rules loaded");