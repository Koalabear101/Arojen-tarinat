document.getElementById('faction-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);

    fetch('/start_game', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            document.getElementById('setup').style.display = 'none';
            document.getElementById('game').style.display = 'block';
            document.getElementById('player-faction').textContent = data.faction;
            updateBoard();
        }
    });
});

function updateBoard() {
    fetch('/get_board')
    .then(response => response.json())
    .then(data => {
        const boardDiv = document.getElementById('board');
        boardDiv.innerHTML = '';

        data.board.forEach(row => {
            row.forEach(cell => {
                const cellDiv = document.createElement('div');
                cellDiv.className = 'cell';

                if (cell) {
                    cellDiv.textContent = cell.faction[0]; // Ensimmäinen kirjain
                    if (cell.faction === document.getElementById('player-faction').textContent) {
                        cellDiv.classList.add('player');
                    } else {
                        cellDiv.classList.add('enemy');
                    }
                } else {
                    cellDiv.classList.add('empty');
                }

                boardDiv.appendChild(cellDiv);
            });
        });

        document.getElementById('turn').textContent = data.turn;
        document.getElementById('cards-remaining').textContent = data.cards_remaining;
        
        // Päivitä korttien näyttö
        updateHand(data.hand);
    });
}

function updateHand(hand) {
    const handDiv = document.getElementById('hand');
    if (!handDiv) return;
    
    handDiv.innerHTML = '';
    hand.forEach(card => {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card';
        cardDiv.innerHTML = `
            <div class="card-name">${card.name}</div>
            <div class="card-type">${card.type}</div>
            <button onclick="playCardFromHand(${card.id})">Pelaa</button>
        `;
        handDiv.appendChild(cardDiv);
    });
}

function playCardFromHand(cardId) {
    fetch('/play_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ card_id: cardId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('messages').textContent = `Pelasit kortin: ${data.card.name}`;
            document.getElementById('cards-remaining').textContent = data.cards_remaining;
            updateHand(data.hand);
        } else {
            document.getElementById('messages').textContent = data.error;
        }
    });
}

document.getElementById('attack-btn').addEventListener('click', function() {
    fetch('/attack', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('messages').textContent = data.message;
        } else {
            document.getElementById('messages').textContent = data.message;
            document.getElementById('cards-remaining').textContent = data.cards_remaining;
            updateBoard();
        }
    });
});

document.getElementById('diplomacy-btn').addEventListener('click', function() {
    fetch('/diplomacy', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('messages').textContent = data.message;
        } else {
            document.getElementById('messages').textContent = data.message;
            document.getElementById('cards-remaining').textContent = data.cards_remaining;
        }
    });
});

document.getElementById('end-turn-btn').addEventListener('click', function() {
    fetch('/end_turn', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('messages').textContent = 'Vuoro päättyi!';
            document.getElementById('turn').textContent = data.turn;
            document.getElementById('cards-remaining').textContent = data.cards_remaining;
            updateBoard();
        }
    });
});