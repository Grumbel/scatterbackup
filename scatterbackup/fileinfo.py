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


import hashlib
import socket
import os
import json
from collections import OrderedDict


class FileInfo:

    def __init__(self,
                 path,
                 host=None,
                 md5=None,
                 sha1=None,
                 mtime=None,
                 size=None):
        self.host = host
        self.path = path
        self.md5 = md5
        self.sha1 = sha1
        self.mtime = mtime
        self.size = size

    def json(self):
        # use OrderedDict to create pretty and deterministic output
        fileinfo = OrderedDict()
        js = OrderedDict([
            ('path', self.path),
            ('mtime', self.mtime),
            ('type', 'file'),
            ('info', fileinfo)
        ])

        if self.host:
            js['host']

        if self.md5:
            fileinfo['md5'] = self.md5
        if self.sha1:
            fileinfo['sha1'] = self.sha1
        if self.size:
            fileinfo['size'] = self.size

        return json.dumps(js)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    @staticmethod
    def from_file(path, checksums=True, relative=False, host=None):
        abspath = path if relative else os.path.abspath(path)
        if host is None:
            host = socket.getfqdn()
        elif host == "":
            host = None
        statinfo = os.lstat(path)
        mtime = statinfo.st_mtime_ns
        # st_mode=17407, st_ino=280, st_dev=23, st_nlink=1, st_uid=0, st_gid=0, st_size=1178,
        # st_atime=1449495214,
        # st_mtime=1449498613,
        # st_ctime=1449498613)

        if not checksums:
            size = statinfo.st_size
            md5_hex = None
            sha1_hex = None
        else:
            size = 0
            md5 = hashlib.md5()
            sha1 = hashlib.sha1()
            with open(path, 'rb') as fin:
                data = fin.read(65536)
                while data:
                    size += len(data)
                    md5.update(data)
                    sha1.update(data)
                    data = fin.read(16384)

            md5_hex = md5.hexdigest()
            sha1_hex = sha1.hexdigest()

        return FileInfo(path=abspath,
                        host=host,
                        mtime=mtime,
                        md5=md5_hex,
                        sha1=sha1_hex,
                        size=size)

    @staticmethod
    def from_json(text):
        js = json.loads(text)
        path = js.get('path')
        host = js.get('host')
        objtype = js.get('type')
        mtime = js.get('mtime')
        if objtype != 'file':
            raise "unknown type: {}".format(file)
        else:
            info = js['info']
            md5_hex = info.get('md5')
            sha1_hex = info.get('sha1')
            size = info.get('size')
            return FileInfo(path=path,
                            host=host,
                            mtime=mtime,
                            md5=md5_hex,
                            sha1=sha1_hex,
                            size=size)


# EOF #
