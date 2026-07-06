"""Bootstrap wrapper for the AICluster Worker service.

When PyInstaller sees ``worker/scripts/run.py`` as the entry, it
freezes it as ``__main__``. The worker application uses
``from app.main import run`` (an absolute import) so a wrapper is not
strictly required, but having one ensures the worker always has a
clean entry point and the right working directory.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and os.path.isdir(os.path.join(meipass, "app")):
        sys.path.insert(0, meipass)
    from app.main import run
    run()


if __name__ == "__main__":
    main()
