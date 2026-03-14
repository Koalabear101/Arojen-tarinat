# GameBoard.py
# Python implementation for the game board

class GameBoard:
    """
    Represents the game board with grid-based unit placement.
    """
    def __init__(self, width, height):
        """
        Initializes the game board.

        Args:
            width (int): The width of the board.
            height (int): The height of the board.
        """
        self.width = width
        self.height = height
        self.board = self.initialize_board()

    def initialize_board(self):
        """
        Initializes the board as a 2D list filled with None.

        Returns:
            list: The initialized board.
        """
        return [[None for _ in range(self.width)] for _ in range(self.height)]

    def place_unit(self, x, y, unit):
        """
        Places a unit on the board at the specified coordinates if valid.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            unit: The unit to place.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.board[y][x] = unit

if __name__ == "__main__":
    print("Game Board initialized")