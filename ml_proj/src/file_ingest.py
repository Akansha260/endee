import glob
import os
import time
from typing import Generator, Tuple, Dict, Any


def tail_files(pattern: str, follow: bool = True, poll_interval: float = 0.5) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """
    Tail all files matching the given glob pattern.

    Yields (line, metadata) where metadata contains at least the filename.
    """
    files = {}

    def _open_new_files():
        for path in glob.glob(pattern):
            if path not in files:
                try:
                    f = open(path, "r", encoding="utf-8", errors="ignore")
                    # Start at end for true tail behaviour
                    f.seek(0, os.SEEK_END)
                    files[path] = f
                except OSError:
                    continue

    _open_new_files()

    while True:
        any_line = False

        for path, f in list(files.items()):
            line = f.readline()
            if line:
                any_line = True
                yield line.rstrip("\n"), {"file": path}

        if not follow:
            break

        _open_new_files()

        if not any_line:
            time.sleep(poll_interval)

