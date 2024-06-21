#!/usr/bin/env python3.12
from datetime import date, datetime
import logging
import pathlib
from signal import SIGINT
import subprocess
import re
from argparse import ArgumentParser
import sys


class ReportFile:
    cnt: int = 0
    filename: str
    MAX_ENTRIES: int = 500000
    stdout_regex: re.Pattern | None = None
    fh = None

    def __init__(self, args):
        if args.report_file:
            self.filename_base = args.report_file
            if args.stdout_regex:
                self.stdout_regex = re.compile(args.stdout_regex, re.IGNORECASE)
            self.today = date.today()
            filename = self.filename_base + self.today.strftime("%Y%m%d.log")
            try:
                self.fh = open(filename, "a", 1)
                logging.info(f"Opened Log File {filename}")
            except Exception as e:
                logging.info(f"Error {e} when Open Log File {self.filename}")

    def log(self, text: str):
        if not self.stdout_regex or self.stdout_regex.search(text):
            print(text, end="")
            sys.stdout.flush()
        if self.fh:
            today = date.today()
            if today != self.today or self.cnt > self.MAX_ENTRIES:
                self.today = today
                filename = self.filename_base + datetime.now().strftime(
                    "%Y%m%d_%H%M%S.log"
                )
                self.fh.write(f">>> Rotate to Log File {filename}\n")
                self.cnt = 0
                fh = self.fh
                try:
                    self.fh = open(filename, "a", 1)
                    fh.close()
                    logging.info(f"Rotate Log File {filename}")
                except Exception as e:
                    logging.info(f"Error {e} when Rotate Log File {filename}")
            self.fh.write(text)
            self.fh.flush()
            self.cnt += 1


