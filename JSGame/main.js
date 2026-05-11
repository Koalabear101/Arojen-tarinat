// main.js
// Main game script for Arojen-tarinat (JavaScript version)

const { GameBoard } = require('./GameBoard');
const { calculateDamage } = require('./AdvancedCombatRules');
const { DiplomacySystem } = require('./DiplomacySystem');
const { CardSystem } = require('./CardSystem');

// Game state
let gameState = {
    gameOver: false,
    winner: null,
    message: null,
    phase: 'CARD_PHASE'  // CARD_PHASE, ENEMY_PHASE
};

function checkGameStatus(board) {
    // Tarkista pelin voitto/häviö-ehdot
    const playerUnit = board.board[0][0];
    const enemyUnit = board.board[9][9];
    
    // Tarkista voitto (vihollinen tuhottu)
    if (!enemyUnit || enemyUnit.defense <= 0) {
        gameState.gameOver = true;
        gameState.winner = 'player';
        gameState.message = 'Voitit! Vihollinen on tuhottu!';
        return true;
    }
    
    // Tarkista häviö (pelaajan yksikkö tuhottu)
    if (!playerUnit || playerUnit.defense <= 0) {
        gameState.gameOver = true;
        gameState.winner = 'enemy';
        gameState.message = 'Hävisit! Sinun yksikkösi oli tuhottu!';
        return true;
    }
    
    return false;
}

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
    console.log(`Kortteja voi pelata vuorossa: ${cardSystem.getCardsRemaining()}\n`);
    console.log(`Nykyinen vaihe: ${gameState.phase}\n`);

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

    // Yksinkertainen hyökkäys demo (CARD_PHASE:ssa)
    console.log("--- CARD_PHASE: Kortti-vaihe ---");
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
                checkGameStatus(board);
            }
            console.log(`Jäljellä: ${cardSystem.getCardsRemaining()} korttia tässä vaiheessa`);
        } else {
            console.log("Et voi pelata enää kortteja tässä vaihessa! (max 3 korttia)");
        }
    }

    if (gameState.gameOver) {
        console.log(`\n*** ${gameState.message} ***`);
        console.log("Peli päättyi. Kiitos pelaamisesta!");
        return;
    }

    // Siirry ENEMY_PHASE:hen
    gameState.phase = 'ENEMY_PHASE';
    console.log(`\n--- ENEMY_PHASE: Vihollisen vaihe ---`);
    console.log("Vihollinen hyökkää takaisin!");
    
    // Vihollisen counter-hyökkäys
    const enemyAttacker = board.board[9][9];
    const playerDefender = board.board[0][0];
    
    if (enemyAttacker && playerDefender) {
        const counterDamage = calculateDamage(enemyAttacker, playerDefender);
        playerDefender.defense -= counterDamage;
        console.log(`Vihollinen hyökkäsi takaisin ja aiheutti ${counterDamage} vahinkoa!`);
        if (playerDefender.defense <= 0) {
            console.log("Sinun yksikkösi tuhottu!");
            board.board[0][0] = null;
            checkGameStatus(board);
        }
    }

    if (gameState.gameOver) {
        console.log(`\n*** ${gameState.message} ***`);
    }

    // Palaa CARD_PHASE:hen seuraavalle vuorolle
    gameState.phase = 'CARD_PHASE';
    cardSystem.endTurn();
    console.log(`\n--- Uusi vuoro alkaa (CARD_PHASE) ---`);
    console.log(`Jäljellä seuraavalla vuorolla: ${cardSystem.getCardsRemaining()} korttia`);

    console.log("Peli päättyi. Kiitos pelaamisesta!");
}

main();