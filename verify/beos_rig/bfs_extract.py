#!/usr/bin/env python3
"""bfs_extract.py -- minimal read-only BFS (Be File System) reader / font extractor.

Pure Python 3 stdlib. Reads a raw BFS volume image (little-endian / x86 BeOS),
resolves a directory path via the BFS directory B+trees, and extracts TrueType
fonts, identifying them by parsing the TTF 'name' table.

Layout references: Dominic Giampaolo, "Practical File System Design with the
Be File System" (BFS chapters), cross-checked byte-for-byte against a real
BeOS 5 Pro volume image (all field offsets below were verified empirically
against on-disk ground truth: superblock magics, inode magic 0x3bbe0ad9,
root inode self-reference, B+tree root node of the root directory).

On-disk essentials (all little-endian on x86 volumes, structs packed --
int64 fields sit at 4-byte alignment, verified against the real volume):

  block_run (8 bytes):  int32 allocation_group; uint16 start; uint16 len
      absolute block = (allocation_group << ag_shift) + start

  disk_super_block (at byte 512 of the volume):
      +0   char  name[32]
      +32  int32 magic1        0x42465331 'BFS1'
      +36  int32 fs_byte_order
      +40  uint32 block_size   +44 uint32 block_shift
      +48  off_t num_blocks    +56 off_t used_blocks
      +64  int32 inode_size    +68 int32 magic2 0xdd121031
      +72  int32 blocks_per_ag +76 int32 ag_shift +80 int32 num_ags
      +84  int32 flags         +88 block_run log_blocks
      +96  off_t log_start     +104 off_t log_end
      +112 int32 magic3 0x15b6830e
      +116 block_run root_dir  +124 block_run indices

  bfs_inode (one per file, at start of the block its block_run addresses):
      +0   int32 magic1 0x3bbe0ad9
      +4   block_run inode_num   +12 uid +16 gid +20 mode +24 flags
      +28  bigtime create_time   +36 bigtime last_modified_time
      +44  block_run parent      +52 block_run attributes
      +60  uint32 type           +64 int32 inode_size  +68 etc (kernel ptr)
      +72  data_stream:
             block_run direct[12]            (+72 .. +168)
             +168 off_t max_direct_range     +176 block_run indirect
             +184 off_t max_indirect_range   +192 block_run double_indirect
             +200 off_t max_double_indirect_range
             +208 off_t size
      +232 small_data area (attrs in inode; unused here)

  Directory = B+tree stored in the directory inode's data stream.
      bplustree_header (stream offset 0):
        uint32 magic 0x69f6c2e8; uint32 node_size (1024); uint32 max_levels;
        uint32 data_type; int64 root_node_pointer; int64 free_node_pointer;
        int64 maximum_size
      bplustree_node (at stream offsets given by node pointers):
        int64 left_link; int64 right_link; int64 overflow_link;
        uint16 all_key_count; uint16 all_key_length        (28-byte header)
        then: packed key bytes (all_key_length total),
              pad to alignment (8-byte in Haiku's impl; auto-detected here
              and validated, since 4 vs 8 is ambiguous in the literature),
              uint16 key_end_offsets[all_key_count] (cumulative ends),
              int64 values[all_key_count].
        Leaf nodes have overflow_link == -1; their values are the absolute
        BLOCK numbers of the entries' inodes. Internal-node values are byte
        offsets of child nodes within the tree stream; values[0] is the
        leftmost child, so full enumeration = descend leftmost, then follow
        right_link across the leaf chain. (Enumeration + name matching is
        used for path lookup too -- BeOS directories are small, and this
        sidesteps every key-comparison subtlety of a search descent.)

Fallback: --scan ignores directories entirely and sweeps every block of the
volume for the inode magic, extracting any regular file whose content sniffs
as a TrueType font (names then come only from the TTF name table).

Usage:
  bfs_extract.py VOLUME OUTDIR [--dir /beos/etc/fonts/ttfonts]
                 [--match REGEX] [--all] [--list-only] [--scan] [--offset N]

Default --match extracts the Swiss 721 family and Dutch 801 (Bitstream).
Exit code 0 on success (>=1 font extracted or listed), 1 on failure.
"""

import argparse
import hashlib
import re
import struct
import sys
from pathlib import Path

# ---------------------------------------------------------------- constants

