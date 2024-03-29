# ScatterBackup - A chaotic backup solution
# Copyright (C) 2015 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from typing import Any, Optional

import json
import os
import stat
import time

from collections import OrderedDict
from scatterbackup.blobinfo import BlobInfo


class FileInfo:

    def __init__(self, path: str) -> None:
        self.rowid: Optional[int] = None

        self.kind: Optional[str] = None
        self.path: str = path

        self.dev: Optional[int] = None  # FIXME: this is not stable across reboots
        self.ino: Optional[int] = None

        self.mode: Optional[int] = None
        self.nlink: Optional[int] = None

        self.uid: Optional[int] = None
        self.gid: Optional[int] = None

        self.rdev: Optional[int] = None

        self.size: Optional[int] = None
        self.blksize: Optional[int] = None
        self.blocks: Optional[int] = None

        self.atime: Optional[float] = None
        self.ctime: Optional[float] = None
        self.mtime: Optional[float] = None

        self.time: Optional[float] = None

        self.birth: Optional[int] = None
        self.death: Optional[int] = None

        self.blob: Optional[BlobInfo] = None
        self.target: Optional[str] = None

        self.directory_id: Optional[int] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FileInfo):
            return False

        return (
            self.kind == other.kind and
            self.path == other.path and

            # dev does not stay permanent across reboots
            # self.dev == other.dev and
            self.ino == other.ino and

            self.mode == other.mode and
            self.nlink == other.nlink and

            self.uid == other.uid and
            self.gid == other.gid and

            self.rdev == other.rdev and

            self.size == other.size and
            self.blksize == other.blksize and
            self.blocks == other.blocks and

            # atime creates to much bloat in db if each change is recorded
            # self.atime == other.atime and

            self.ctime == other.ctime and
            self.mtime == other.mtime and

            # creation time of the FileInfo is not relevant
            # self.time == other.time and

            self.blob == other.blob and
            self.target == other.target)

    def to_js_dict(self) -> OrderedDict[str, Any]:
        # use OrderedDict to create pretty and deterministic output
        js = OrderedDict()

        def assign(name: str, value: Any) -> None:
            if value is not None:
                js[name] = value

        assign('type', self.kind)
        assign('path', self.path)

        assign('dev', self.dev)
        assign('ino', self.ino)

        assign('mode', self.mode)
        assign('nlink', self.nlink)

        assign('uid', self.uid)
        assign('gid', self.gid)

        assign('rdev', self.rdev)

        assign('size', self.size)
        assign('blksize', self.blksize)
        assign('blocks', self.blocks)

        assign('atime', self.atime)
        assign('ctime', self.ctime)
        assign('mtime', self.mtime)

        if self.blob is not None:
            js['blob'] = OrderedDict([('size', self.size)])
            if self.blob.sha1 is not None:
                js['blob']['sha1'] = self.blob.sha1  # type: ignore
            if self.blob.md5 is not None:
                js['blob']['md5'] = self.blob.md5  # type: ignore
            if self.blob.crc32 is not None:
                js['blob']['crc32'] = self.blob.crc32  # type: ignore

        assign('target', self.target)

        assign('time', self.time)

        return js

    def json(self) -> str:
        js = self.to_js_dict()
        return json.dumps(js)

    def calc_checksums(self) -> None:
        statinfo = os.lstat(self.path)
        if stat.S_ISREG(statinfo.st_mode):
            self.blob = BlobInfo.from_file(self.path)

    @staticmethod
    def from_file(path: str, checksums: bool = True, relative: bool = False, base: Optional[str] = None) -> 'FileInfo':
        abspath = path if relative else os.path.abspath(path)

        result = FileInfo(abspath)

        statinfo = os.lstat(path)

        m = statinfo.st_mode
        if stat.S_ISREG(m):
            result.kind = "file"
        elif stat.S_ISDIR(m):
            result.kind = "directory"
        elif stat.S_ISCHR(m):
            result.kind = "chardev"
        elif stat.S_ISBLK(m):
            result.kind = "blockdev"
        elif stat.S_ISFIFO(m):
            result.kind = "fifo"
        elif stat.S_ISLNK(m):
            result.kind = "link"
        elif stat.S_ISSOCK(m):
            result.kind = "socket"
        else:
            result.kind = "unknown"

        result.dev = statinfo.st_dev
        result.ino = statinfo.st_ino

        result.mode = statinfo.st_mode
        result.nlink = statinfo.st_nlink

        result.uid = statinfo.st_uid
        result.gid = statinfo.st_gid

        result.rdev = statinfo.st_rdev

        result.size = statinfo.st_size
        result.blksize = statinfo.st_blksize
        result.blocks = statinfo.st_blocks

        result.atime = statinfo.st_atime_ns
        result.ctime = statinfo.st_ctime_ns
        result.mtime = statinfo.st_mtime_ns

        result.time = int(round(time.time() * 1000000000))

        if stat.S_ISREG(statinfo.st_mode) and checksums:
            result.blob = BlobInfo.from_file(abspath)
        elif stat.S_ISLNK(statinfo.st_mode):
            result.target = os.readlink(abspath)

        return result

    @staticmethod
    def from_json(text: str) -> 'FileInfo':
        js = json.loads(text)
        path = js.get('path')

        result = FileInfo(path)
        result.kind = js.get('type')
        result.dev = js.get('dev')
        result.ino = js.get('ino')

        result.mode = js.get('mode')
        result.nlink = js.get('nlink')

        result.uid = js.get('uid')
        result.gid = js.get('gid')

        result.rdev = js.get('rdev')

        result.size = js.get('size')
        result.blksize = js.get('blksize')
        result.blocks = js.get('blocks')

        result.atime = js.get('atime')
        result.ctime = js.get('ctime')
        result.mtime = js.get('mtime')

        result.time = js.get('time')

        blob = js.get('blob')
        if blob is not None:
            result.blob = BlobInfo(blob.get('size'),
                                   md5=blob.get('md5'),
                                   sha1=blob.get('sha1'),
                                   crc32=blob.get('crc32'))

        result.target = js.get('target')

        return result

    def __repr__(self) -> str:
        return "FileInfo({!r})".format(self.path)


# EOF #
