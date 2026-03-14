// GameBoard.js
// JavaScript implementation for the game board

class GameBoard {
    constructor(width, height) {
        this.width = width;
        this.height = height;
        this.board = this.initializeBoard();
    }

    initializeBoard() {
        let board = [];
        for (let i = 0; i < this.height; i++) {
            board[i] = new Array(this.width).fill(null);
        }
        return board;
    }

    placeUnit(x, y, unit) {
        if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
            this.board[y][x] = unit;
        }
    }
}

console.log("Game Board initialized");