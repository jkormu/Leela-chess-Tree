import sys
from setuptools import find_packages
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["dash", "plotly",
                 #"pandas",
                 "networkx",
                 "jinja2"
                 #"numpy",
                 #"mkl",
                 ],
    #"includes": ["numpy", "mkl"],
    "excludes": ["tkinter"],
    "include_files": [('./assets/', 'assets')]
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "LcT",
        version = "0.1",
        packages=find_packages(),
        description = "Leela chess Tree",
        options = {"build_exe": build_exe_options},
        executables = [Executable("run.py", base=base)]
        )