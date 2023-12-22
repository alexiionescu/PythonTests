# %%
import numpy as np
import json
import timeit
import math
import sys
import logging
import re


class TestObject:
    """ Test Object """

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
        import pandas as pd

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
        delimiter = "-" * 30
        with open(name) as fpin:
            calls: dict = {}
            for line in fpin:
                cnt += 1
                fields = line.strip().split("\t")
                ftype = fields[2]
                fmsg = fields[3]
                if ftype == "ACD":
                    if fmsg == "new ACDCall":
                        cid = fields[4]
                        calls[cid] = {"clines": [fields], "out": False}
                    elif fmsg == "del ACDCall":
                        cid = fields[4]
                        if cid in calls.keys():
                            cinfo = calls.pop(cid, {})
                            if cinfo["out"]:
                                for cline in cinfo.get("clines"):
                                    print(" ".join(cline))
                                print(" ".join(fields))
                                print(delimiter * 2)
                    else:
                        if fmsg != "Merge":
                            cid = fields[4]
                            consultid = ""
                        else:
                            cid = re.findall("dwCallID=\d+", fields[4])[0]
                            consultid = re.findall("dwCallID=\d+", fields[6])[0]
                        if cid in calls.keys():
                            cinfo = calls[cid]
                            if consultid:
                                # not empty string is True, empty string is False
                                if consultid in calls.keys():
                                    consultinfo = calls[consultid]
                                    cinfo["clines"].append([delimiter])
                                    for cline in consultinfo["clines"]:
                                        cinfo["clines"].append(cline)
                                    cinfo["clines"].append([delimiter])
                                    if consultinfo["out"]:
                                        cinfo["out"] = True
                            cinfo["clines"].append(fields)
                            if not cinfo["out"]:
                                if len(fields) > 5:
                                    dbidm = re.findall("L:\d+", fields[5])
                                    if dbidm:
                                        # not empty list is True, empty list is False
                                        for f in filter:
                                            if f == dbidm[0]:
                                                cinfo["out"] = True
                                                break
                elif ftype == "CALL EVENT":
                    cid = fields[6]
                    if cid in calls.keys():
                        cinfo = calls[cid]
                        cinfo["clines"].append(fields)
                        if not cinfo["out"]:
                            for f in filter:
                                if f == fields[4] or f == " ".join(fields[3:5]):
                                    # 'DEV=?' or '<Event> DEV=?' match
                                    cinfo["out"] = True
                                    break
                elif ftype == "UPL NOTIFY":
                    cid = fields[6]
                    if cid in calls.keys():
                        calls[cid]["clines"].append(fields)
                elif ftype == "DB":
                    cid = re.findall("dwCallID=\d+", fmsg)[0]
                    if cid in calls.keys():
                        calls[cid]["clines"].append(fields)

        self.Result = cnt
        self.resultFormat = ">>> parsed lines cnt: {}"

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
    if sys.argv[0] == "ipykernel_launcher":
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
            t1.testFormating()
            # t1.testFiles("tests/test.log", "Established DEV=2798")

        mainTester()
        t1.printResult()
    else:
        code = "t1." + sys.argv[1] + "('" + "','".join(sys.argv[2:]) + "')"
        print(">>> exec", code)
        exec(code, globals(), locals())
        t1.printResult()