SUPERBLOCK_OFFSET = 512
SB_MAGIC1 = 0x42465331          # 'BFS1'
SB_MAGIC2 = 0xDD121031
SB_MAGIC3 = 0x15B6830E
INODE_MAGIC = 0x3BBE0AD9
BTREE_MAGIC = 0x69F6C2E8
BPLUSTREE_NULL = -1

S_IFMT = 0o170000
S_IFDIR = 0o040000
S_IFREG = 0o100000
S_IFLNK = 0o120000

INODE_IN_USE = 0x00000001
INODE_DELETED = 0x00000002

TTF_SIGNATURES = (b"\x00\x01\x00\x00", b"true", b"OTTO", b"ttcf")

DEFAULT_DIR = "/beos/etc/fonts/ttfonts"
DEFAULT_MATCH = r"(?i)swis{1,2}[\s_-]?721|dutch[\s_-]?801"

# ------------------------------------------------------------- struct forms

BLOCK_RUN = struct.Struct("<iHH")                       # ag, start, len
SB_FMT = struct.Struct("<32sIIIIqqiIiiiI8sqqI8s8s")     # through indices
INODE_FMT = struct.Struct("<I8siiIIqq8s8sIiI")          # header through etc
DATASTREAM_FMT = struct.Struct("<" + "8s" * 12 + "q8sq8sqq")
BT_HEADER = struct.Struct("<IIIIqqq")
BT_NODE = struct.Struct("<qqqHH")


class BFSError(Exception):
    pass


class BlockRun:
    __slots__ = ("ag", "start", "len")

    def __init__(self, raw):
        self.ag, self.start, self.len = BLOCK_RUN.unpack(raw)

    def block(self, ag_shift):
        return (self.ag << ag_shift) + self.start

    def __repr__(self):
        return f"run({self.ag},{self.start},{self.len})"


class DataStream:
    def __init__(self, raw216):
        f = DATASTREAM_FMT.unpack(raw216)
        self.direct = [BlockRun(r) for r in f[0:12]]
        self.max_direct_range = f[12]
        self.indirect = BlockRun(f[13])
        self.max_indirect_range = f[14]
        self.double_indirect = BlockRun(f[15])
        self.max_double_indirect_range = f[16]
        self.size = f[17]


class Inode:
    def __init__(self, raw, block):
        (self.magic1, inode_num, self.uid, self.gid, self.mode, self.flags,
         self.create_time, self.last_modified_time, parent, attributes,
         self.type, self.inode_size, _etc) = INODE_FMT.unpack_from(raw, 0)
        self.inode_num = BlockRun(inode_num)
        self.parent = BlockRun(parent)
        self.attributes = BlockRun(attributes)
        self.data = DataStream(raw[72:72 + DATASTREAM_FMT.size])
        self.block = block          # absolute block this inode lives at

    @property
    def is_dir(self):
        return (self.mode & S_IFMT) == S_IFDIR

    @property
    def is_file(self):
        return (self.mode & S_IFMT) == S_IFREG


