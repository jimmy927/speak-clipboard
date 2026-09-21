#Requires AutoHotkey v2.0
#SingleInstance Force
; Read the clipboard aloud on Win+C; press again to stop.
;
; Do not run this copy directly: install.py fills in the @...@ values below and
; writes the result to %USERPROFILE%\.local\bin\speak-clipboard.ahk.
;
; With copyOnSelect enabled in Windows Terminal, marking text with the mouse is
; already enough - the selection is on the clipboard by the time the key press
; arrives.
;
; Win+C is what the Keychron mic key emits in Windows mode. Windows treats Win+C
; as the Copilot shortcut; binding it here consumes the press, so Copilot no
; longer opens on that key. Change the hotkey on the last line to taste.
;
; This half only reads the clipboard and drops it in a file. Synthesis and
; playback belong to speak-daemon, which stays resident in WSL: launching an
; interpreter per keypress cost ~2000ms before a single word was spoken, and
; almost none of that was the speech itself.
;
; The daemon owns the speaking/idle state, so this writes the same request
; either way and lets it decide. Two places tracking one piece of state is how
; a toggle ends up working most of the time.

; %LOCALAPPDATA% rather than %TEMP%: TEMP is often an 8.3 short path
; (C:\Users\JOHNSM~1\...), which the WSL side cannot open.
REQUEST_DIR := EnvGet("LOCALAPPDATA") "\speak-clipboard"
REQUEST := REQUEST_DIR "\request.txt"
DirCreate(REQUEST_DIR)

; Bring the daemon up with the keyboard hook, so one Startup entry covers both.
;
; Re-run on a timer as well, because WSL dies independently of Windows: a
; `wsl --shutdown`, a WSL update, or the VM idling out takes the daemon with it
; and AutoHotkey would never notice - the key would just silently stop working
; until the next login. A second copy is harmless: the daemon holds a lock and
; the loser exits at once.
EnsureDaemon(*) {
    ; --exec skips the login shell, so the daemon is named by full path. Its
    ; shebang runs plain `python3`; speak-daemon re-execs itself into its own
    ; venv, which is where edge_tts lives.
    Run 'wsl.exe -d @WSL_DISTRO@ -u @WSL_USER@ --exec @DAEMON@', , "Hide"
}

EnsureDaemon()
SetTimer EnsureDaemon, 60000

Speak(*) {
    text := A_Clipboard
    if (text = "")
        return
    ; Rewriting the file is the signal; the daemon watches its timestamp.
    try FileDelete(REQUEST)
    FileAppend(text, REQUEST, "UTF-8")
}

#c::Speak()
