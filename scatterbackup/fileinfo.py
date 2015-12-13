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


from collections import OrderedDict
from scatterbackup.blobinfo import BlobInfo
import hashlib
import json
import os
import socket
import stat
import time


class FileInfo:

    def __init__(self, path):
        self.kind = None
        self.path = path
        self.host = None

        self.dev = None
        self.ino = None

        self.mode = None
        self.nlink = None

        self.uid = None
        self.gid = None

        self.rdev = None

        self.size = None
        self.blksize = None
        self.blocks = None

        self.atime = None
        self.ctime = None
        self.mtime = None

        self.time = None

        self.blob = None
        self.target = None

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def json(self):
        # use OrderedDict to create pretty and deterministic output
        js = OrderedDict()

        if self.kind is not None: js['type'] = self.kind

        js['path'] = self.path

        if self.host is not None: js['host'] = self.host

        if self.dev is not None: js['dev'] = self.dev
        if self.ino is not None: js['ino'] = self.ino

        if self.mode is not None: js['mode'] = self.mode
        if self.nlink is not None: js['nlink'] = self.nlink

        if self.uid is not None: js['uid'] = self.uid
        if self.gid is not None: js['gid'] = self.gid

        if self.rdev is not None: js['rdev'] = self.rdev

        if self.size is not None: js['size'] = self.size
        if self.blksize is not None: js['blksize'] = self.blksize
        if self.blocks is not None: js['blocks'] = self.blocks

        if self.atime is not None: js['atime'] = self.atime
        if self.ctime is not None: js['ctime'] = self.ctime
        if self.mtime is not None: js['mtime'] = self.mtime

        if self.blob is not None:
            js['blob'] = OrderedDict([('size', self.size)])
            if self.blob.sha1 is not None: js['blob']['sha1'] = self.blob.sha1
            if self.blob.md5 is not None: js['blob']['md5'] = self.blob.md5

        if self.target is not None:
            js['target'] = self.target

        if self.time is not None: js['time'] = self.time

        return json.dumps(js)

    @staticmethod
    def from_file(path, checksums=True, relative=False, host=None):
        abspath = path if relative else os.path.abspath(path)

        result = FileInfo(abspath)

        if host is None:
            result.host = socket.getfqdn()
        elif host == "":
            result.host = None
        else:
            result.host = host

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
    def from_json(text):
        js = json.loads(text)
        path = js.get('path')

        result = FileInfo(path)
        result.kind = js.get('type')
        result.host = js.get('host')
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
                                   sha1=blob.get('sha1'))

        result.target = js.get('target')

        return result

# EOF #