class BFSVolume:
    """Read-only accessor for a raw BFS volume image."""

    def __init__(self, path, offset=0):
        self.fh = open(path, "rb")
        self.offset = offset        # byte offset of the volume in the image
        raw = self._read_at(SUPERBLOCK_OFFSET, SB_FMT.size)
        (name, magic1, self.fs_byte_order, self.block_size, self.block_shift,
         self.num_blocks, self.used_blocks, self.inode_size, magic2,
         self.blocks_per_ag, self.ag_shift, self.num_ags, self.flags,
         _log_blocks, self.log_start, self.log_end, magic3,
         root_dir, indices) = SB_FMT.unpack(raw)
        if magic1 != SB_MAGIC1 or magic2 != SB_MAGIC2 or magic3 != SB_MAGIC3:
            raise BFSError(
                f"bad superblock magics: {magic1:#x} {magic2:#x} {magic3:#x}")
        if self.block_size != (1 << self.block_shift):
            raise BFSError("block_size / block_shift mismatch")
        self.name = name.split(b"\0", 1)[0].decode("utf-8", "replace")
        self.root_dir = BlockRun(root_dir)
        self.indices = BlockRun(indices)
        self._btree_align = None    # lazily detected: 8 or 4

    # -- raw access ---------------------------------------------------------

    def _read_at(self, pos, n):
        self.fh.seek(self.offset + pos)
        data = self.fh.read(n)
        if len(data) != n:
            raise BFSError(f"short read at {pos} ({len(data)}/{n})")
        return data

    def read_blocks(self, block, count=1):
        if not (0 <= block and block + count <= self.num_blocks):
            raise BFSError(f"block range {block}+{count} out of volume")
        return self._read_at(block * self.block_size, count * self.block_size)

    def read_run(self, run):
        return self.read_blocks(run.block(self.ag_shift), run.len)

    # -- inodes and file content -------------------------------------------

    def read_inode(self, block):
        raw = self.read_blocks(block)
        ino = Inode(raw, block)
        if ino.magic1 != INODE_MAGIC:
            raise BFSError(f"no inode magic at block {block}")
        return ino

    def inode_from_run(self, run):
        return self.read_inode(run.block(self.ag_shift))

    def _runs_in_array(self, run):
        """Yield the block_runs packed inside an indirect-array run."""
        raw = self.read_run(run)
        for off in range(0, len(raw), BLOCK_RUN.size):
            r = BlockRun(raw[off:off + BLOCK_RUN.size])
            if r.len == 0:
                continue            # unused slot
            yield r

    def read_file(self, ino):
        """Return exactly data.size bytes of the inode's data stream."""
        ds = ino.data
        if not (0 <= ds.size <= self.num_blocks * self.block_size):
            raise BFSError(f"implausible file size {ds.size}")
        out = bytearray()

        def want_more():
            return len(out) < ds.size

        for run in ds.direct:
            if run.len == 0 or not want_more():
                break
            out += self.read_run(run)
        if want_more() and ds.indirect.len:
            for run in self._runs_in_array(ds.indirect):
                if not want_more():
                    break
                out += self.read_run(run)
        if want_more() and ds.double_indirect.len:
            # double-indirect: array of runs -> each an indirect array of
            # data runs. BFS fills these strictly in file order, so
            # sequential concatenation is correct for regular files.
            for arr_run in self._runs_in_array(ds.double_indirect):
                if not want_more():
                    break
                for run in self._runs_in_array(arr_run):
                    if not want_more():
                        break
                    out += self.read_run(run)
        if len(out) < ds.size:
            raise BFSError(f"file data short: {len(out)} < {ds.size}")
        return bytes(out[:ds.size])

    # -- directory B+trees --------------------------------------------------

    def _node_arrays(self, tree, off, count, key_len):
        """Locate key_ends[] / values[] after the packed keys, handling the
        4-vs-8 byte alignment ambiguity by validating against ground truth:
        key_ends must be non-decreasing, start > 0, and end == key_len."""
        base = off + BT_NODE.size + key_len

        def attempt(align):
            p = (base + align - 1) & ~(align - 1)
            if p + 2 * count + 8 * count > len(tree):
                return None
            ends = struct.unpack_from(f"<{count}H", tree, p)
            if count and (ends[-1] != key_len or ends[0] == 0
                          or any(b < a for a, b in zip(ends, ends[1:]))):
                return None
            vals = struct.unpack_from(f"<{count}q", tree, p + 2 * count)
            return ends, vals

        order = (8, 4) if self._btree_align != 4 else (4, 8)
        for align in order:
            got = attempt(align)
            if got is not None:
                if self._btree_align is None and count:
                    self._btree_align = align
                return got
        raise BFSError(f"b+tree node at {off}: cannot locate key arrays")

    def iter_dir(self, dir_inode):
        """Yield (name_bytes, inode_block) for every entry of a directory."""
        if not dir_inode.is_dir:
            raise BFSError("not a directory")
        tree = self.read_file(dir_inode)
        (magic, node_size, _levels, _dtype, root_ptr,
         _free_ptr, _max_size) = BT_HEADER.unpack_from(tree, 0)
        if magic != BTREE_MAGIC:
            raise BFSError(f"bad b+tree magic {magic:#x}")

        def node(off):
            if not (0 < off <= len(tree) - BT_NODE.size):
                raise BFSError(f"b+tree node pointer {off} out of stream")
            left, right, overflow, count, key_len = BT_NODE.unpack_from(
                tree, off)
            return left, right, overflow, count, key_len

        # descend to the leftmost leaf
        seen = set()
        off = root_ptr
        left, right, overflow, count, key_len = node(off)
        while overflow != BPLUSTREE_NULL:        # internal node
            if off in seen or count < 1:
                raise BFSError("b+tree descent loop / empty internal node")
            seen.add(off)
            _ends, vals = self._node_arrays(tree, off, count, key_len)
            off = vals[0]                        # leftmost child
            left, right, overflow, count, key_len = node(off)

        # walk the leaf chain left to right
        seen = set()
        while True:
            if off in seen:
                raise BFSError("b+tree leaf chain loop")
            seen.add(off)
            ends, vals = self._node_arrays(tree, off, count, key_len)
            key_base = off + BT_NODE.size
            prev = 0
            for i in range(count):
                name = tree[key_base + prev:key_base + ends[i]]
                prev = ends[i]
                yield name, vals[i]
            off = right
            if off == BPLUSTREE_NULL or off <= 0:
                break
            left, right, overflow, count, key_len = node(off)

    def resolve(self, path):
        """Resolve an absolute path to an Inode (no symlink following)."""
        ino = self.inode_from_run(self.root_dir)
        for comp in [c for c in path.split("/") if c]:
            target = comp.encode("utf-8")
            hit = None
            for name, block in self.iter_dir(ino):
                if name == target:
                    hit = block
                    break
            if hit is None:
                raise BFSError(f"path component not found: {comp!r} in {path}")
            ino = self.read_inode(hit)
        return ino


