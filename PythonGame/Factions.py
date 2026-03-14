"""
Factions.py — Heimojen yleiskatsaus

Näyttää 4 heimon perustiedot: nimi, bonus ja alkuasetelma.
Tiivistetympi versio kuin DetailedFactions.
"""

factions = [
    {
        "name": "Mongoli-heimo",
        "color": "amber",
        "bonus": "Ratsuväen bonus, nopea liikkeelläolo",
        "startUnits": ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
    },
    {
        "name": "Kiinan dynastia",
        "color": "red",
        "bonus": "Linnoitukset, teknologia-edistykset",
        "startUnits": ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
    },
    {
        "name": "Persialainen valtakunta",
        "color": "blue",
        "bonus": "Kauppataidot, kulttuuriresurssit",
        "startUnits": ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
    },
    {
        "name": "Venäläiset ruhtinaskunnat",
        "color": "green",
        "bonus": "Talvisotataktiikat, metsäresurssit",
        "startUnits": ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
    },
]

if __name__ == "__main__":
    print("Heimot ja Faktiot")
    print("Valitse heimosi ja hyodynna sen ainutlaatuisia erikoisuuksia")
    for faction in factions:
        print("\n" + faction['name'])
        print("Bonus: " + faction['bonus'])
        print("Aloitusyksikot: " + ', '.join(faction['startUnits']))