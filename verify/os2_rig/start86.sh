#!/bin/bash
# Launch 86Box headless against the /work config. Safe to re-run: kills ALL
# old 86Box instances (by binary path, not pid-file — the pid file used to
# hold the AppRun wrapper pid, leaving real binaries alive; see RIG.md).
set -u
export DISPLAY=:99 QT_QPA_PLATFORM=xcb XDG_RUNTIME_DIR=/tmp/xdg HOME=/root

pkill -f '/opt/86box/usr/local/bin/86Box' 2>/dev/null || true
for i in $(seq 1 20); do
    pgrep -f '/opt/86box/usr/local/bin/86Box' >/dev/null || break
    sleep 0.5
done
pkill -9 -f '/opt/86box/usr/local/bin/86Box' 2>/dev/null || true
sleep 0.5

cd /work
nohup /opt/86box/AppRun --config /work/86box.cfg --vmpath /work --rompath /roms --noconfirm \
    >>/work/86box.log 2>&1 &
# record the REAL binary pid, not the AppRun wrapper pid
sleep 3
PID=$(pgrep -f '/opt/86box/usr/local/bin/86Box' | head -1)
echo "${PID:-unknown}" > /tmp/86box.pid
N=$(pgrep -cf '/opt/86box/usr/local/bin/86Box')
echo "start86: 86Box launched, pid $(cat /tmp/86box.pid), instances now: $N, log /work/86box.log"
