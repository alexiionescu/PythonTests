import calendar
import os
import pandas as pd
from pathlib import Path
import sys
import urllib.request
import time
from datetime import datetime


RO_COUNTIES = [
    "ab",
    "ar",
    "ag",
    "bc",
    "bn",
    "bt",
    "br",
    "bv",
    "bz",
    "cl",
    "cs",
    "cj",
    "ct",
    "cv",
    "db",
    "dj",
    "gl",
    "gr",
    "gj",
    "hr",
    "hd",
    "il",
    "is",
    "if",
    "mm",
    "ms",
    "nt",
    "ot",
    "ph",
    "sj",
    "sv",
    "tr",
    "tm",
    "tl",
    "vl",
    "vs",
    "vn",
    "b",
]


def download(path: Path, basename, url_base):
    now = datetime.now().timestamp()
    for county in RO_COUNTIES:
        filename = basename + county + ".csv"
        f = path / filename
        file_mtime = None
        if f.exists():
            file_mtime = f.stat().st_mtime
        if not file_mtime or now - file_mtime > 30:
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
            try:
                _, headers = urllib.request.urlretrieve(url_base + filename, f)
                if "Last-Modified" in headers:
                    mtime = calendar.timegm(
                        time.strptime(
                            headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT"
                        )
                    )
                    os.utime(f, (mtime, mtime))
                    print(f"downloaded {f.name} Modified {headers['Last-Modified']}")
                else:
                    print(f"downloaded {f.name} No Last-Modified header")
            except urllib.error.HTTPError as e:
                if e.code != 304:
                    print(f"Could not download {f.name} Error: {e}")
            urllib.request.install_opener(urllib.request.build_opener())


def run(path: Path, basename):
    files = path.glob(f"**/{basename}*.csv")
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    sum_series = df.loc[:, df.columns.str.endswith("-voturi")].sum(numeric_only=True)
    total = sum_series.sum()
    tr_dict = {
        str(k)[:-7]: p for (k, v) in sum_series.items() if (p := 100 * v / total) > 2
    }
    df_perc = pd.DataFrame(tr_dict.items(), columns=["Candidat", "VotesPerc"])
    print(df_perc.sort_values("VotesPerc", ascending=False))


if __name__ == "__main__":
    pd.options.display.float_format = "{:.2f}".format
    path = Path(sys.argv[1])
    download(
        path,
        "pv_part_cnty_eup_",
        "https://prezenta.roaep.ro/europarlamentare09062024/data/csv/sicpv/",
    )
    run(path, "pv_part_cnty_eup_")
