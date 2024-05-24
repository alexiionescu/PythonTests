from sys import platform, modules
from typing import Callable
import numpy as np
import re
from pympler.asizeof import asizeof  # type: ignore

from IPython.core.magic import register_line_cell_magic
from IPython import get_ipython
from traitlets.config.manager import BaseJSONConfigManager

ipython = get_ipython()

if platform == "win32":
    """
    Register Powershell Cell Magic
    """
    SM = ipython.magics_manager.magics.get("cell")["script"].__self__
    scripts = list(SM.script_magics)
    paths = dict(SM.script_paths)
    if "pwsh" not in scripts:
        scripts.append("pwsh")
        paths["pwsh"] = "pwsh.exe -noprofile -command -"
        config_manager = BaseJSONConfigManager(config_dir=ipython.profile_dir.location)
        config_basename = "ipython_config"
        config_manager.set(
            config_basename,
            {"ScriptMagics": {"script_magics": scripts, "script_paths": paths}},
        )
        print("pwsh magic added. please restart ipython...")

    @register_line_cell_magic
    def ps(line, cell=None):
        "Magic that works both as %ps and as %%ps"
        if cell is None:
            ipython.run_cell_magic("pwsh", "--out posh_output", line)
            return posh_output.splitlines()  # type: ignore
        else:
            return ipython.run_cell_magic("pwsh", line, cell)

elif platform == "linux":
    pass
elif platform == "darwin":
    pass

from IPython.display import display, Markdown

def printmd(string):
    display(Markdown(string))


class IPythonShellEx:
    def __init__(self):
        pass

    @staticmethod
    def timed_func(times: Callable | int = 1):
        """
        decorator for timeit and print a function
        with repeat `times` optional first argument
        """
        from timeit import default_timer as timer

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

    @staticmethod
    def print_matrix(array, format="%.3f"):
        data = ""
        for line in array:
            for element in line:
                data += format % element + " & "
            data = data.rstrip(" &")
            data += r"\\" + "\n"
        md = (
            r"""$$\begin{pmatrix} 
%s
\end{pmatrix}$$"""
            % data
        )
        # print(md)
        display(Markdown(md))

    @staticmethod
    def generate_imports():
        import types

        for _, val in globals().items():
            if isinstance(val, types.ModuleType) and val.__name__ != "types":
                yield val.__name__, asizeof(val)


np.set_printoptions(linewidth=160, precision=3)
