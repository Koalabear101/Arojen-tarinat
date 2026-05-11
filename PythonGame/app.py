from flask import Flask, render_template, request, jsonify
from GameBoard import GameBoard
from AdvancedCombatRules import calculate_damage
from DiplomacySystem import DiplomacySystem
from CardSystem import CardSystem
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Game'))
from Factions import factions

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)

# Globaali pelitila (yksinkertaistettu, käytä sessioita tuotannossa)
game_state = {
    'board': None,
    'diplomacy': None,
    'card_system': None,
    'player_faction': None,
    'turn': 0,
    'game_over': False,
    'winner': None,
    'message': None
}

def check_game_status():
    """Tarkista pelin voitto/häviö-ehdot."""
    if not game_state['board']:
        return
    
    player_unit = game_state['board'].board[0][0]
    enemy_unit = game_state['board'].board[9][9]
    
    # Tarkista voitto (vihollinen tuhottu)
    if not enemy_unit or enemy_unit['defense'] <= 0:
        game_state['game_over'] = True
        game_state['winner'] = 'player'
        game_state['message'] = 'Voitit! Vihollinen on tuhottu!'
        return True
    
    # Tarkista häviö (pelaajan yksikkö tuhottu)
    if not player_unit or player_unit['defense'] <= 0:
        game_state['game_over'] = True
        game_state['winner'] = 'enemy'
        game_state['message'] = 'Hävisit! Sinun yksikkösi oli tuhottu!'
        return True
    
    return False

@app.route('/')
def index():
    return render_template('index.html', factions=factions)

@app.route('/start_game', methods=['POST'])
def start_game():
    faction_choice = int(request.form['faction'])
    player_faction = factions[faction_choice]

    board = GameBoard(10, 10)
    diplomacy = DiplomacySystem()
    card_system = CardSystem()

    # Lisää aloitusyksiköitä
    board.place_unit(0, 0, {'type': 'warrior', 'strength': 10, 'defense': 5, 'faction': player_faction['name']})
    board.place_unit(9, 9, {'type': 'warrior', 'strength': 8, 'defense': 6, 'faction': 'Vihollinen'})

    game_state['board'] = board
    game_state['diplomacy'] = diplomacy
    game_state['card_system'] = card_system
    game_state['player_faction'] = player_faction
    game_state['turn'] = 0
    game_state['game_over'] = False
    game_state['winner'] = None
    game_state['message'] = None

    return jsonify({'status': 'started', 'faction': player_faction['name']})

@app.route('/get_board')
def get_board():
    if not game_state['board']:
        return jsonify({'error': 'Game not started'})

    check_game_status()

    board_data = []
    for y in range(game_state['board'].height):
        row = []
        for x in range(game_state['board'].width):
            unit = game_state['board'].board[y][x]
            if unit:
                row.append({'faction': unit['faction'], 'type': unit['type']})
            else:
                row.append(None)
        board_data.append(row)

    cards_remaining = game_state['card_system'].get_cards_remaining()
    return jsonify({
        'board': board_data, 
        'turn': game_state['turn'],
        'cards_remaining': cards_remaining,
        'hand': game_state['card_system'].get_hand(),
        'game_over': game_state['game_over'],
        'winner': game_state['winner'],
        'message': game_state['message']
    })

