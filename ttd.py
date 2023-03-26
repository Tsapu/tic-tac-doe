import grpc
import time
import sys
import threading
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
                self.node_listener = threading.Thread(target=self.join_game)
                self.node_listener.start()
                #self.join_game()
                return
        print("Unable to join the game, the node list is already full")

    def join_game(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        ttd_pb2_grpc.add_ttdServicer_to_server(ttdServicer(), server)
        server.add_insecure_port(f"[::]:{self.node_port}")
        server.start()
        print("Successfully joined the player list")
        server.wait_for_termination()
    
    def start_game(self):
        print("Someone started the game")

    # static method to parse commands"
    def parse_cmd(cmd):
        if cmd == "start-game":
            # Check if all three nodes have connected:
            for n in NODE_PORTS:
                if not check_socket(n):
                    print("All nodes must be connected before starting the game")
                    return
            # Start the game

class Game:
    def __init__(self):
        self.board = ttdBoard()
        self.players = []
        self.current_player = 0
        self.game_over = False

    def start_game(self):        
     # Send gRPC request to show the board
            

class ttdServicer(ttd_pb2_grpc.ttdServicer):
    def GetTime(self, request, context):
        current_time = time.time()
        return ttd_pb2.TimeResponse(current_time=current_time)


def sync_time(node):
    with grpc.insecure_channel(f"localhost:{node}") as channel:
        stub = ttd_pb2_grpc.ttdStub(channel)
        response = stub.GetTime(ttd_pb2.TimeRequest())
        current_time = time.time()
        round_trip_time = current_time - response.current_time
        corrected_time = current_time - (round_trip_time / 2)
        return corrected_time

if __name__ == '__main__':
    # if len(sys.argv) != 2:
    #     print("Usage: python3 ttd.py <node_id>")
    #     sys.exit(1)
    node = Participant()
    while True:
        cmd = input("> ")
        if cmd == "quit" or cmd == "q":
            break
        Participant.parse_cmd(cmd)