#!/bin/bash
# (Re)launch SheepShaver on :99 without touching the container.
# Modeled on verify/os2_rig/start86.sh's role (kill+relaunch, log+pid file).
set -u
export DISPLAY=:99

OLDPID="$(cat /tmp/sheepshaver.pid 2>/dev/null || true)"
if [ -n "${OLDPID}" ] && kill -0 "$OLDPID" 2>/dev/null; then
    kill "$OLDPID" 2>/dev/null
    sleep 1
fi
pkill -f '/usr/local/bin/SheepShaver' 2>/dev/null
sleep 1

cd /work
nohup /usr/local/bin/SheepShaver --config /work/sheepshaver_prefs \
    > /work/sheepshaver.log 2>&1 &
echo $! > /tmp/sheepshaver.pid
sleep 1
echo "started SheepShaver pid $(cat /tmp/sheepshaver.pid)"
