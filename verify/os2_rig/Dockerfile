FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb xauth x11-utils xdotool imagemagick procps \
    fonts-dejavu-core \
    libxcb1 libx11-6 libx11-xcb1 libxext6 libxrender1 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-render0 libxcb-shape0 \
    libxcb-shm0 libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 \
    libxcb-xinput0 libxcb-xkb1 libxkbcommon-x11-0 libxkbcommon0 \
    libgl1 libegl1 libopengl0 libgl1-mesa-dri \
    libfontconfig1 libfreetype6 libglib2.0-0 libdbus-1-3 \
    libasound2 libpulse0 \
    && rm -rf /var/lib/apt/lists/*

# Extract the AppImage at build time (no FUSE needed)
COPY 86Box-arm64.AppImage /tmp/86Box.AppImage
RUN chmod +x /tmp/86Box.AppImage \
    && cd /opt \
    && /tmp/86Box.AppImage --appimage-extract >/dev/null \
    && mv squashfs-root 86box \
    && rm /tmp/86Box.AppImage \
    && ls -la /opt/86box/

COPY entrypoint.sh /entrypoint.sh
COPY start86.sh /usr/local/bin/start86.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/start86.sh

ENV DISPLAY=:99 \
    QT_QPA_PLATFORM=xcb \
    XDG_RUNTIME_DIR=/tmp/xdg \
    HOME=/root

ENTRYPOINT ["/entrypoint.sh"]
