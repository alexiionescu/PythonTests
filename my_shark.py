#!/usr/bin/env python3
import logging
import pathlib
import subprocess
import re
from argparse import ArgumentParser


class MyTshark:
    def __init__(self, args, extra_args):
        self.p_args = ["-Q", "-i"]
        self._prepare(args, extra_args)

    def _prepare(self, args, extra_args):
        self.p_args.append(self.select_interface(args.interface))

        self.p_args.extend(extra_args)

        if args.dry_run:
            print(self)
            exit(0)

    def run(self):
        pass

    def __str__(self):
        return "tshark '" + "' '".join(self.p_args) + "'"

    @staticmethod
    def select_interface(interface) -> str:
        res = subprocess.run(["tshark", "-D"], capture_output=True, timeout=5)
        pattern = re.compile(rf"(\d+).*{interface}", re.I)
        if_lines = [if_line.decode() for if_line in res.stdout.split(b"\n")]
        # print("\n".join(if_lines))
        if_matches = [
            m for ifs in if_lines if (m := re.match(pattern, ifs)) is not None
        ]
        if len(if_matches) > 1:
            logging.warning("more than one iterface with same name")
        return if_matches[0].group(1)

    @staticmethod
    def parse_args():
        parser = ArgumentParser(
            description=f"{pathlib.Path(__file__).name} argument parser"
        )

        parser.add_argument(
            "-i", "--interface", required=True, help="the interface to capture from"
        )
        parser.add_argument(
            "-p",
            "--protocol",
            help="Provide the protocol",
            choices=[
                "snom",
                "tcp-conn",
                "mqtt",
                "sip",
                "json",
                "udp_tap",
                "tcp_tap",
                "en6080",
                "mgcp",
            ],
        )
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

        result, extra_args = parser.parse_known_args()

        return MyTshark(result, extra_args)


def main():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
    )
    my_tshark = MyTshark.parse_args()
    my_tshark.run()


if __name__ == "__main__":
    main()
