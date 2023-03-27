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
        row = (cell - 1) // 3
        column = (cell - 1) % 3
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
        symbol_board = [ [self.board[i][j][0] for j in range(3)] for i in range(3) ]
        print(symbol_board)
        if symbol_board[0][0] == symbol_board[0][1] == symbol_board[0][2] != "e":
            return True
        elif symbol_board[0][0] == symbol_board[1][0] == symbol_board[2][0] != "e":
            return True
        elif symbol_board[0][0] == symbol_board[1][1] == symbol_board[2][2] != "e":
            return True
        elif symbol_board[0][1] == symbol_board[1][1] == symbol_board[2][1] != "e":
            return True
        elif symbol_board[2][0] == symbol_board[2][1] == symbol_board[2][2] != "e":
            return True
        elif symbol_board[0][2] == symbol_board[1][2] == symbol_board[2][2] != "e":
            return True
        elif symbol_board[0][2] == symbol_board[1][1] == symbol_board[2][0] != "e":
            return True
        elif symbol_board[1][0] == symbol_board[1][1] == symbol_board[1][2] != "e":
            return True
        return False

    def check_draw(self):
        flatten = [item for sublist in self.board for item in sublist]
        if "empty" not in flatten:
            return True
        return False