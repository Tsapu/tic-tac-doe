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
                self.acting_leader = False
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
                print(f"Election completed successfully. Coordinator ID is {response.leader_id}")
            else:
                print("Election failed")
        
    def start_game(self):
        # Step 1) Start clock sync with Berkeley
        self.start_clock_sync()
        # Step 2) Elect a leader
        self.elect_game_master()
        # Step 3) Configure the game
        # -- initialise the board
        self.board = ttdBoard()

    # static method to parse commands"
    def parse_cmd(self, cmd):
        if cmd == "start-game":
            # Check if all three nodes have connected:
            for n in NODE_PORTS:
                if not check_socket("localhost", n):
                    print("All nodes must be connected before starting the game")
                    return
            # Start the game
            self.start_game()


class Game:
    def __init__(self):
        self.board = ttdBoard()
        self.players = []
        self.current_player = 0
        self.game_over = False

    def start_game(self):        
     # Send gRPC request to show the board
        pass

class ttdServicer(ttd_pb2_grpc.ttdServicer):

    # def __init__(self):
    #     # self.node_times =
    #     pass

    def SyncTime(self, request, context):
        global node_clock
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        node.clock = timestamp
        # print(node.clock)
        return ttd_pb2.SyncResponse(server_timestamp=timestamp) 

    def GetTime(self, request, context):
        current_time = time.time()
        return ttd_pb2.TimeResponse(current_time=current_time)

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
                    return response
            else:
                continue
        # All the upper nodes are dead, or we are the uppermost node, claim leadership
        print("Election resolved, I am the leader #" + str(process_id))
        result = ttd_pb2.ElectionResult()
        result.leader_id = process_id
        result.success = True
        node.acting_leader = True
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
    # if len(sys.argv) != 2:
    #     print("Usage: python3 ttd.py <node_id>")
    #     sys.exit(1)
    node = Participant()
    while True:
        cmd = input("> ")
        # print(node.clock)
        if cmd == "quit" or cmd == "q":
            break
        node.parse_cmd(cmd)