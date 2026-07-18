#!/usr/bin/env python3
"""Extract ISO9660 user data from a CloneCD raw .img (2352-byte MODE1 sectors).

stdlib only. Usage: ccd2iso.py <input.img> <output.iso>
"""
import sys

SECTOR_RAW = 2352
DATA_OFFSET = 16   # 12 sync + 4 header for MODE1
DATA_SIZE = 2048

def main():
    src, dst = sys.argv[1], sys.argv[2]
    n = 0
    with open(src, 'rb') as f, open(dst, 'wb') as out:
        while True:
            sector = f.read(SECTOR_RAW)
            if not sector:
                break
            if len(sector) != SECTOR_RAW:
                print(f"warning: trailing partial sector ({len(sector)} bytes) ignored", file=sys.stderr)
                break
            mode = sector[15]
            if mode == 1:
                out.write(sector[DATA_OFFSET:DATA_OFFSET + DATA_SIZE])
            elif mode == 2:
                out.write(sector[24:24 + 2048])  # MODE2/XA form1
            else:
                out.write(b'\x00' * DATA_SIZE)
            n += 1
    print(f"{n} sectors -> {dst}")

if __name__ == '__main__':
    main()
