#Requires AutoHotkey v2.0
#SingleInstance Force
; Read the terminal selection aloud, on the Keychron mic key.
;
; Windows Terminal has copyOnSelect enabled, so marking text with the mouse is
; already enough - the selection is on the clipboard by the time the key press
; arrives.
;
; The mic key emits Win+C in Windows mode (verified with a raw key probe: six
; presses, LWin then c every time). Windows treats Win+C as the Copilot
; shortcut, which is why the key looked dead - it was opening Copilot, not
; doing nothing. Binding it here consumes the press, so Copilot no longer opens
; on that key.
;
; This half only reads the clipboard and drops it in a file. Synthesis and
; playback belong to speak-daemon, which stays resident in WSL: launching an
; interpreter per keypress cost ~2000ms before a single word was spoken, and
; almost none of that was the speech itself.
;
; The daemon owns the speaking/idle state, so this writes the same request
; either way and lets it decide. Two places tracking one piece of state is how
; a toggle ends up working most of the time.

REQUEST := A_Temp "\speak-request.txt"

; Bring the daemon up with the keyboard hook, so one Startup entry covers both.
;
; Re-run on a timer as well, because WSL dies independently of Windows: a
; `wsl --shutdown`, a WSL update, or the VM idling out takes the daemon with it
; and AutoHotkey would never notice - the mic key would just silently stop
; working until the next login. A second copy is harmless: the daemon holds an
; abstract-socket lock and the loser exits at once.
EnsureDaemon(*) {
    ; Full interpreter path, not `python3`: --exec skips the login shell, so
    ; PATH is the bare default and `python3` resolves to /usr/bin/python3,
    ; which has no edge_tts. The daemon gets its own venv rather than borrowing
    ; a project environment that could be rebuilt or removed underneath it.
    ; ~/.local/bin/speak-daemon is install.py's symlink into this repo. Its
    ; shebang runs plain `python3`; speak-daemon re-execs itself into its own
    ; venv, which is where edge_tts lives.
    Run 'wsl.exe -d Ubuntu-20.04 -u jimmy --exec '
        . '/home/jimmy/.local/bin/speak-daemon', , "Hide"
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
