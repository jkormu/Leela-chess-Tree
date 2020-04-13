import sys
from setuptools import find_packages
from cx_Freeze import setup, Executable
from os.path import join
from constants import ROOT_DIR

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["dash", "plotly",
                 "networkx",
                 "jinja2",
                 ],
    #"includes": [],
    "excludes": ["tkinter"],
    "include_files": [(join(ROOT_DIR, 'assets'), 'assets')]
    #"include_files": [('./assets/', 'assets')]
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
#if sys.platform == "win32":
#    base = "Win32GUI"
icon = join(ROOT_DIR, 'assets')
icon = join(icon, 'favicon.ico')

setup(name="LcT",
        version="beta",
        packages=find_packages(),
        description="Leela chess Tree",
        options={"build_exe": build_exe_options},
        executables=[Executable("LcT.py", base=base, icon=icon)]
        )