"""Build-time helper modules.

This package contains Python source files that are bundled into the
release (for example ``cli_entry.py``, the entry point of the
``aicluster.exe`` CLI). They are not part of the application code path
at runtime — they are imported by the build system to generate a
PyInstaller spec.
"""
