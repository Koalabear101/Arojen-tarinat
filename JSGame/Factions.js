/**
 * Factions.js — Heimojen yleiskatsaus
 *
 * Näyttää 4 heimon perustiedot: nimi, bonus ja alkuasetelma.
 * Tiivistetympi versio kuin DetailedFactions.
 */

const factions = [
    {
        name: "Mongoli-heimo",
        color: "amber",
        bonus: "Ratsuväen bonus, nopea liikkeelläolo",
        startUnits: ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
    },
    {
        name: "Kiinan dynastia",
        color: "red",
        bonus: "Linnoitukset, teknologia-edistykset",
        startUnits: ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
    },
    {
        name: "Persialainen valtakunta",
        color: "blue",
        bonus: "Kauppataidot, kulttuuriresurssit",
        startUnits: ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
    },
    {
        name: "Venäläiset ruhtinaskunnat",
        color: "green",
        bonus: "Talvisotataktiikat, metsäresurssit",
        startUnits: ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
    },
];

console.log("Heimot ja Faktiot");
console.log("Valitse heimosi ja hyödynnä sen ainutlaatuisia erikoisuuksia");
factions.forEach(faction => {
    console.log(`\n${faction.name}`);
    console.log(`Bonus: ${faction.bonus}`);
    console.log(`Aloitusyksiköt: ${faction.startUnits.join(', ')}`);
});

module.exports = { factions };