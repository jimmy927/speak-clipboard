# speak-clipboard

Select text, press one key, hear it read aloud. Press the key again to stop.

It's built for **Windows + WSL2**, which is the tested setup. Speech starts about a quarter of a second after the key press. The voice is Microsoft Edge's neural TTS via [edge-tts](https://github.com/rany2/edge-tts), so you need an internet connection. No API key is needed.

## Setup on Windows + WSL2

You need:

- WSL2 with audio. Windows 11, or Windows 10 with WSLg, works out of the box. Check that `ffplay` makes sound from WSL.
- `ffmpeg` and Python venv support inside WSL: `sudo apt install ffmpeg python3-venv`
- [AutoHotkey v2](https://www.autohotkey.com/) on Windows: `winget install AutoHotkey.AutoHotkey`

Then, inside WSL:

```sh
git clone https://github.com/jimmy927/speak-clipboard.git ~/src/speak-clipboard
python3 ~/src/speak-clipboard/install.py
```

That's all. The installer detects your distro, user and Windows paths. It adds a Startup shortcut so the hotkey comes back after every login, and it starts the hotkey and the daemon right away.

**Use:** copy some text and press **Win+C**. That replaces the Copilot shortcut. On Keychron keyboards in Windows mode it's the mic key. In Windows Terminal, turn on *Settings → Interaction → Automatically copy selection to clipboard*. Then selecting text is enough, and you don't need to copy it.

From a WSL shell you can also run `speak "build finished"` or `make 2>&1 | tail -1 | speak`.

**After a `git pull`**, run `install.py` again so the new code takes over.

## How it works

| Piece | Runs on | Job |
|---|---|---|
| `speak-clipboard.ahk` | Windows | Owns the hotkey. Writes the clipboard to `%LOCALAPPDATA%\speak-clipboard\request.txt`. Starts the daemon in WSL, and restarts it every minute if WSL was shut down. |
| `speak-daemon` | WSL / Linux / macOS | Keeps running and checks the request file. Streams edge-tts audio into `ffplay`. Each request toggles playback: if it's speaking, it stops; if it's idle, it starts. |
| `speak` | WSL / Linux / macOS | Command-line front end. Stops any current speech first, so your text is always spoken. |
| `install.py` | WSL / Linux / macOS | Sets up a venv at `~/.local/share/speak-daemon/venv` and links `speak` and `speak-daemon` into `~/.local/bin`. On WSL it also does everything on the Windows side. |

**Voice and speed:** change `VOICE` and `RATE` at the top of `speak-daemon`. `edge-tts --list-voices` lists the voices. **Hotkey:** change the last line of `speak-clipboard.ahk`, then run `install.py` again.

## Linux and macOS (untested)

The daemon and `speak` should work as they are. What's missing is a hotkey and autostart. Without WSL, the request file is `~/.cache/speak-clipboard/request.txt`, and any write to it toggles speech.

1. Install ffmpeg: `sudo apt install ffmpeg python3-venv` or `brew install ffmpeg`.
2. Run `python3 install.py`.
3. Start the daemon at login. On Linux, add `speak-daemon` to your desktop's autostart applications. On macOS, add a Login Item or put `(speak-daemon &) 2>/dev/null` in your shell rc. A second copy exits on its own.
4. Bind a key to a command that writes the selection to the request file:
   - **GNOME / KDE on X11:** make a custom shortcut that runs
     `sh -c 'xclip -o -selection primary > ~/.cache/speak-clipboard/request.txt'`. The primary selection is highlighted text, so you don't have to copy. Requires `xclip`.
   - **Wayland:** the same command with `wl-paste --primary` instead of `xclip -o -selection primary`. Requires `wl-clipboard`.
   - **macOS:** make a Quick Action in the Shortcuts app with *Run Shell Script* running
     `pbpaste > ~/.cache/speak-clipboard/request.txt`, and give it a keyboard shortcut in its settings. Or use Hammerspoon or skhd.

If nothing happens, run `speak-daemon` in a terminal to see its errors, and try `speak hello`.

## Troubleshooting

- **Silence on WSL:** run `ffplay -nodisp -autoexit some.mp3` in WSL. If that's silent too, WSLg audio is the problem, not this tool.
- **The key does nothing:** check that the AutoHotkey tray icon is there. If it isn't, run `install.py` again.
- **"speak-daemon already running":** that's expected. Only one daemon runs at a time.
