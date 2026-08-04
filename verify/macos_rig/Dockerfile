FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Same headless-GUI idiom as verify/os2_rig/Dockerfile (Xvfb + xdotool +
# ImageMagick), plus a build toolchain since SheepShaver has no upstream
# binary release and must be compiled from source here.
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb xauth x11-utils xdotool imagemagick procps \
    fonts-dejavu-core \
    build-essential autoconf automake libtool pkg-config git ca-certificates \
    libsdl2-dev libgtk-3-dev libreadline-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Fetch SheepShaver source at build time (open-source, GPLv2): the actively
# maintained fork, github.com/kanjitalk755/macemu. Recorded here for
# provenance; RIG.md pins the exact commit that was actually built.
RUN git clone --depth 1 https://github.com/kanjitalk755/macemu.git /src/macemu

# Build (Linux/Unix autotools path from macemu/README.md "How To Build").
# arm64 has no JIT backend for the PPC dynamic recompiler, so the build
# auto-selects the portable interpreter (kpx_cpu) -- same "no JIT on arm64,
# interpreter is fine" precedent the 86Box rig set for OS/2. DGA/VidMode/
# fbdev extensions are disabled since we run windowed under Xvfb (no direct
# framebuffer access), matching the OS/2 rig's windowed-not-exclusive mode.
WORKDIR /src/macemu/SheepShaver/src/Unix
# addressing=direct (base-offset host<->guest translation) instead of the
# real)-mode default: real mode requires mmap'ing the guest's low memory
# globals at literal host address 0, which is fragile on a modern 64-bit
# Linux host (mmap_min_addr, ASLR) -- it crashed (SIGSEGV) on this arm64
# container even after lowering mmap_min_addr to 0. direct mode is the
# documented, more portable alternative for exactly this class of host.
RUN ./autogen.sh \
      --enable-sdl-video --disable-sdl-audio --without-esd \
      --with-gtk=gtk3 --disable-xf86-dga --disable-xf86-vidmode \
      --disable-fbdev-dga --disable-vosf --with-mon=no \
      --enable-addressing=direct \
    && make -j"$(nproc)"

RUN install -m 0755 SheepShaver /usr/local/bin/SheepShaver

COPY entrypoint.sh /entrypoint.sh
COPY start_sheep.sh /usr/local/bin/start_sheep.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/start_sheep.sh

ENV DISPLAY=:99 \
    SDL_VIDEODRIVER=x11 \
    XDG_RUNTIME_DIR=/tmp/xdg \
    HOME=/root

ENTRYPOINT ["/entrypoint.sh"]
