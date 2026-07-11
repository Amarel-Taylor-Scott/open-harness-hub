#!/bin/bash
# START_VNC=1 -> a WATCHABLE desktop: Xvfb + fluxbox + x11vnc + noVNC on :6080, browser runs HEADED.
set -e
if [ "$START_VNC" = "1" ]; then
    Xvfb :99 -screen 0 1600x900x24 &
    sleep 1
    DISPLAY=:99 fluxbox >/dev/null 2>&1 &
    x11vnc -display :99 -forever -nopw -shared -bg -quiet
    websockify --web=/usr/share/novnc 6080 localhost:5900 >/dev/null 2>&1 &
    export DISPLAY=:99 TAEDRI_EMULATOR_HEADED=1
    echo "watchable desktop: http://localhost:6080/vnc.html (connect, no password)"
fi
exec python3 /emulator/taedri_real_use_emulator.py "$@"
