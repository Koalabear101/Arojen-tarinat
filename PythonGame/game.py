"""
Arojen-tarinat - Python version
A simple text-based strategy game
"""

from Factions import factions

def main():
    print("Tervetuloa Arojen-tarinoihin!")
    print("Valitse heimosi:")
    for i, faction in enumerate(factions, 1):
        print(f"{i}. {faction['name']} - {faction['bonus']}")

    choice = int(input("Valinta (1-4): ")) - 1
    player_faction = factions[choice]
    print(f"Valitsit: {player_faction['name']}")
    print(f"Aloitusyksiköt: {', '.join(player_faction['startUnits'])}")

    # Simple game loop
    turn = 1
    while True:
        print(f"\nVuoro {turn}")
        print("1. Liiku")
        print("2. Taistele")
        print("3. Lopeta")
        action = input("Toiminto: ")
        if action == "3":
            break
        elif action == "1":
            print("Liikut yksikköä")
        elif action == "2":
            print("Taistelet")
        turn += 1

    print("Peli päättyi!")

if __name__ == "__main__":
    main()