# ------------------------------------------------------- TrueType name table

def ttf_names(data):
    """Parse a TrueType/OpenType 'name' table (big-endian). Returns
    {'full': str, 'family': str, 'ps': str, 'all': [str...], 'ok': bool}
    or None if data is not sfnt-shaped. Pure struct, bounds-checked."""
    if len(data) < 12 or data[:4] not in TTF_SIGNATURES:
        return None
    base = 0
    if data[:4] == b"ttcf":                       # collection: use first font
        if len(data) < 16:
            return None
        base = struct.unpack_from(">I", data, 12)[0]
        if base + 12 > len(data):
            return None
    num_tables = struct.unpack_from(">H", data, base + 4)[0]
    name_off = name_len = None
    ok = True
    for i in range(num_tables):
        rec = base + 12 + 16 * i
        if rec + 16 > len(data):
            ok = False
            break
        tag, _chk, off, length = struct.unpack_from(">4sIII", data, rec)
        if off + length > len(data):
            ok = False                            # structural damage signal
            continue
        if tag == b"name":
            name_off, name_len = off, length
    result = {"full": "", "family": "", "ps": "", "all": [], "ok": ok}
    if name_off is None or name_off + 6 > len(data):
        result["ok"] = False
        return result
    _fmt, count, str_off = struct.unpack_from(">HHH", data, name_off)
    storage = name_off + str_off
    best = {}                                     # nameID -> (score, text)
    for i in range(count):
        rec = name_off + 6 + 12 * i
        if rec + 12 > len(data):
            result["ok"] = False
            break
        plat, enc, lang, nid, slen, soff = struct.unpack_from(
            ">6H", data, rec)
        lo, hi = storage + soff, storage + soff + slen
        if hi > len(data):
            continue
        raw = data[lo:hi]
        if plat in (0, 3):
            text = raw.decode("utf-16-be", "replace")
        else:
            try:
                text = raw.decode("mac_roman")
            except UnicodeDecodeError:
                text = raw.decode("latin-1", "replace")
        text = text.strip("\0").strip()
        if not text:
            continue
        # prefer Microsoft/English (3,0x409), then Mac/English (1,0)
        score = (2 if (plat == 3 and lang == 0x409)
                 else 1 if (plat == 1 and lang == 0) else 0)
        if score >= best.get(nid, (-1, ""))[0]:
            best[nid] = (score, text)
        if text not in result["all"]:
            result["all"].append(text)
    result["family"] = best.get(1, (0, ""))[1]
    result["full"] = best.get(4, (0, ""))[1]
    result["ps"] = best.get(6, (0, ""))[1]
    return result


# ------------------------------------------------------------------ helpers

def sniff_ttf(data):
    return len(data) >= 12 and data[:4] in TTF_SIGNATURES


def safe_name(name):
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "unnamed"


def sha256_short(data, n=12):
    return hashlib.sha256(data).hexdigest()[:n]


# -------------------------------------------------------------------- modes

def collect_via_tree(vol, dir_path):
    """Primary mode: enumerate dir_path via the directory B+trees.
    Returns list of dicts (one per regular file entry)."""
    dnode = vol.resolve(dir_path)
    found = []
    for name, block in vol.iter_dir(dnode):
        if name in (b".", b".."):
            continue
        ino = vol.read_inode(block)
        if not ino.is_file:
            continue
        found.append({"name": name.decode("utf-8", "replace"),
                      "inode": ino})
    return found