class MyTshark:
    def __init__(self, args, extra_args):
        self.p_args = ["tshark", "-Q", "-i"]
        self.p = None
        self._prepare(args, extra_args)
        self.report_file = ReportFile(args)

    def _prepare(self, args, extra_args):
        if args.interface:
            self.p_args.append(self.select_interface(args.interface))
        elif args.from_file:
            self.p_args += ["r", args.from_file]
        proto_filter = self.add_proto_capture_filter_args(
            args.protocol, args.capture_filter
        )
        if proto_filter:
            self.p_args += ["-f", proto_filter]
        else:
            logging.warning("Capturing without any filter !!!")

        if args.display_filter:
            self.p_args += ["-Y", args.display_filter]
        else:
            proto_filter = self.add_proto_display_filter_args(args.protocol)
            if proto_filter:
                self.p_args += ["-Y", proto_filter]
        if args.decode_as:
            self.p_args += ["-d", args.decode_as]
        self.p_args += ["-l", "-T", "fields"]
        self.p_args += ["-e", "_ws.col.Time", "-t", args.time_format]
        self.add_protocol_args(args.protocol)
        self.p_args += extra_args

        if args.dry_run:
            print(self)
            exit(0)

    def run(self):
        self.p = subprocess.Popen(self.p_args, stdout=subprocess.PIPE)
        try:
            while (exit_code := self.p.poll()) == None:
                line = self.p.stdout.readline().decode()
                self.report_file.log(line)
        except KeyboardInterrupt:
            print("\nCtrl-C Received. EXIT.")
        except Exception as e:
            logging.error(f"Error reading tshark stdout {e!r}")
        finally:
            if exit_code:
                logging.error(f"tshark unexpected exit with code {exit_code}.")
            # self.p.send_signal(SIGINT)

    def __str__(self):
        return "tshark '" + "' '".join(self.p_args[1:]) + "'"

    def add_protocol_args(self, proto):
        match proto:
            case "tcp_tap":
                self.p_args += ["-e", "ip.src", "-e", "tcp.stream"]
                self.p_args += ["-e", "tcp_tap.msgraw"]
            case "udp_tap":
                self.p_args += ["-e", "ip.src", "-e", "udp.srcport"]
                self.p_args += ["-e", "udp_tap.msgraw"]
            case "snom":
                self.p_args += ["-e", "ip.src"]
                self.p_args += ["-e", "snom.sender.address", "-e", "snom.alarmid"]
                self.p_args += ["-e", "snom.msgtype", "-e", "snom.extid"]
                self.p_args += ["-e", "snom.status", "-e", "snom.msguui"]
            case "json":
                self.p_args += ["-e", "ip.src", "-e", "udp.srcport"]
                self.p_args += ["-e", "json.member_with_value"]
            case "tls_json":
                self.p_args += ["-e", "tcp.dstport", "-e", "tcp.stream"]
                self.p_args += ["-e", "http.request.uri.query.parameter"]
                self.p_args += ["-e", "json.member_with_value"]
            case "sip":
                self.p_args += ["-e", "ip.src", "-e", "udp.srcport"]
                self.p_args += ["-e", "sip.from.addr", "-e", "sip.to.addr"]
                self.p_args += ["-e", "sip.CSeq", "-e", "sip.Status-Code"]
                self.p_args += [
                    "-e",
                    "sip.Expires",
                    "-e",
                    "sdp.connection_info.address",
                ]
                self.p_args += ["-e", "sdp.media.port"]
            case "mqtt":
                self.p_args += ["-e", "ip.src", "-e", "tcp.stream"]
                self.p_args += ["-e", "_ws.col.Info"]
            case "en6080":
                self.p_args += []
            case _:
                self.p_args += ["-e", "frame.len"]
                self.p_args += ["-e", "_ws.col.Info"]

    @staticmethod
    def add_proto_capture_filter_args(proto, capture_filter):
        match proto:
            case "tcp-conn":
                if capture_filter:
                    return (
                        capture_filter
                        + " and (tcp[tcpflags] & (tcp-syn|tcp-fin|tcp-rst) != 0)"
                    )
                else:
                    return "(tcp[tcpflags] & (tcp-syn|tcp-fin|tcp-rst) != 0)"
            case "tcp_tap":
                return capture_filter if capture_filter else "tcp"
            case "udp_tap":
                return capture_filter if capture_filter else "udp"
            case _:
                return capture_filter

    @staticmethod
    def add_proto_display_filter_args(proto):
        match proto:
            case "tcp_tap" | "udp_tap" | "snom" | "sip":
                return proto
            case "json" | "tls_json":
                return "json"
            case "en6080":
                return "http or (websocket and wsino.scicode != 125)"
            case "mgcp":
                return 'mgcp.req.verb == "CRCX" || mgcp.req.verb == "DLCX" || sdp'
            case "mqtt":
                return "(tcp.flags.syn==1||tcp.flags.reset==1||tcp.flags.fin==1||tcp.flags.push==1)"
            case _:
                return None

    @staticmethod
    def select_interface(interface) -> str:
        res = subprocess.run(["tshark", "-D"], capture_output=True, timeout=5)
        pattern = re.compile(rf"(\d+).*{interface}.*", re.I)
        if_lines = [if_line.decode() for if_line in res.stdout.split(b"\n")]
        # print("\n".join(if_lines))
        if_matches = [
            m for ifs in if_lines if (m := re.match(pattern, ifs)) is not None
        ]
        if len(if_matches) > 1:
            logging.warning(
                f"""More than one iterface with {interface} matched:
{"\n".join([m.group(0) for m in if_matches])}
Chossing no {if_matches[0].group(1)}.
            """
            )
        return if_matches[0].group(1)

    @staticmethod
    def parse_args():
        parser = ArgumentParser(
            description=f"{pathlib.Path(__file__).name} argument parser"
        )

        parser.add_argument("-i", "--interface", help="the interface to capture from")
        parser.add_argument(
            "-p",
            "--protocol",
            default="other",
            help="Provide the protocol",
            choices=[
                "snom",
                "tcp-conn",
                "mqtt",
                "sip",
                "json",
                "tls_json",
                "udp_tap",
                "tcp_tap",
                "en6080",
                "mgcp",
                "other",
            ],
        )
        parser.add_argument("-r", "--from-file", help="the pcap capture file to read")
        parser.add_argument("-f", "--capture-filter", help="the pcap capture filter")
        parser.add_argument(
            "-d",
            "--decode-as",
            help="decode as parameter (ex. udp.port==2011,udp_tap see tshark help)",
        )
        parser.add_argument("-Y", "--display-filter", help="wireshark display filter")
        parser.add_argument(
            "--dry-run",
            help="Display tshark generated cmd line and exit",
            action="store_true",
        )
        parser.add_argument(
            "--time-format",
            help="Provide the time formating option",
            default="ad",
            choices=["a", "ad", "adoy", "d", "dd", "e", "r", "u", "ud", "udoy"],
        )
        parser.add_argument(
            "--report-file",
            help="Report output file name",
        )
        parser.add_argument(
            "--stdout-regex",
            help="regex for filtering stdout",
        )

        result, extra_args = parser.parse_known_args()
        if not (result.from_file or result.interface):
            parser.error("-i/--interface or -r/--from-file need to be present")
        elif result.from_file and result.interface:
            parser.error("-i/--interface and -r/--from-file cannot be both present")

        return MyTshark(result, extra_args)


def main():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
    )
    my_tshark = MyTshark.parse_args()
    my_tshark.run()


if __name__ == "__main__":
    main()
