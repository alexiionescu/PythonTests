from concurrent import futures
import logging

import grpc  # type: ignore
import stats_pb2, stats_pb2_grpc


class StatsReportService(stats_pb2_grpc.StatsReportServicer):
    def GetStats(self, request, context):
        print("gRPC StatsReportService request :" + str(request))
        return stats_pb2.StatsReply(
            stats={
                f"{k:04X}": stats_pb2.StatsItem(
                    timestamp=1716604635341223 + k * 1000000,
                    istat1=k % 0x10,
                    istat2=1000 + k,
                    fstat1=1111.0 / k,
                    fstat2=14395.0 / k,
                )
                for k in range(0x10, 0x20)
            }
        )


def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    stats_pb2_grpc.add_StatsReportServicer_to_server(StatsReportService(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("gRPC Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
