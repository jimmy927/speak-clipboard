# speak-clipboard

Select text in Windows Terminal, press one key, hear it read aloud. Press the key again to stop.

It's built for Windows + WSL2 and has low latency. Speech starts about 260 ms after the key press, because the daemon stays running and plays the audio while it's still being synthesised.

## How it works

- **`speak-clipboard.ahk`** (Windows, AutoHotkey v2) binds Win+C. On a Keychron keyboard in Windows mode that's the mic key. The script writes the clipboard to `%TEMP%\speak-request.txt`. It also starts the daemon in WSL at login and restarts it every minute if WSL killed it.
- **`speak-daemon`** (WSL, Python) keeps running and checks the request file for changes. It streams [edge-tts](https://github.com/rany2/edge-tts) audio into `ffplay`. Each request toggles playback: if it's speaking, it stops; if it's idle, it starts.
- **`speak`** (WSL, command line) takes text as arguments or on stdin, e.g. `echo done | speak`. It stops any current playback first, so your text is always spoken.

Windows Terminal needs `copyOnSelect` turned on. Then selecting text is enough, and you don't have to copy it.

## Install

Requirements: WSL2 with WSLg audio, `ffmpeg` (`sudo apt install ffmpeg`), and [AutoHotkey v2](https://www.autohotkey.com/) on Windows.

```sh
python3 install.py
```

Then add a shortcut to `%USERPROFILE%\.local\bin\speak-clipboard.ahk` in `shell:startup`, and run the script once.

Some paths are hardcoded: the WSL distro and user in `speak-clipboard.ahk` (`Ubuntu-20.04`, `jimmy`), and the Windows temp path in `speak` and `speak-daemon`. Edit them to match your machine. The voice (`en-GB-RyanNeural`, +20 % rate) is set at the top of `speak-daemon`.
