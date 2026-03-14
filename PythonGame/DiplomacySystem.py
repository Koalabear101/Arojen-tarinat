# DiplomacySystem.py
# Python implementation for diplomacy system

class DiplomacySystem:
    def __init__(self):
        self.relations = {}

    def set_relation(self, faction1, faction2, relation):
        if faction1 not in self.relations:
            self.relations[faction1] = {}
        self.relations[faction1][faction2] = relation

    def get_relation(self, faction1, faction2):
        return self.relations.get(faction1, {}).get(faction2, 0)

if __name__ == "__main__":
    print("Diplomacy System loaded")