import unittest
from AdvancedCombatRules import calculate_damage

class TestAdvancedCombatRules(unittest.TestCase):
    def test_calculate_damage_basic(self):
        attacker = {'strength': 10}
        defender = {'defense': 5}
        self.assertEqual(calculate_damage(attacker, defender), 5)

    def test_calculate_damage_no_negative(self):
        attacker = {'strength': 3}
        defender = {'defense': 5}
        self.assertEqual(calculate_damage(attacker, defender), 0)

if __name__ == '__main__':
    unittest.main()