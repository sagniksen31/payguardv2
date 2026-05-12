# Proxy package to keep original core logic untouched.
import os
import sys


_PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)
