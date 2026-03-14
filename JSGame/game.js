/**
 * Arojen-tarinat - JavaScript version
 * A simple console-based strategy game
 */

const { factions } = require('./Factions');

function main() {
    console.log("Tervetuloa Arojen-tarinoihin!");
    console.log("Valitse heimosi:");
    factions.forEach((faction, i) => {
        console.log(`${i + 1}. ${faction.name} - ${faction.bonus}`);
    });

    const readline = require('readline');
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    rl.question("Valinta (1-4): ", (answer) => {
        const choice = parseInt(answer) - 1;
        const playerFaction = factions[choice];
        console.log(`Valitsit: ${playerFaction.name}`);
        console.log(`Aloitusyksiköt: ${playerFaction.startUnits.join(', ')}`);

        // Simple game loop
        let turn = 1;
        function gameLoop() {
            console.log(`\nVuoro ${turn}`);
            console.log("1. Liiku");
            console.log("2. Taistele");
            console.log("3. Lopeta");
            rl.question("Toiminto: ", (action) => {
                if (action === "3") {
                    console.log("Peli päättyi!");
                    rl.close();
                    return;
                } else if (action === "1") {
                    console.log("Liikut yksikköä");
                } else if (action === "2") {
                    console.log("Taistelet");
                }
                turn++;
                gameLoop();
            });
        }
        gameLoop();
    });
}

main();