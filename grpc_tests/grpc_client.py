from __future__ import print_function

import logging

import grpc  # type: ignore
import stats_pb2, stats_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    print("gRPC Will try to get stats from server ...")
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = stats_pb2_grpc.StatsReportStub(channel)
        response = stub.GetStats(stats_pb2.StatsRequest(type="nwk_stats"))
    print("gRPC Stats client received: \n" + str(response))


if __name__ == "__main__":
    logging.basicConfig()
    run()