@app.route('/attack', methods=['POST'])
def attack():
    if not game_state['board']:
        return jsonify({'error': 'Game not started'})

    # Tarkista pelin tila
    if game_state['game_over']:
        return jsonify({
            'message': game_state['message'],
            'error': True,
            'game_over': True,
            'winner': game_state['winner']
        })

    # Tarkista että kortteja voi vielä pelata
    if not game_state['card_system'].can_play_card():
        return jsonify({
            'message': 'Et voi pelata enää kortteja tässä vuorossa! (max 3 korttia)',
            'error': True,
            'turn': game_state['turn']
        })

    # Yksinkertainen hyökkäys (voit laajentaa koordinaateilla)
    attacker = game_state['board'].board[0][0]
    defender = game_state['board'].board[9][9]
    if attacker and defender:
        damage = calculate_damage(attacker, defender)
        defender['defense'] -= damage
        message = f"Hyökkäys aiheutti {damage} vahinkoa!"
        if defender['defense'] <= 0:
            message += " Vihollinen tuhottu!"
            game_state['board'].board[9][9] = None
            check_game_status()
        # Merkitse että kortti pelattiin
        game_state['card_system'].cards_played_this_turn += 1
    else:
        message = "Ei kelvollisia yksiköitä hyökkäykseen."

    cards_remaining = game_state['card_system'].get_cards_remaining()
    response = {
        'message': message,
        'turn': game_state['turn'],
        'cards_remaining': cards_remaining,
        'game_over': game_state['game_over'],
        'winner': game_state['winner']
    }
    
    if game_state['game_over']:
        response['end_message'] = game_state['message']
    
    return jsonify(response)

@app.route('/diplomacy', methods=['POST'])
def diplomacy_action():
    if not game_state['diplomacy']:
        return jsonify({'error': 'Game not started'})

    # Tarkista että kortteja voi vielä pelata
    if not game_state['card_system'].can_play_card():
        return jsonify({'message': 'Et voi pelata enää kortteja tässä vuorossa! (max 3 korttia)', 'error': True})

    relation = game_state['diplomacy'].get_relation(game_state['player_faction']['name'], 'Vihollinen')
    game_state['diplomacy'].set_relation(game_state['player_faction']['name'], 'Vihollinen', relation + 10)
    message = f"Diplomatia paransi suhteita! Nykyinen suhde: {relation + 10}"
    # Merkitse että kortti pelattiin
    game_state['card_system'].cards_played_this_turn += 1

    cards_remaining = game_state['card_system'].get_cards_remaining()
    return jsonify({'message': message, 'cards_remaining': cards_remaining})

@app.route('/play_card', methods=['POST'])
def play_card():
    if not game_state['card_system']:
        return jsonify({'error': 'Game not started'})

    data = request.get_json()
    card_id = data.get('card_id')
    
    if not game_state['card_system'].can_play_card():
        return jsonify({'error': 'Et voi pelata enää kortteja tässä vuorossa! (max 3 korttia)', 'cards_remaining': 0})

    played_card = game_state['card_system'].play_card(card_id)
    
    if not played_card:
        return jsonify({'error': 'Korttia ei löydy kädessäsi'})

    cards_remaining = game_state['card_system'].get_cards_remaining()
    return jsonify({
        'success': True,
        'card': played_card,
        'cards_remaining': cards_remaining,
        'hand': game_state['card_system'].get_hand()
    })

@app.route('/end_turn', methods=['POST'])
def end_turn():
    if not game_state['card_system']:
        return jsonify({'error': 'Game not started'})

    # Tarkista pelin tila
    if game_state['game_over']:
        return jsonify({
            'message': game_state['message'],
            'error': True,
            'game_over': True,
            'winner': game_state['winner']
        })

    game_state['card_system'].end_turn()
    game_state['turn'] += 1
    
    # Vihollinen hyökkää takaisin
    attacker = game_state['board'].board[9][9]
    defender = game_state['board'].board[0][0]
    counter_message = ""
    
    if attacker and defender:
        damage = calculate_damage(attacker, defender)
        defender['defense'] -= damage
        counter_message = f"Vihollinen hyökkäsi takaisin ja aiheutti {damage} vahinkoa!"
        if defender['defense'] <= 0:
            counter_message += " Sinun yksikkösi tuhottu!"
            game_state['board'].board[0][0] = None
            check_game_status()
    
    return jsonify({
        'success': True,
        'turn': game_state['turn'],
        'cards_remaining': game_state['card_system'].get_cards_remaining(),
        'counter_message': counter_message,
        'game_over': game_state['game_over'],
        'winner': game_state['winner'],
        'end_message': game_state['message'] if game_state['game_over'] else None
    })

if __name__ == '__main__':
    app.run(debug=True)