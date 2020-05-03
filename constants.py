import sys
import os

MAX_NODES = 100000
MAX_NUMBER_OF_CONFIGS = 10
DEFAULT_NUMBER_OF_CONFIGS = 1
DEFAULT_NODES = 800
SHOW_UNICODE_BOARD = False

def root_directory():
    if getattr(sys, 'frozen', False):
        # The application is frozen
        root = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        root = os.path.dirname(__file__)#os.path.dirname(os.path.abspath(__file__))#os.path.dirname(__file__)
    return(root)

ROOT_DIR = root_directory()