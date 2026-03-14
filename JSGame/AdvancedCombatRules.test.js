const { calculateDamage } = require('./AdvancedCombatRules');

test('calculateDamage basic', () => {
  const attacker = { strength: 10 };
  const defender = { defense: 5 };
  expect(calculateDamage(attacker, defender)).toBe(5);
});

test('calculateDamage no negative', () => {
  const attacker = { strength: 3 };
  const defender = { defense: 5 };
  expect(calculateDamage(attacker, defender)).toBe(0);
});