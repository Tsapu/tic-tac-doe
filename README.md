# tic-tac-doe
Mini-project 1: Distributed tic-tac-toe LTAT.06.007

**Authors:** Davis Krumins

This is a simple tic-tac-toe game that can run on a distributed network of computers (currently for testing purposes it can be run on the same computer as separate processes).

## How to run
First generate the gRPC python files:
```
python3 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. ttd.proto
```

Start up to three nodes with:
```
python3 ttd.py
```

### Commands available
- `start-game`
    
	Will sync all the clocks of the nodes using Berkeley clock synchronization.
- `list-board`

    Will request the current board state from the current leader.
- `set-symbol {1-9} {X|O}`
    
	Will set the symbol at the given position on the board. The position is given as a number from 1 to 9, where 1 is the top left corner and 9 is the bottom right corner.

The game will automatically end if a player wins or if the board is full (a draw scenario). Once a game is over a new leader needs to be elected.