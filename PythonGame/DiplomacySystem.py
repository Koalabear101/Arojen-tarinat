# DiplomacySystem.py
# Python implementation for diplomacy system

class DiplomacySystem:
    """
    Manages diplomatic relations between factions.
    """
    def __init__(self):
        """
        Initializes the diplomacy system.
        """
        self.relations = {}

    def set_relation(self, faction1, faction2, relation):
        """
        Sets the relation value between two factions.

        Args:
            faction1 (str): The first faction.
            faction2 (str): The second faction.
            relation (int): The relation value.
        """
        if faction1 not in self.relations:
            self.relations[faction1] = {}
        self.relations[faction1][faction2] = relation

    def get_relation(self, faction1, faction2):
        """
        Gets the relation value between two factions.

        Args:
            faction1 (str): The first faction.
            faction2 (str): The second faction.

        Returns:
            int: The relation value, default 0.
        """
        return self.relations.get(faction1, {}).get(faction2, 0)

if __name__ == "__main__":
    print("Diplomacy System loaded")