"""Runtime hook: pre-load numpy's OpenBLAS DLL before any imports."""
import os
import sys
import glob

if sys.platform == "win32":
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(__file__)
    libs_dir = os.path.join(base, "numpy", ".libs")
    if os.path.isdir(libs_dir):
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(libs_dir)
        from ctypes import WinDLL
        for dll in glob.glob(os.path.join(libs_dir, "*.dll")):
            try:
                WinDLL(dll)
            except OSError:
                pass
