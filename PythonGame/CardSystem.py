# CardSystem.py
# Python implementation for the card system

import random

# Oletuskortit
DEFAULT_CARDS = [
    {'id': 1, 'name': 'Hyökkäys', 'type': 'attack', 'effect': 'Hyökkää viholliseen'},
    {'id': 2, 'name': 'Puolustus', 'type': 'defense', 'effect': 'Lisää puolustusta'},
    {'id': 3, 'name': 'Diplomaattinen neuvottelu', 'type': 'diplomacy', 'effect': 'Parani suhteita'},
    {'id': 4, 'name': 'Liike', 'type': 'movement', 'effect': 'Siirrä yksikköä'},
    {'id': 5, 'name': 'Strategia', 'type': 'strategy', 'effect': 'Erityinen liike'},
]

class CardSystem:
    """
    Manages the card system and player hand.
    """
    MAX_CARDS_PER_TURN = 3
    HAND_SIZE = 10

    def __init__(self):
        """Initialize the card system."""
        self.player_hand = []
        self.cards_played_this_turn = 0
        self.initialize_hand()

    def initialize_hand(self):
        """Initialize player's hand with random cards."""
        for _ in range(self.HAND_SIZE):
            card = random.choice(DEFAULT_CARDS).copy()
            self.player_hand.append(card)

    def can_play_card(self):
        """Check if player can play another card this turn."""
        return self.cards_played_this_turn < self.MAX_CARDS_PER_TURN

    def play_card(self, card_id):
        """
        Play a card from hand.
        
        Args:
            card_id (int): The ID of the card to play.
            
        Returns:
            dict: The played card or None if not found/can't play.
        """
        if not self.can_play_card():
            return None

        for i, card in enumerate(self.player_hand):
            if card['id'] == card_id:
                played_card = self.player_hand.pop(i)
                self.cards_played_this_turn += 1
                # Draw a new card
                new_card = random.choice(DEFAULT_CARDS).copy()
                self.player_hand.append(new_card)
                return played_card

        return None

    def end_turn(self):
        """Reset card counter for next turn."""
        self.cards_played_this_turn = 0

    def get_hand(self):
        """Get player's current hand."""
        return self.player_hand

    def get_cards_remaining(self):
        """Get how many cards can be played this turn."""
        return self.MAX_CARDS_PER_TURN - self.cards_played_this_turn

if __name__ == "__main__":
    print("Card System initialized")
    cs = CardSystem()
    print(f"Hand: {cs.get_hand()}")
    print(f"Cards remaining this turn: {cs.get_cards_remaining()}")
