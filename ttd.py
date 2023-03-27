import grpc
import time
from datetime import datetime, timezone, timedelta
import sys
import threading
import queue
from concurrent import futures
from Board import ttdBoard
from util import check_socket

import ttd_pb2
import ttd_pb2_grpc

NODE_PORTS = ["20040", "20041", "20042"]

class Participant:
    def __init__(self, node_address="localhost"):
        # Check if we can join the game
        for n in NODE_PORTS:
            url = f"{node_address}:{n}"
            if check_socket(node_address, n):
                continue
            else:
                print(n, "is free ...joining the game.")
                self.node_port = n
                self.clock = 0
                self.acting_leader = None
                self.player_id = None
                self.is_leader = False
                # self.players = []
                # self.queue = queue.Queue()
                self.node_listener = threading.Thread(target=self.join_game)
                self.node_listener.start()
                # self.start_clock_sync()
                # self.join_game()
                return
        print("Unable to join the game, the node list is already full")

    def join_game(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        ttd_pb2_grpc.add_ttdServicer_to_server(ttdServicer(), server)
        server.add_insecure_port(f"[::]:{self.node_port}")
        server.start()
        print("Successfully joined the player list")
        server.wait_for_termination()
    
    def start_clock_sync(self):
        # Will sync node clock to other nodes, if they are connected
        print(" ...Starting a clock synchronization thread...")
        self.clock_thread = threading.Thread(target=sync_time, args=(self.node_port,))
        self.clock_thread.start()

    def elect_game_master(self):
        print("STARTING A NEW ELECTION")
        with grpc.insecure_channel(f"localhost:{self.node_port}") as channel:
            stub = ttd_pb2_grpc.ttdStub(channel)
            response = stub.StartElection(ttd_pb2.ElectionMessage(sender_id=int(self.node_port[-1:]), election_id=0))
            if response.success:
                return response.leader_id
            else:
                print("Election failed")
        
    def init_game(self):
        # Step 1) Start clock sync with Berkeley
        self.start_clock_sync()
        # Step 2) Elect a leader
        self.elect_game_master()
    
    def start_game_as_master(self):
        # Initialise the board
        self.board = ttdBoard()
        # Initialise the game with other players
        self.board.players = [{ "port": n } for n in NODE_PORTS if n != self.node_port]
        self.board.assign_symbols()
        time.sleep(0.5)
        self.send_info(self.board.players[0]["port"], "Game has started, you are X!")
        self.send_info(self.board.players[1]["port"], "Game has started, you are O!")
        self.send_info(self.board.players[0]["port"], "Your turn!")
        #self.game = Game(players)
        
        #self.open_channels()

    def send_info(self, port, message):
        with grpc.insecure_channel(f"localhost:{port}") as channel:
            stub = ttd_pb2_grpc.ttdStub(channel)
            response = stub.SendInfo(ttd_pb2.InfoMessage(message=message))
            return response.received
    
    def set_symbol(self, symbol, cell_id):
        with grpc.insecure_channel(f"localhost:{NODE_PORTS[self.acting_leader]}") as channel:
            stub = ttd_pb2_grpc.ttdStub(channel)
            response = stub.SetSymbol(ttd_pb2.SetSymbolRequest(player_id=self.player_id, symbol=symbol, cell_id=int(cell_id)))
            if response.success:
                print("Turn was succsessful")
            else:
                print("The cell is already occupied, or your're not the current player")
            return response.success

    def list_board(self):
        with grpc.insecure_channel(f"localhost:{NODE_PORTS[self.acting_leader]}") as channel:
            stub = ttd_pb2_grpc.ttdStub(channel)
            response = stub.GetBoardState(ttd_pb2.BoardRequest())
            return response.board_state
    
    def reset_game(self):
        self.acting_leader = None
        self.player_id = None
        self.is_leader = False
        
        self.send_info(self.board.players[0]["port"], "Game has been reset")
        self.send_info(self.board.players[1]["port"], "Game has been reset")
        self.board = None
        # self.elect_game_master()

    # def open_channels(self):
    #     player_1 = grpc.insecure_channel(f"localhost:{self.players[0]['port']}")
    #     player_2 = grpc.insecure_channel(f"localhost:{self.players[1]['port']}")
    #     self.channels = [player_1, player_2]
        
    # static method to parse commands"
    def parse_cmd(self, cmd):
        if cmd == "start-game":
            # Check if all three nodes have connected:
            for n in NODE_PORTS:
                if not check_socket("localhost", n):
                    print("All nodes must be connected before starting the game")
                    return
            # Everyone connected, decide on the game master
            self.init_game()
        elif cmd == "list-board":
            board_state = self.list_board()
            print(board_state)
        elif cmd.startswith("set-symbol") and len(cmd.split()) == 3:
            cell_id = cmd.split(" ")[1]
            symbol = cmd.split(" ")[2]
            print(cell_id)
            self.set_symbol(symbol, cell_id)

class ttdServicer(ttd_pb2_grpc.ttdServicer):

    def GetBoardState(self, request, context):
        return ttd_pb2.BoardResponse(board_state=node.board.to_str())

    def SetSymbol(self, request, context):
        _is_set = node.board.place_symbol(request.symbol, request.cell_id, request.player_id, node.clock)
        if _is_set:
            print(f"Symbol {request.symbol} was set at cell {request.cell_id}")
            # Check if the game is over
            if node.board.check_win():
                node.send_info(node.board.players[request.player_id]["port"], "You won!")
                node.send_info(node.board.players[(request.player_id + 1) % 2]["port"], "You lost!")
                node.reset_game()
            # Maybe it's a draw
            elif node.board.check_draw():
                node.send_info(node.board.players[request.player_id]["port"], "Draw!")
                node.send_info(node.board.players[(request.player_id + 1) % 2]["port"], "Draw!")
                node.reset_game()
            # Nope, it still continues
            else:
                # Switch turns
                node.board.players[request.player_id]["turn"] = False
                node.board.players[(request.player_id + 1) % 2]["turn"] = True
                node.send_info(node.board.players[(request.player_id + 1) % 2]["port"], "Your turn!")
                return ttd_pb2.SetSymbolResponse(success=_is_set)
        else:
            return ttd_pb2.SetSymbolResponse(success=_is_set)

    def SyncTime(self, request, context):
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        node.clock = timestamp
        return ttd_pb2.SyncResponse(server_timestamp=timestamp)

    def SendInfo(self, request, context):
        print(request.message)
        return ttd_pb2.InfoResponse(received=True)

    def StartElection(self, request, context):
        node.acting_leader = False
        process_id = int(node.node_port[-1:])
        print(f"Received election message from process {request.sender_id} with election ID {request.election_id}")
        # If we are higher prio in the ring, then make it known
        if request.election_id < process_id:
            print(f"Setting the current election ID to {process_id}")
            request.election_id = process_id

        for node_id in range(process_id+1, len(NODE_PORTS)):
            next_node_alive = check_socket('localhost', int(NODE_PORTS[node_id]))
            print(f"Checking if process {node_id} is alive: {next_node_alive}")
            if next_node_alive:
                print(f"Forwarding election message from process {process_id} to process {node_id}")
                with grpc.insecure_channel(f'localhost:{NODE_PORTS[node_id]}') as channel:
                    stub = ttd_pb2_grpc.ttdStub(channel)
                    response = stub.StartElection(ttd_pb2.ElectionMessage(sender_id=node_id, election_id=request.election_id))
                    if response.success:
                        print(f"Election completed successfully. Coordinator ID is {response.leader_id}")
                        node.player_id = process_id
                        node.acting_leader = response.leader_id
                        if node_id != process_id:
                            node.is_leader = False
                    return response
            else:
                continue
        # All the upper nodes are dead, or we are the uppermost node, claim leadership
        print("Election resolved, I am the leader #" + str(process_id))
        result = ttd_pb2.ElectionResult()
        result.leader_id = process_id
        result.success = True
        node.is_leader = True
        node.acting_leader = process_id
        # START THE GAME, YEA BOI
        node.start_game_as_master()
        return result


def sync_time(node_port):
    def get_current_time(stub):
        response = stub.SyncTime(ttd_pb2.SyncRequest())
        server_timestamp = response.server_timestamp
        return server_timestamp / 1000.0

    def calculate_offset(stub):
        local_time = datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()
        server_time = get_current_time(stub)
        return server_time - local_time

    def adjust_time(offset):
        current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        adjusted_time = current_time + timedelta(seconds=offset)
        return adjusted_time

    while True:
        for peer_node in NODE_PORTS:
            if peer_node != node_port:
                if not check_socket("localhost", peer_node):
                    continue
                with grpc.insecure_channel(f"localhost:{peer_node}") as channel:
                    stub = ttd_pb2_grpc.ttdStub(channel)
                    offset = calculate_offset(stub)
                    adjusted_time = adjust_time(offset)
                    # print('Local time:', datetime.utcnow().replace(tzinfo=timezone.utc))
                    # print('Adjusted time:', adjusted_time)

                    # Set the current timestamp of the node
                    node.clock = adjusted_time
        # will sync every second in the background
        time.sleep(1)
    

if __name__ == '__main__':
    node = Participant()
    while True:
        cmd = input("> ")
        # print(node.clock)
        if cmd == "quit" or cmd == "q":
            break
        node.parse_cmd(cmd)