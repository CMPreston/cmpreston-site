#!/usr/bin/env python3
"""Crop a full Xvfb-root screenshot down to the exact 640x480 SheepShaver
guest framebuffer region and save losslessly. The guest's (0,0) sits at
root (192,144) in this rig's window layout (borderless SDL window under
Xvfb) -- verified once via bounding-box analysis of a full-desktop capture,
reused here rather than recomputed per shot for speed.

Usage: crop_guest.py <in.png> <out.png>
"""
import sys
from PIL import Image

GX0, GY0 = 192, 144
GW, GH = 640, 480

def main():
    src, dst = sys.argv[1], sys.argv[2]
    im = Image.open(src).convert('RGB')
    crop = im.crop((GX0, GY0, GX0 + GW, GY0 + GH))
    assert crop.size == (GW, GH), crop.size
    crop.save(dst)
    print(f"{src} -> {dst} {crop.size}")

if __name__ == '__main__':
    main()
