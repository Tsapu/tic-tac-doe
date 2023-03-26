# Storing the state of the Tic-Tac-Doe board

class ttdBoard:
    def __init__(self):
        # create a 3x3 board
        self.board = [
            ["empty", "empty", "empty"],
            ["empty", "empty", "empty"],
            ["empty", "empty", "empty"],
        ]
    def to_str(self):
        return str(self.board)
    def place_symbol(self, symbol, cell):
        if symbol != "X" and symbol != "O":
            raise Exception("Invalid symbol")
        row = cell // 3
        column = (cell % 3) - 1
        self.board[row][column] = symbol