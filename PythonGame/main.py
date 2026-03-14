# main.py
# Main game script for Arojen-tarinat

from GameBoard import GameBoard
from AdvancedCombatRules import calculate_damage
from DiplomacySystem import DiplomacySystem
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Game'))
from Factions import factions

def main():
    print("Tervetuloa Arojen-tarinoihin!")
    print("Strategiapeli heimojen välisestä taistelusta.\n")

    # Valitse heimot
    print("Saatavilla olevat heimot:")
    for i, faction in enumerate(factions, 1):
        print(f"{i}. {faction['name']} - {faction['bonus']}")
    faction_choice = int(input("Valitse heimosi numero: ")) - 1
    player_faction = factions[faction_choice]
    print(f"Valitsit: {player_faction['name']}\n")

    # Alusta pelilauta
    board = GameBoard(10, 10)
    diplomacy = DiplomacySystem()

    # Lisää aloitusyksiköitä (yksinkertaistettu)
    board.place_unit(0, 0, {'type': 'warrior', 'strength': 10, 'defense': 5, 'faction': player_faction['name']})
    board.place_unit(9, 9, {'type': 'warrior', 'strength': 8, 'defense': 6, 'faction': 'Vihollinen'})

    print("Pelilauta alustettu. Aloitusyksiköt sijoitettu.\n")

    # Simuloi yksinkertainen kierros
    while True:
        print("Nykyinen lauta:")
        for y in range(board.height):
            row = []
            for x in range(board.width):
                unit = board.board[y][x]
                if unit:
                    row.append(f"{unit['faction'][0]}")
                else:
                    row.append(".")
            print(" ".join(row))

        action = input("\nValitse toiminto: (move, attack, diplomacy, quit): ").lower()
        if action == 'quit':
            break
        elif action == 'attack':
            # Yksinkertainen hyökkäys
            attacker = board.board[0][0]
            defender = board.board[9][9]
            if attacker and defender:
                damage = calculate_damage(attacker, defender)
                defender['defense'] -= damage
                print(f"Hyökkäys aiheutti {damage} vahinkoa!")
                if defender['defense'] <= 0:
                    print("Vihollinen tuhottu!")
                    board.board[9][9] = None
            else:
                print("Ei kelvollisia yksiköitä hyökkäykseen.")
        elif action == 'diplomacy':
            relation = diplomacy.get_relation(player_faction['name'], 'Vihollinen')
            print(f"Nykyinen suhde viholliseen: {relation}")
            # Yksinkertainen diplomacy
            diplomacy.set_relation(player_faction['name'], 'Vihollinen', relation + 10)
            print("Diplomatia paransi suhteita!")
        else:
            print("Tuntematon toiminto.")

    print("Kiitos pelaamisesta!")

if __name__ == "__main__":
    main()