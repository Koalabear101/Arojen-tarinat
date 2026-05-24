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
        
        // Päivitä vaiheen näyttö
        updatePhaseDisplay(data.phase);
        
        // Päivitä korttien näyttö
        updateHand(data.hand);
        
        // Päivitä mainosbanneri
        updateAdBanner();
        
        // Näytä voitto/häviö-viesti
        if (data.game_over) {
            showGameOverScreen(data.message, data.winner);
            disableGameControls();
        }
    });
}

const ads = [
    'Pelaa nyt ja saa 50% enemmän voimia!',
    'Tutustu voimakkaisiin korttipaketteihin ja voita taistelut helpommin!',
    'Vahvista heimotasi tänään – uusi kampanja alkaa pian!',
    'Käytä strategiaa ja ansaitse harvinaisia voimakortteja!',
    'Pysy mukana pelissä: uusi päivitys tuo lisää haasteita!'
];

window.addEventListener('load', updateAdBanner);

function updateAdBanner() {
    const banner = document.getElementById('ad-banner');
    if (!banner) return;
    const randomIndex = Math.floor(Math.random() * ads.length);
    banner.innerHTML = `<strong>Sponsoroitu viesti:</strong> ${ads[randomIndex]}`;
}

function updatePhaseDisplay(phase) {
    const phaseDiv = document.getElementById('phase-display');
    if (!phaseDiv) return;
    
    let phaseText = '';
    let phaseClass = '';
    
    if (phase === 'CARD_PHASE') {
        phaseText = '🎴 KORTIN VAIHE - Pelaa kortteja (enintään 3)';
        phaseClass = 'card-phase';
    } else if (phase === 'ENEMY_PHASE') {
        phaseText = '⚔️ VIHOLLISEN VAIHE - Klikkaa "Seuraava vaihe" jatkaaksesi';
        phaseClass = 'enemy-phase';
    }
    
    phaseDiv.textContent = phaseText;
    phaseDiv.className = `phase-display ${phaseClass}`;
    
    // Päivitä napeista saatavuus
    updateButtonStates(phase);
}

function updateButtonStates(phase) {
    const attackBtn = document.getElementById('attack-btn');
    const nextPhaseBtn = document.getElementById('next-phase-btn');
    const endTurnBtn = document.getElementById('end-turn-btn');
    
    if (phase === 'CARD_PHASE') {
        if (attackBtn) attackBtn.disabled = false;
        if (nextPhaseBtn) nextPhaseBtn.style.display = 'none';
        if (endTurnBtn) endTurnBtn.style.display = 'none';
    } else if (phase === 'ENEMY_PHASE') {
        if (attackBtn) attackBtn.disabled = true;
        if (nextPhaseBtn) nextPhaseBtn.style.display = 'inline-block';
        if (endTurnBtn) endTurnBtn.style.display = 'inline-block';
    }
}

function showGameOverScreen(message, winner) {
    const gameOverDiv = document.createElement('div');
    gameOverDiv.id = 'game-over-screen';
    gameOverDiv.className = winner === 'player' ? 'win' : 'loss';
    gameOverDiv.innerHTML = `
        <div class="game-over-content">
            <h2>${message}</h2>
            <button onclick="location.reload()">Pelaa uudelleen</button>
        </div>
    `;
    document.body.appendChild(gameOverDiv);
}

function disableGameControls() {
    document.getElementById('attack-btn').disabled = true;
    document.getElementById('diplomacy-btn').disabled = true;
    document.getElementById('end-turn-btn').disabled = true;
    
    const cardButtons = document.querySelectorAll('.card button');
    cardButtons.forEach(btn => btn.disabled = true);
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
            document.getElementById('messages').textContent = data.error;
        } else {
            document.getElementById('messages').textContent = data.message;
            updatePhaseDisplay(data.phase);
        }
        
        if (data.game_over) {
            showGameOverScreen(data.end_message, data.winner);
            disableGameControls();
        } else {
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
        if (data.error) {
            document.getElementById('messages').textContent = data.error;
        } else {
            document.getElementById('messages').textContent = 'Vuoro päättyi! Uusi käyttäjävuoro alkaa.';
            document.getElementById('turn').textContent = data.turn;
            document.getElementById('cards-remaining').textContent = data.cards_remaining;
            updatePhaseDisplay(data.phase);
        }
        
        if (data.game_over && data.end_message) {
            showGameOverScreen(data.end_message, data.winner);
            disableGameControls();
        } else if (!data.error) {
            updateBoard();
        }
    });
});

// Lisää next-phase nappula kuuntelija
const nextPhaseBtn = document.getElementById('next-phase-btn');
if (nextPhaseBtn) {
    nextPhaseBtn.addEventListener('click', function() {
        fetch('/next_phase', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('messages').textContent = data.error;
            } else {
                let message = '';
                if (data.counter_message) {
                    message = data.counter_message;
                }
                if (data.game_over) {
                    message += ' ' + data.end_message;
                }
                document.getElementById('messages').textContent = message || 'Vihollinen on toiminut.';
                updatePhaseDisplay(data.phase);
            }
            
            if (data.game_over && data.end_message) {
                showGameOverScreen(data.end_message, data.winner);
                disableGameControls();
            } else {
                updateBoard();
            }
        });
    });
}