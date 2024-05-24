# %% [markdown]
# ## Python Learning Tests
# PyPi Requirements (requires Window Reload after install)
# - pip install pympler
# %%
from typing import Callable
import numpy as np
import json
import timeit
import sys
import logging
import re

from pympler.asizeof import asizeof # type: ignore
from timeit import default_timer as timer


def timed_func(times: Callable | int = 1):
    """
    decorator for timeit and print a function
    with repeat `times` optional first argument
    """

    def timer_func(func):
        def wrapper(*args, **kwargs):
            t1 = timer()
            for _ in range(times - 1):
                func(*args, **kwargs)
            result = func(*args, **kwargs)
            t2 = timer()
            print(f"{func.__name__}() executed {times} time(s) in {(t2-t1):.6f}s")
            return result

        return wrapper

    if callable(times):
        func = times
        times = 1
        return timer_func(func)
    else:
        return timer_func


# %%
class TestObject:
    """Test Object"""

    xi = 200
    xc = 678 + 4j
    xs = "12345"
    xd = {"k1": 1, "k2": "v2", "k3": [True, None]}

    def __init__(self, **kwargs):
        for pname, pval in kwargs.items():
            setattr(self, pname, pval)

    def __str__(self):
        return json.dumps(self, indent=4, default=lambda x: x.__dict__)

    def testFormating(self):
        self.resultFormat = "&{:6}: {:016X} \t&{:6}: {:016X}"
        x1, x2 = self.xi, self.xc
        s2 = s1 = self.xs
        d = self.xd

        print(f"(|{x2.real:^12.3f}|+j|{x2.imag:^12.3f}|) |{s1:>10s}| |{x1:<10b}|")

        print(self.resultFormat.format("s1", id(s1), "s2", id(s2)))
        s2 += "dd"
        print(self.resultFormat.format("s1", id(s1), "s2", id(s2)))
        x1c = x1
        # c style fomrating
        print("&%- 6s: %016X \t&%- 6s: %016X" % ("x1c", id(x1c), "x1", id(x1)))

        d["k3"][1] = 3
        dc = d
        dc["k3"].append("sss")
        self.Result = ("dc[k3]", id(dc["k3"]), "d[k3]", id(d["k3"]))

    def testMatrix(self, n=3, m=4):
        # M1 = np.array(range(10, 22, 1)).reshape(n, m)
        # M2 = np.array(range(10, 22, 1)).reshape(m, n)
        M1 = np.random.normal(scale=5, size=(n, m)) + 1j * np.random.normal(
            scale=5, size=(n, m)
        )
        M2 = np.random.normal(scale=5, size=(m, n)) + 1j * np.random.normal(
            scale=5, size=(m, n)
        )
        # M1, M2 = np.indices((n, n))
        self.printMat(M1)
        self.printMat(M2)
        self.Result = np.matmul(M1, M2)
        self.resultFormat = "{}"

    def testIterables(self):
        for i, j in enumerate(range(10, 20, 2), 1):
            print(i, j)
        self.Result = [
            (i, j)
            for i, j in enumerate(range(10, 20, 2), 1)
            # if i % 2 == 0
        ]
        self.resultFormat = "{}"

    def testRandom(self):
        self.Result = np.random.rand(2, 10)
        self.resultFormat = "{}"

    def testSequences(self, l):
        self.Result = set(l)
        self.resultFormat = "{}"

    def testBits(self, n):
        logging.debug("n =  {:16b}".format(n))
        i = 1
        j = 1
        while True:
            c = n & i
            logging.debug("|{:02d}: {:16b}".format(j, n | i))
            logging.debug("&{:02d}: {:16b}".format(j, n & ~i))
            if c == 0:
                n |= i
                break
            else:
                n &= ~i
            i <<= 1
            j += 1
        self.Result = n
        self.resultFormat = "n = {:16b}"

    def testTime(self, func, num=100, gvars=globals()):
        self.Result = timeit.timeit(func, number=num, globals=gvars) / num
        self.resultFormat = "{:f}"

    def testTinker(self):
        import tkinter as tk
        from tkinter import filedialog
        import pandas as pd # type: ignore

        root = tk.Tk()

        canvas1 = tk.Canvas(root, width=300, height=300, bg="lightsteelblue")
        canvas1.pack()

        def getExcel():
            global df

            import_file_path = filedialog.askopenfilename()
            df = pd.read_excel(import_file_path)
            print(df)

        browseButton_Excel = tk.Button(
            text="Import Excel File",
            command=getExcel,
            bg="green",
            fg="white",
            font=("helvetica", 12, "bold"),
        )
        canvas1.create_window(150, 150, window=browseButton_Excel)

        root.lift()
        root.attributes("-topmost", True)
        root.after_idle(root.attributes, "-topmost", False)
        root.mainloop()
        self.Result = "tinker end"
        self.resultFormat = "{}"

    def testWin32(self):
        if sys.platform in ["Windows", "win32", "cygwin"]:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            h_wnd = user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(h_wnd, ctypes.byref(pid))
            self.Result = pid
            self.resultFormat = "{}"

    def testFiles(self, name: str, *filter: str):
        cnt = 0
        with open(name) as fpin:
            for line in fpin:
                cnt += 1
                fields = line.strip().split("\t")
                re.findall(r"id=(\d+)", fields[1])

        self.Result = cnt
        self.resultFormat = ">>> parsed lines cnt: {}"

    def testListComprehension(self, size=1000, sub_size=1000):
        type DictType = dict[str, dict[str, int]] | dict[str, dict[str, str]]

        x: list[DictType]
        mx: list[DictType] = []
        cat = "sss"
        sub_cat = "zlll"
        # fmt: off
        x = [
            {cat: {"ll0": 3}},
            {cat: {"ll2": 'input("Type ll2: ")'}},
            {"vvv": {sub_cat: 'input("Type lll: ")'}},
            {"vvv": {"pp0": 86596}},
            {cat: {"ll1": "ll1 value", sub_cat: f"{sub_cat} value 1"}},
            {cat: {"ll4": "ll4 value", sub_cat: f"{sub_cat} value 2"}},
        ]
        # fmt: on
        sss_unique_cnt = len([value for p in x if (value := p.get(cat)) is not None])
        # extend x, build mx
        for i in range(size * len(x)):
            item = x[i % len(x)]
            if i < len(x):  # buildup x
                sss_val = item.get(cat)
                if sss_val and sss_val.get(sub_cat):
                    for j in range(sub_size):
                        sss_val[f"ll{j:02d}"] = f"ll{j:02d} value"
            mx.append(item)

        # print(mx[1].get(cat, {}).get("ll2", "Not Found"))
        # Walrus Operator and List Comprehension
        @timed_func(1000)
        def process_list(mx, cat, sub_cat):
            cat_vals = [value for p in mx if (value := p.get(cat)) is not None]
            return cat_vals, [
                value for s in cat_vals if (value := s.get(sub_cat)) is not None
            ]

        cat_vals, cat_sub_vals = process_list(mx, cat, sub_cat)
        self.Result = len(cat_sub_vals)

        # equality test
        i = 1 % sss_unique_cnt
        k = 2 % sss_unique_cnt
        j = i + 4 * sss_unique_cnt
        print(id(cat_vals[i]), id(cat_vals[j]), cat_vals[i] == cat_vals[j])
        print(id(cat_vals[i]), id(cat_vals[k]), cat_vals[i] == cat_vals[k])
        # sizeof
        print("x        -> size =", asizeof(x), "len=", len(x))
        print("mx       -> size =", asizeof(mx), "len=", len(mx))
        print("cat_vals -> size =", asizeof(cat_vals), "len=", len(cat_vals))
        print("sub_vals -> size =", asizeof(cat_sub_vals), "len=", len(cat_sub_vals))
        self.resultFormat = "Found {} matches"

    def testDictComprehension(self, size=1000):
        rng = np.random.default_rng()
        d = {f"key{i:04d}": rng.standard_normal(10) for i in range(size)}
        # print(d["key0100"])
        d_var = [
            {k: var for k in d if (var := np.var(d[k])) >= 0.0 and var <= 0.1},
            {k: var for k in d if (var := np.var(d[k])) > 0.1 and var <= 0.2},
            {k: var for k in d if (var := np.var(d[k])) > 0.2 and var <= 0.3},
            {k: var for k in d if (var := np.var(d[k])) > 0.3 and var <= 0.4},
            {k: var for k in d if (var := np.var(d[k])) > 0.4 and var <= 0.5},
        ]
        print("d   -> size =", asizeof(d), "len=", len(d))
        self.Result = tuple(len(dv) / len(d) for dv in d_var)
        self.resultFormat = (
            "testDictComprehension variance \n"
            "[0.0,0.1]={:.2%}\n(0.1,0.2]={:.2%}\n"
            "(0.2,0.3]={:.2%}\n(0.3,0.4]={:.2%}\n"
            "(0.4,0.5]={:.2%}"
        )

    def printResult(self):
        if isinstance(self.Result, tuple):
            print(
                self.resultFormat.format(*self.Result)
            )  # unpack the iterable into argument list using *
        elif isinstance(self.Result, np.ndarray):
            self.printMat(self.Result)
        else:
            print(self.resultFormat.format(self.Result))

    def printMat(self, mat, fmt="g"):
        col_maxes = [
            max([len(("{:" + fmt + "}").format(x)) for x in col]) for col in mat.T
        ]
        for x in mat:
            for i, y in enumerate(x):
                print(("{:" + str(col_maxes[i]) + fmt + "}").format(y), end="  ")
            print("")
        print("\n")


# %%
if "__main__" == __name__:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=logging.ERROR,
        stream=sys.stdout,
    )
    logger = logging.getLogger()
    t1 = TestObject(xl=[1, "1", True, 1, "1", None], xi=199)
    if sys.argv[0].endswith("ipykernel_launcher.py"):
        # logger.setLevel(logging.DEBUG)
        def mainTester():
            # exec(input("Insert Expression"),globals(),locals())
            # t1.testWin32()
            # t1.testTinker()
            # t1.testIterables()
            # t1.testMatrix()
            # t1.testTime('t1.testMatrix()')
            # t1.testSequences([True, 1, "1", True, 1, "1" , False, 1+2j,None])  # True is 1 and 0 is False
            # t1.testBits(2**12-1)
            # t1.testFormating()
            # t1.testFiles("tests/test.log", "Established DEV=2798")
            # t1.testListComprehension(10000, 100000)
            t1.testDictComprehension(10000)

        mainTester()
        t1.printResult()
    elif len(sys.argv) > 2:
        code = "t1." + sys.argv[1] + "('" + "','".join(sys.argv[2:]) + "')"
        print(">>> exec", code)
        exec(code, globals(), locals())
        t1.printResult()

# %%
