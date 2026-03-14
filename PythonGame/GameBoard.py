# GameBoard.py
# Python implementation for the game board

class GameBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = self.initialize_board()

    def initialize_board(self):
        return [[None for _ in range(self.width)] for _ in range(self.height)]

    def place_unit(self, x, y, unit):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.board[y][x] = unit

if __name__ == "__main__":
    print("Game Board initialized")