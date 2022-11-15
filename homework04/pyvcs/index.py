import hashlib
import operator
import os
import pathlib
import struct
import typing as tp

from pyvcs.objects import hash_object


class GitIndexEntry(tp.NamedTuple):
    # @see: https://github.com/git/git/blob/master/Documentation/technical/index-format.txt
    ctime_s: int
    ctime_n: int
    mtime_s: int
    mtime_n: int
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
    sha1: bytes
    flags: int
    name: str

    def pack(self) -> bytes:
        pack = struct.pack(">IIIIIIIIII", self.ctime_s, self.ctime_n, self.mtime_s, self.mtime_n, self.dev, self.ino,
                           self.mode,
                           self.uid, self.gid, self.size) + self.sha1 + struct.pack(">H",
                                                                                    self.flags) + self.name.encode() + b"\x00\x00\x00"
        return pack

    @staticmethod
    def unpack(data: bytes) -> "GitIndexEntry":
        ctime_s, ctime_n, mtime_s, mtime_n, dev, ino, mode, uid, gid, size = struct.unpack(">IIIIIIIIII", data[:40])
        sha1 = data[40:60]
        flags = struct.unpack(">H", data[60:62])[0]
        name = data[62:data[62:].index(b"\x00\x00\x00") + 62].decode("ascii")
        return GitIndexEntry(
            ctime_s, ctime_n, mtime_s, mtime_n, dev, ino, mode, uid, gid, size, sha1, flags, name
        )


def read_index(gitdir: pathlib.Path) -> tp.List[GitIndexEntry]:
    if not pathlib.Path(gitdir / "index").is_file():
        return []
    with open(gitdir / "index", "rb") as f:
        b = f.read()
        l = struct.unpack(">I", b[8:12])[0]
        data = b[12:]
        arr = []
        for i in range(l):
            arr.append(GitIndexEntry.unpack(data))
            index = data.index(arr[-1].name.encode()) + len(arr[-1].name) + 3
            data = data[index:]
        return arr


def write_index(gitdir: pathlib.Path, entries: tp.List[GitIndexEntry]) -> None:
    with open(gitdir / "index", "wb") as f:
        all = b""
        all += b"DIRC"
        all += struct.pack(">I", 2)
        all += struct.pack(">I", len(entries))
        for i in entries:
            all += i.pack()
        all += hashlib.sha1(all).digest()
        f.write(all)


def ls_files(gitdir: pathlib.Path, details: bool = False) -> None:
    res = read_index(gitdir)
    for i in res:
        if details:
            print("100644 " + i.sha1.hex() + " 0\t" + i.name, flush=True)
        else:
            print(i.name, flush=True)


def update_index(gitdir: pathlib.Path, paths: tp.List[pathlib.Path], write: bool = True) -> None:
    objects = []
    for i in paths:
        path = pathlib.Path(i)
        stats = os.stat(path)

        with open(path, "rb") as f:
            hash = hash_object(f.read(), "blob", True)

        e = GitIndexEntry(
            ctime_s=int(stats.st_ctime),
            ctime_n=int(stats.st_ctime),
            mtime_s=int(stats.st_mtime),
            mtime_n=int(stats.st_mtime),
            dev=stats.st_dev,
            ino=stats.st_ino,
            mode=stats.st_mode,
            uid=stats.st_uid,
            gid=stats.st_uid,
            size=stats.st_size,
            sha1=bytes.fromhex(hash),
            flags=0,
            name=str(path).replace("\\", "/")
        )

        objects.append(e)
    objects.sort(key=lambda x: x.name)
    if not (gitdir / "index").exists():
        write_index(gitdir, objects)
    else:
        index = read_index(gitdir)
        index += objects
        write_index(gitdir, index)