def collect_via_scan(vol):
    """Fallback mode: sweep every block for inode magic; keep regular files
    whose first data bytes sniff as a TrueType font. Names are unknown at
    this level (BFS keeps names only in directory trees)."""
    found = []
    for block in range(1, vol.num_blocks):
        try:
            head = vol._read_at(block * vol.block_size, 4)
        except BFSError:
            break
        if struct.unpack("<I", head)[0] != INODE_MAGIC:
            continue
        try:
            ino = vol.read_inode(block)
        except BFSError:
            continue
        if (not ino.is_file or ino.flags & INODE_DELETED
                or not ino.flags & INODE_IN_USE):
            continue
        if not (12 <= ino.data.size <= 32 * 1024 * 1024):
            continue
        run = ino.data.direct[0]
        if run.len == 0:
            continue
        try:
            first = vol._read_at(
                run.block(vol.ag_shift) * vol.block_size, 4)
        except BFSError:
            continue
        if first in TTF_SIGNATURES or first[:4] == b"\x00\x01\x00\x00":
            found.append({"name": f"font-{block}.ttf", "inode": ino})
    return found


# ---------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Extract TrueType fonts from a raw BFS (BeOS) volume.")
    ap.add_argument("volume", help="raw BFS volume image")
    ap.add_argument("outdir", help="directory to write extracted fonts into")
    ap.add_argument("--dir", default=DEFAULT_DIR,
                    help=f"volume directory to read (default {DEFAULT_DIR})")
    ap.add_argument("--match", default=DEFAULT_MATCH,
                    help="regex (case-insensitive-ready) matched against the "
                         "on-disk filename and every name-table string; "
                         "matching fonts are extracted")
    ap.add_argument("--all", action="store_true",
                    help="extract every TTF found, not just --match hits")
    ap.add_argument("--list-only", action="store_true",
                    help="list fonts, write nothing")
    ap.add_argument("--scan", action="store_true",
                    help="skip directories; brute-force scan all blocks for "
                         "TTF-bearing inodes")
    ap.add_argument("--offset", type=int, default=0,
                    help="byte offset of the BFS volume inside the image "
                         "(default 0 = raw volume)")
    args = ap.parse_args(argv)

    vol = BFSVolume(args.volume, args.offset)
    print(f"volume: {vol.name!r}  block_size={vol.block_size} "
          f"num_blocks={vol.num_blocks} ag_shift={vol.ag_shift}")

    mode = "scan"
    if args.scan:
        entries = collect_via_scan(vol)
    else:
        try:
            entries = collect_via_tree(vol, args.dir)
            mode = "b+tree"
        except BFSError as e:
            print(f"WARNING: b+tree walk failed ({e}); "
                  f"falling back to full-volume scan", file=sys.stderr)
            entries = collect_via_scan(vol)
    print(f"mode: {mode}  candidates: {len(entries)}")

    matcher = re.compile(args.match)
    outdir = Path(args.outdir)
    rows, extracted = [], 0
    for ent in sorted(entries, key=lambda e: e["name"].lower()):
        data = vol.read_file(ent["inode"])
        if not sniff_ttf(data):
            continue
        info = ttf_names(data) or {"full": "", "family": "", "ps": "",
                                   "all": [], "ok": False}
        haystack = " ".join([ent["name"]] + info["all"])
        hit = bool(matcher.search(haystack))
        take = args.all or hit
        status = "-"
        if take and not args.list_only:
            outdir.mkdir(parents=True, exist_ok=True)
            out = outdir / safe_name(ent["name"])
            out.write_bytes(data)
            extracted += 1
            status = "EXTRACTED"
        elif take:
            status = "match"
        rows.append((ent["name"], info["full"] or info["family"] or "?",
                     len(data), sha256_short(data),
                     "" if info["ok"] else "(damaged?)", status))

    namew = max([len(r[0]) for r in rows] + [8])
    fullw = max([len(r[1]) for r in rows] + [9])
    print(f"\n{'file':<{namew}}  {'full name':<{fullw}}  "
          f"{'bytes':>8}  sha256-12     note")
    for r in rows:
        print(f"{r[0]:<{namew}}  {r[1]:<{fullw}}  {r[2]:>8}  {r[3]}  "
              f"{r[4]}{r[5] if r[5] != '-' else ''}")
    print(f"\n{len(rows)} TrueType fonts found; {extracted} extracted "
          f"to {outdir}")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
