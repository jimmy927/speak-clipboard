#!/usr/bin/env python3
"""Install speak-clipboard on a WSL machine. Safe to re-run.

1. A dedicated venv with edge-tts, where speak-daemon re-execs itself.
2. Symlinks ~/.local/bin/{speak,speak-daemon} into this repo, so the
   AutoHotkey script (and your shell) always run the checked-out code.
3. A copy of speak-clipboard.ahk in the Windows %USERPROFILE%\\.local\\bin:
   AutoHotkey is a Windows binary and cannot load a script over the WSL mount
   at boot, when WSL may not be up yet.
"""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import venv
from pathlib import Path

REPO = Path(__file__).resolve().parent
VENV = Path.home() / ".local/share/speak-daemon/venv"
LOCAL_BIN = Path.home() / ".local/bin"
COMMANDS = ("speak", "speak-daemon")
AHK = "speak-clipboard.ahk"


def install_venv() -> None:
    if not (VENV / "bin/python").exists():
        venv.create(VENV, with_pip=True)
    subprocess.run(  # nosec B603 - fixed venv interpreter, fixed arguments
        [str(VENV / "bin/python"), "-m", "pip", "install", "-q", "-U", "edge-tts"],
        check=True,
    )
    print(f"  venv: {VENV}")


def install_commands() -> None:
    LOCAL_BIN.mkdir(parents=True, exist_ok=True)
    for name in COMMANDS:
        link = LOCAL_BIN / name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(REPO / name)
        print(f"  {link} -> {REPO / name}")


def windows_home() -> Path:
    profile = subprocess.run(  # nosec B603 - fixed full-path cmd, no untrusted input
        ["/mnt/c/Windows/System32/cmd.exe", "/c", "echo %USERPROFILE%"],
        capture_output=True,
        text=True,
        cwd="/mnt/c",
        check=True,
    ).stdout.strip()
    return Path(f"/mnt/{profile[0].lower()}{profile[2:].replace(chr(92), '/')}")


def install_ahk() -> None:
    target_dir = windows_home() / ".local/bin"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / AHK
    target.write_bytes((REPO / AHK).read_bytes())
    print(f"  {target}")


def main() -> int:
    print("Installing speak-clipboard:")
    install_venv()
    install_commands()
    install_ahk()
    print(
        "Start it: run the .ahk with AutoHotkey v2 (put a shortcut to it in\n"
        "shell:startup to have it at every login). It brings the daemon up itself."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
