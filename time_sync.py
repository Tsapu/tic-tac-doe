import grpc
import time
from concurrent import futures

import time_sync_pb2
import time_sync_pb2_grpc

class TimeSyncServicer(time_sync_pb2_grpc.TimeSyncServicer):
    def GetTime(self, request, context):
        current_time = time.time()
        return time_sync_pb2.TimeResponse(current_time=current_time)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    time_sync_pb2_grpc.add_TimeSyncServicer_to_server(TimeSyncServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Time Sync Server started...")
    server.wait_for_termination()

def sync_time(node):
    with grpc.insecure_channel(node) as channel:
        stub = time_sync_pb2_grpc.TimeSyncStub(channel)
        response = stub.GetTime(time_sync_pb2.TimeRequest())
        current_time = time.time()
        round_trip_time = current_time - response.current_time
        corrected_time = current_time - (round_trip_time / 2)
        return corrected_time

if __name__ == '__main__':
    serve()