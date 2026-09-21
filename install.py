#!/usr/bin/env python3
"""Install speak-clipboard. Safe to re-run; re-run it when speak-clipboard.ahk changes.

Everywhere:
  1. A dedicated venv with edge-tts, where speak-daemon re-execs itself.
  2. Symlinks ~/.local/bin/{speak,speak-daemon} into this repo.
  3. Stops a running daemon, so the next start runs the current code.

On WSL, additionally:
  4. Renders speak-clipboard.ahk with this distro, user and daemon path into
     %USERPROFILE%\\.local\\bin. AutoHotkey is a Windows binary and cannot load
     a script over the WSL mount at boot, when WSL may not be up yet.
  5. Records where the Windows-side request file lives (speak_paths.py).
  6. Puts a shortcut in the Windows Startup folder and starts AutoHotkey,
     which starts the daemon.
"""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess  # nosec B404
import sys
import venv
from pathlib import Path

from speak_paths import REQUEST_POINTER, VENV_PYTHON

REPO = Path(__file__).resolve().parent
LOCAL_BIN = Path.home() / ".local/bin"
COMMANDS = ("speak", "speak-daemon")
AHK = "speak-clipboard.ahk"
CMD_EXE = "/mnt/c/Windows/System32/cmd.exe"
POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"


def install_venv() -> None:
    if not VENV_PYTHON.exists():
        venv.create(VENV_PYTHON.parent.parent, with_pip=True)
    subprocess.run(  # nosec B603 - fixed venv interpreter, fixed arguments
        [str(VENV_PYTHON), "-m", "pip", "install", "-q", "-U", "edge-tts"],
        check=True,
    )
    print(f"  venv with edge-tts: {VENV_PYTHON.parent.parent}")


def install_commands() -> None:
    LOCAL_BIN.mkdir(parents=True, exist_ok=True)
    for name in COMMANDS:
        link = LOCAL_BIN / name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(REPO / name)
        print(f"  {link} -> {REPO / name}")
    if str(LOCAL_BIN) not in os.environ.get("PATH", "").split(":"):
        print(f'  NOTE: add to your shell rc: export PATH="{LOCAL_BIN}:$PATH"')


def stop_daemon() -> None:
    subprocess.run(  # nosec B603 B607 - fixed arguments
        ["pkill", "-f", f"{VENV_PYTHON} .*speak-daemon"], check=False
    )


def windows_env(name: str) -> str:
    return subprocess.run(  # nosec B603 - fixed full-path cmd, fixed variable name
        [CMD_EXE, "/c", f"echo %{name}%"],
        capture_output=True,
        text=True,
        cwd="/mnt/c",  # cmd.exe refuses a WSL (UNC) working directory
        check=True,
    ).stdout.strip()


def wslpath(flag: str, path: str) -> str:
    return subprocess.run(  # nosec B603 B607 - fixed arguments
        ["wslpath", flag, path], capture_output=True, text=True, check=True
    ).stdout.strip()


def find_autohotkey() -> Path | None:
    for base in (
        windows_env("LOCALAPPDATA") + r"\Programs",
        windows_env("ProgramFiles"),
    ):
        exe = Path(wslpath("-u", base + r"\AutoHotkey\v2\AutoHotkey64.exe"))
        if exe.exists():
            return exe
    return None


def install_windows_side() -> int:
    autohotkey = find_autohotkey()
    if autohotkey is None:
        print(
            "AutoHotkey v2 is not installed. In PowerShell run\n"
            "    winget install AutoHotkey.AutoHotkey\n"
            "then run this installer again."
        )
        return 1

    request_dir = Path(wslpath("-u", windows_env("LOCALAPPDATA") + r"\speak-clipboard"))
    request_dir.mkdir(parents=True, exist_ok=True)
    REQUEST_POINTER.parent.mkdir(parents=True, exist_ok=True)
    REQUEST_POINTER.write_text(f"{request_dir / 'request.txt'}\n", encoding="utf-8")
    print(f"  request file: {request_dir / 'request.txt'}")

    script = (REPO / AHK).read_text(encoding="utf-8")
    script = (
        script.replace("@WSL_DISTRO@", os.environ["WSL_DISTRO_NAME"])
        .replace("@WSL_USER@", getpass.getuser())
        .replace("@DAEMON@", str(LOCAL_BIN / "speak-daemon"))
    )
    target_dir = Path(wslpath("-u", windows_env("USERPROFILE") + r"\.local\bin"))
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / AHK
    target.write_text(script, encoding="utf-8")
    print(f"  {target}")

    exe_win = wslpath("-w", str(autohotkey))
    script_win = wslpath("-w", str(target))
    startup = windows_env("APPDATA") + r"\Microsoft\Windows\Start Menu\Programs\Startup"
    shortcut = f"{startup}\\speak-clipboard.lnk"
    def ps(value: str) -> str:  # a PowerShell single-quoted literal
        return "'" + value.replace("'", "''") + "'"

    subprocess.run(  # nosec B603 - fixed full-path powershell, paths we computed
        [
            POWERSHELL,
            "-NoProfile",
            "-Command",
            f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut({ps(shortcut)});"
            f" $s.TargetPath = {ps(exe_win)}; $s.Arguments = {ps(chr(34) + script_win + chr(34))};"
            " $s.Description = 'Read the clipboard aloud on Win+C'; $s.Save()",
        ],
        cwd="/mnt/c",
        check=True,
    )
    print(f"  startup shortcut: {shortcut}")

    subprocess.Popen(  # nosec B603 - AutoHotkey we located, script we wrote
        [str(autohotkey), script_win], cwd="/mnt/c", start_new_session=True
    )
    print("  AutoHotkey started; it brings the daemon up within a few seconds.")
    return 0


def main() -> int:
    if shutil.which("ffplay") is None:
        print(
            "ffplay is missing. Install ffmpeg (Debian/Ubuntu: sudo apt install ffmpeg; macOS: brew install ffmpeg)."
        )
        return 1
    print("Installing speak-clipboard:")
    install_venv()
    install_commands()
    stop_daemon()
    if "WSL_DISTRO_NAME" in os.environ:
        return install_windows_side()
    print("Not WSL: the hotkey and autostart are yours to set up - see README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
