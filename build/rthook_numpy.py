"""Runtime hook: ensure numpy DLLs are findable in frozen builds."""
import os
import sys

if getattr(sys, "frozen", False) and sys.platform == "win32":
    _base = sys._MEIPASS
    _dirs = [
        _base,
        os.path.join(_base, "numpy", ".libs"),
        os.path.join(_base, "numpy.libs"),
        os.path.join(_base, "_internal", "numpy", ".libs"),
        os.path.join(_base, "_internal", "numpy.libs"),
    ]
    for _d in _dirs:
        if os.path.isdir(_d):
            try:
                os.add_dll_directory(_d)
            except (OSError, AttributeError):
                pass
            os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")
