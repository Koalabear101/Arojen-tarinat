// GameBoard.js
// JavaScript implementation for the game board

/**
 * Represents the game board with grid-based unit placement.
 */
class GameBoard {
    /**
     * Creates a new game board.
     * @param {number} width - The width of the board.
     * @param {number} height - The height of the board.
     */
    constructor(width, height) {
        this.width = width;
        this.height = height;
        this.board = this.initializeBoard();
    }

    /**
     * Initializes the board as a 2D array filled with null.
     * @returns {Array<Array>} The initialized board.
     */
    initializeBoard() {
        let board = [];
        for (let i = 0; i < this.height; i++) {
            board[i] = new Array(this.width).fill(null);
        }
        return board;
    }

    /**
     * Places a unit on the board at the specified coordinates if valid.
     * @param {number} x - The x-coordinate.
     * @param {number} y - The y-coordinate.
     * @param {*} unit - The unit to place.
     */
    placeUnit(x, y, unit) {
        if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
            this.board[y][x] = unit;
        }
    }
}

console.log("Game Board initialized");