from flask import Flask, render_template, request, jsonify
from GameBoard import GameBoard
from AdvancedCombatRules import calculate_damage
from DiplomacySystem import DiplomacySystem
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
    'player_faction': None,
    'turn': 0
}

@app.route('/')
def index():
    return render_template('index.html', factions=factions)

@app.route('/start_game', methods=['POST'])
def start_game():
    faction_choice = int(request.form['faction'])
    player_faction = factions[faction_choice]

    board = GameBoard(10, 10)
    diplomacy = DiplomacySystem()

    # Lisää aloitusyksiköitä
    board.place_unit(0, 0, {'type': 'warrior', 'strength': 10, 'defense': 5, 'faction': player_faction['name']})
    board.place_unit(9, 9, {'type': 'warrior', 'strength': 8, 'defense': 6, 'faction': 'Vihollinen'})

    game_state['board'] = board
    game_state['diplomacy'] = diplomacy
    game_state['player_faction'] = player_faction
    game_state['turn'] = 0

    return jsonify({'status': 'started', 'faction': player_faction['name']})

@app.route('/get_board')
def get_board():
    if not game_state['board']:
        return jsonify({'error': 'Game not started'})

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

    return jsonify({'board': board_data, 'turn': game_state['turn']})

@app.route('/attack', methods=['POST'])
def attack():
    if not game_state['board']:
        return jsonify({'error': 'Game not started'})

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
    else:
        message = "Ei kelvollisia yksiköitä hyökkäykseen."

    game_state['turn'] += 1
    return jsonify({'message': message, 'turn': game_state['turn']})

@app.route('/diplomacy', methods=['POST'])
def diplomacy_action():
    if not game_state['diplomacy']:
        return jsonify({'error': 'Game not started'})

    relation = game_state['diplomacy'].get_relation(game_state['player_faction']['name'], 'Vihollinen')
    game_state['diplomacy'].set_relation(game_state['player_faction']['name'], 'Vihollinen', relation + 10)
    message = f"Diplomatia paransi suhteita! Nykyinen suhde: {relation + 10}"

    return jsonify({'message': message})

if __name__ == '__main__':
    app.run(debug=True)