// CardSystem.js
// JavaScript implementation for the card system

const DEFAULT_CARDS = [
    { id: 1, name: 'Hyökkäys', type: 'attack', effect: 'Hyökkää viholliseen' },
    { id: 2, name: 'Puolustus', type: 'defense', effect: 'Lisää puolustusta' },
    { id: 3, name: 'Diplomaattinen neuvottelu', type: 'diplomacy', effect: 'Parani suhteita' },
    { id: 4, name: 'Liike', type: 'movement', effect: 'Siirrä yksikköä' },
    { id: 5, name: 'Strategia', type: 'strategy', effect: 'Erityinen liike' },
];

class CardSystem {
    /**
     * Creates a new card system.
     */
    constructor() {
        this.MAX_CARDS_PER_TURN = 3;
        this.HAND_SIZE = 10;
        this.playerHand = [];
        this.cardsPlayedThisTurn = 0;
        this.initializeHand();
    }

    /**
     * Initialize player's hand with random cards.
     */
    initializeHand() {
        for (let i = 0; i < this.HAND_SIZE; i++) {
            const card = { ...DEFAULT_CARDS[Math.floor(Math.random() * DEFAULT_CARDS.length)] };
            this.playerHand.push(card);
        }
    }

    /**
     * Check if player can play another card this turn.
     * @returns {boolean} True if a card can be played.
     */
    canPlayCard() {
        return this.cardsPlayedThisTurn < this.MAX_CARDS_PER_TURN;
    }

    /**
     * Play a card from hand.
     * @param {number} cardId - The ID of the card to play.
     * @returns {Object} The played card or null if not found/can't play.
     */
    playCard(cardId) {
        if (!this.canPlayCard()) {
            return null;
        }

        const cardIndex = this.playerHand.findIndex(card => card.id === cardId);
        if (cardIndex === -1) {
            return null;
        }

        const playedCard = this.playerHand.splice(cardIndex, 1)[0];
        this.cardsPlayedThisTurn++;

        // Draw a new card
        const newCard = { ...DEFAULT_CARDS[Math.floor(Math.random() * DEFAULT_CARDS.length)] };
        this.playerHand.push(newCard);

        return playedCard;
    }

    /**
     * Reset card counter for next turn.
     */
    endTurn() {
        this.cardsPlayedThisTurn = 0;
    }

    /**
     * Get player's current hand.
     * @returns {Array} The player's hand.
     */
    getHand() {
        return this.playerHand;
    }

    /**
     * Get how many cards can be played this turn.
     * @returns {number} Cards remaining.
     */
    getCardsRemaining() {
        return this.MAX_CARDS_PER_TURN - this.cardsPlayedThisTurn;
    }
}

module.exports = { CardSystem };

console.log("Card System initialized");
