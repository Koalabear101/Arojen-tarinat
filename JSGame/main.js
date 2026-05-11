// main.js
// Main game script for Arojen-tarinat (JavaScript version)

const { GameBoard } = require('./GameBoard');
const { calculateDamage } = require('./AdvancedCombatRules');
const { DiplomacySystem } = require('./DiplomacySystem');
const { CardSystem } = require('./CardSystem');

// Yksinkertainen factions data (voit importata jos tarvitset)
const factions = [
    { name: "Mongoli-heimo", bonus: "Ratsuväen bonus", color: "amber" },
    { name: "Kiinan dynastia", bonus: "Linnoitukset", color: "red" },
    { name: "Persialainen valtakunta", bonus: "Kauppataidot", color: "blue" },
    { name: "Venäläiset ruhtinaskunnat", bonus: "Talvisotataktiikat", color: "green" }
];

function main() {
    console.log("Tervetuloa Arojen-tarinoihin!");
    console.log("Strategiapeli heimojen välisestä taistelusta.\n");

    // Valitse heimot (yksinkertaistettu, käytä promptia selaimessa)
    console.log("Saatavilla olevat heimot:");
    factions.forEach((faction, i) => {
        console.log(`${i + 1}. ${faction.name} - ${faction.bonus}`);
    });
    const factionChoice = 0; // Oletusvalinta, muuta tarvittaessa
    const playerFaction = factions[factionChoice];
    console.log(`Valitsit: ${playerFaction.name}\n`);

    // Alusta pelilauta
    const board = new GameBoard(10, 10);
    const diplomacy = new DiplomacySystem();
    const cardSystem = new CardSystem();

    // Lisää aloitusyksiköitä
    board.placeUnit(0, 0, { type: 'warrior', strength: 10, defense: 5, faction: playerFaction.name });
    board.placeUnit(9, 9, { type: 'warrior', strength: 8, defense: 6, faction: 'Vihollinen' });

    console.log("Pelilauta alustettu. Aloitusyksiköt sijoitettu.\n");
    console.log(`Kädessä olevia kortteja: ${cardSystem.getHand().length}`);
    console.log(`Kortteja voi pelata vuorossa: ${cardSystem.getCardsRemaining()}`);

    // Simuloi yksinkertainen kierros (Node.js:ssa, käytä readlinea interaktiivisuuteen)
    console.log("Nykyinen lauta:");
    for (let y = 0; y < board.height; y++) {
        let row = [];
        for (let x = 0; x < board.width; x++) {
            const unit = board.board[y][x];
            row.push(unit ? unit.faction[0] : '.');
        }
        console.log(row.join(' '));
    }

    // Yksinkertainen hyökkäys demo
    const attacker = board.board[0][0];
    const defender = board.board[9][9];
    if (attacker && defender) {
        // Tarkista korttien rajoitus
        if (cardSystem.canPlayCard()) {
            const damage = calculateDamage(attacker, defender);
            defender.defense -= damage;
            console.log(`Hyökkäys aiheutti ${damage} vahinkoa!`);
            cardSystem.playCard(1); // Simuloitu hyökkäyskortti (ID 1)
            if (defender.defense <= 0) {
                console.log("Vihollinen tuhottu!");
                board.board[9][9] = null;
            }
            console.log(`Jäljellä: ${cardSystem.getCardsRemaining()} korttia tässä vuorossa`);
        } else {
            console.log("Et voi pelata enää kortteja tässä vuorossa! (max 3 korttia)");
        }
    }

    // Diplomacy demo
    if (cardSystem.canPlayCard()) {
        let relation = diplomacy.getRelation(playerFaction.name, 'Vihollinen');
        console.log(`Nykyinen suhde viholliseen: ${relation}`);
        diplomacy.setRelation(playerFaction.name, 'Vihollinen', relation + 10);
        cardSystem.playCard(3); // Simuloitu diplomaattinen kortti (ID 3)
        console.log("Diplomatia paransi suhteita!");
        console.log(`Jäljellä: ${cardSystem.getCardsRemaining()} korttia tässä vuorossa`);
    } else {
        console.log("Et voi pelata enää kortteja tässä vuorossa! (max 3 korttia)");
    }

    // Vuoron lopetus
    cardSystem.endTurn();
    console.log("\nVuoro päättyi. Kaikki kortit nollattu uutta vuoroa varten.");
    console.log(`Jäljellä seuraavalla vuorolla: ${cardSystem.getCardsRemaining()} korttia`);

    console.log("Peli päättyi. Kiitos pelaamisesta!");
}

main();