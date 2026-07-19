#!/bin/bash
# Container entrypoint: bring up Xvfb on :99, optionally autostart 86Box, stay alive.
set -u

mkdir -p /tmp/xdg && chmod 700 /tmp/xdg
rm -f /tmp/.X99-lock

Xvfb :99 -screen 0 1024x768x24 -nolisten tcp &
XVFB_PID=$!

# Wait until the display answers
for _ in $(seq 1 100); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then break; fi
    sleep 0.1
done
echo "entrypoint: Xvfb up on :99 (pid $XVFB_PID)"

if [ "${AUTOSTART:-1}" = "1" ] && [ -f /work/86box.cfg ]; then
    /usr/local/bin/start86.sh
fi

# Keep the container alive regardless of what 86Box does
exec tail -f /dev/null
