"""The paths speak, speak-daemon and install.py must agree on.

The request file is the only channel between a hotkey and the daemon: any
write to it is a request. On WSL it lives on the Windows side, because the
AutoHotkey script writes it, and install.py records where. Everywhere else it
is a plain file under ~/.cache.
"""

from __future__ import annotations

from pathlib import Path

VENV_PYTHON = Path.home() / ".local/share/speak-daemon/venv/bin/python"
STATE_DIR = Path.home() / ".cache/speak-clipboard"
LOCK_FILE = STATE_DIR / "daemon.lock"
# Written by install.py on WSL only; holds the WSL path of the Windows file.
REQUEST_POINTER = Path.home() / ".config/speak-clipboard/request-file"


def request_file() -> Path:
    if REQUEST_POINTER.exists():
        return Path(REQUEST_POINTER.read_text(encoding="utf-8").strip())
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / "request.txt"
