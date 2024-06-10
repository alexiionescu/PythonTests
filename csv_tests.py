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
    "bh",
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
    "mh",
    "ms",
    "nt",
    "ot",
    "ph",
    "sm",
    "sj",
    "sb",
    "sv",
    "tr",
    "tm",
    "tl",
    "vl",
    "vs",
    "vn",
    "b",
    "sr",  # diaspora
]


def download(path: Path, basename, url_base):
    now = datetime.now().timestamp()
    for county in RO_COUNTIES:
        filename = basename + county + ".csv"
        f = path / filename
        file_mtime = None
        if f.exists():
            file_mtime = f.stat().st_mtime
        if not file_mtime or now - file_mtime > 3600:
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
                time.sleep(1)
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
    # for f in path.glob(f"**/{basename}*.csv"):
    #     print(f"parse {f}")
    #     pd.read_csv(f)

    files = path.glob(f"**/{basename}*.csv")
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    max_votes = df["a"].sum()
    df_col_filter = df.loc[:, df.columns.str.endswith("-voturi")]
    sum_series = df_col_filter.sum(numeric_only=True)
    total = sum_series.sum()
    tr_dict = [
        [str(k)[:-7], p, v] for (k, v) in sum_series.items() if (p := v / total) > 0.02
    ]
    df_perc = pd.DataFrame(tr_dict, columns=["Candidat", "VotesP", "Votes"])
    df_perc["Votes%"] = 100 * df_perc.VotesP
    df_perc["MEP(s)"] = 33 * df_perc.VotesP
    print(df_perc.sort_values("Votes", ascending=False))
    print(f"\nTotal votes: {total} from {max_votes} ({100 * total / max_votes:.02f}%)")


if __name__ == "__main__":
    pd.options.display.float_format = "{:.2f}".format
    path = Path(sys.argv[1])
    download(
        path,
        "pv_part_cnty_eup_",
        "https://prezenta.roaep.ro/europarlamentare09062024/data/csv/sicpv/",
    )
    run(path, "pv_part_cnty_eup_")
