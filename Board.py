# Storing the state of the Tic-Tac-Doe board

class ttdBoard:
    def __init__(self):
        # create a 3x3 board
        self.board = [
            ["empty", "empty", "empty"],
            ["empty", "empty", "empty"],
            ["empty", "empty", "empty"],
        ]
        self.players = []

    def to_str(self):
        return str(self.board)

    def assign_symbols(self):
        if len(self.players) != 2:
            print("Error: There must be exactly two players to start the game")
            return
        self.players[0]["symbol"] = "X"
        self.players[1]["symbol"] = "O"
        self.players[0]["turn"] = True
        self.players[1]["turn"] = False

    def place_symbol(self, symbol, cell, player_id, timestamp):
        if self.players[player_id]["turn"] == False:
            print(f"Error: It is not player {player_id}'s turn, but that rascal tried it anyway >:()")
            return False
        if symbol != "X" and symbol != "O":
            print("Error: symbol received is not X or O")
            return False
        row = cell // 3
        column = (cell % 3) - 1
        try:
            if self.board[row][column] != "empty":
                print("Error: cell received is not empty")
                return False
            self.board[row][column] = f"{symbol}:{timestamp}"
            return True
        except:
            print("Error: cell received is not valid")
            return False
    
    def check_win(self):
        return False

    def check_draw(self):
        return False