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
    });
}

document.getElementById('attack-btn').addEventListener('click', function() {
    fetch('/attack', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        document.getElementById('messages').textContent = data.message;
        updateBoard();
    });
});

document.getElementById('diplomacy-btn').addEventListener('click', function() {
    fetch('/diplomacy', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        document.getElementById('messages').textContent = data.message;
    });
});