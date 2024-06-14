#!/usr/bin/env python3.12
from argparse import ArgumentParser
import calendar
import os
import pandas as pd
from pathlib import Path
import sys
import urllib.request
import time
from datetime import datetime
import re
import apportionment.methods as app  # type: ignore # pip install apportionment

# fmt: off
RO_COUNTIES = [
    "ab", "ar", "ag", "bc", "bh", "bn", "bt", "br", "bv", "bz", "cl", "cs",
    "cj", "ct", "cv", "db", "dj", "gl", "gr", "gj", "hr", "hd", "il", "is",
    "if", "mm", "mh", "ms", "nt", "ot", "ph", "sm", "sj", "sb", "sv", "tr", 
    "tm", "tl", "vl", "vs", "vn",
    "b",
    "sr",  # diaspora
]
# fmt: on


def download(path: Path, basename: str, url_base: str, county: str | None):
    now = datetime.now().timestamp()
    if county:
        files = [f"{county}.csv"]
    else:
        files = [basename + county + ".csv" for county in RO_COUNTIES]
    for filename in files:
        f = path / filename
        file_mtime = None
        if f.exists():
            file_mtime = f.stat().st_mtime
        if not file_mtime or now - file_mtime > 60:
            opener = urllib.request.build_opener()
            if file_mtime:
                timestr = time.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(file_mtime)
                )
                # print(f"downloading {f.name} modified since {timestr} ...")
                opener.addheaders.append(("If-Modified-Since", timestr))
            else:
                print(f"downloading new {f.name} ... ")
            urllib.request.install_opener(opener)
            for _ in range(3):
                try:
                    _, headers = urllib.request.urlretrieve(url_base + filename, f)
                except urllib.error.HTTPError as e:
                    if e.code != 304:
                        print(f"Could not download {f.name} Error: {e}")
                    break
                try:
                    pd.read_csv(f)  # check valid csv
                    if "Last-Modified" in headers:
                        mtime = calendar.timegm(
                            time.strptime(
                                headers["Last-Modified"],
                                "%a, %d %b %Y %H:%M:%S GMT",
                            )
                        )
                        os.utime(f, (mtime, mtime))
                        print(
                            f"downloaded {f.name} Modified {headers['Last-Modified']}"
                        )
                    else:
                        print(f"downloaded {f.name} No Last-Modified header")
                    time.sleep(0.2)
                    break
                except:  # invalid csv, sleep and retry
                    print(f"retry {f.name} ... ")
                    f.unlink()
                    time.sleep(10)
            else:
                print(f"ERROR: Could not download valid {f.name} ... ")
            urllib.request.install_opener(urllib.request.build_opener())


def run(path: Path, basename: str, seats: int, county: str | None, filter: str | None):
    if county:
        basepath = Path(path)
        files = [basepath / f"{county}.csv"]
    else:
        files = path.glob(f"{basename}*.csv")  # type: ignore
    df_all = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    if filter:
        df = df_all.query(filter)
    else:
        df = df_all
    
    max_votes = df["a"].sum()
    act_votes = df["b"].sum()
    df_col_filter = df.loc[:, df.columns.str.endswith("-voturi")]
    sum_series = df_col_filter.sum(numeric_only=True)
    total = sum_series.sum()
    re_is_group = re.compile(r"ALIANȚA|PARTID|UNIUNEA", flags=re.I)
    tr_dict = [
        [str(k)[:-7], v, p * 100]
        for (k, v) in sum_series.items()
        if (p := v / total) >= 0.05
        or (not re.search(re_is_group, str(k)) and p >= 0.03)
    ]
    df_perc = pd.DataFrame(tr_dict, columns=["Candidat", "Votes", "Votes%"])
    df_perc["Seats"] = app.compute("dhondt", df_perc.Votes.to_list(), seats)
    print(df_perc.sort_values("Votes", ascending=False))
    print(
        f"\nTotal votes: {act_votes} from {max_votes} ({100 * act_votes / max_votes:.02f}%)"
    )


def parse_args():
    parser = ArgumentParser(description=f"{Path(__file__).name} argument parser")

    parser.add_argument("--basename", default="pv_part_cnty_eup_", help="csv base name")
    parser.add_argument("--county", default=None, help="csv file name")
    parser.add_argument(
        "--path", default="csv_files", help="csv files folder path", type=Path
    )
    parser.add_argument(
        "--url",
        default="https://prezenta.roaep.ro/europarlamentare09062024/data/csv/sicpv/",
        help="base url for csv files download",
    )
    parser.add_argument("--no-download", action="store_true", help="disable download")
    parser.add_argument("--seats", default=33, help="number of seats")
    parser.add_argument("--filter", default=None, help="pandas filter expression")

    result, _ = parser.parse_known_args()
    if not result.basename.endswith("_"):
        result.basename += "_"

    return result


if __name__ == "__main__":
    pd.options.display.float_format = "{:.1f}".format
    args = parse_args()
    if not args.no_download:
        download(args.path, args.basename, args.url, args.county)
    run(args.path, args.basename, args.seats, args.county, args.filter)
