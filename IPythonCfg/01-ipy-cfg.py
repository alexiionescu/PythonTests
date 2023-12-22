from IPython.core.magic import register_line_cell_magic
from sys import platform

from IPython import get_ipython
from traitlets.config.manager import BaseJSONConfigManager

ipython = get_ipython()

if platform == "win32":
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
            return posh_output.splitlines()
        else:
            return ipython.run_cell_magic("pwsh", line, cell)


elif platform == "linux":
    pass


class IPythonShellEx:
    def __init__(self):
        pass

ish = IPythonShellEx()