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
        js = {'path': self.path}
        if self.host:
            js['host'] = self.host
        if self.md5:
            js['md5'] = self.md5
        if self.sha1:
            js['sha1'] = self.sha1
        if self.mtime:
            js['mtime'] = self.mtime
        if self.size:
            js['size'] = self.size
        return json.dumps(js)

    @staticmethod
    def from_file(path):
        abspath = os.path.abspath(path)
        host = socket.getfqdn()
        statinfo = os.stat(path)
        statinfo

        size = 0
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        with open(path, 'rb') as fin:
            data = fin.read(16384)
            while data:
                size += len(data)
                md5.update(data)
                sha1.update(data)
                data = fin.read(16384)

        return FileInfo(path=abspath,
                        host=host,
                        md5=md5.hexdigest(),
                        sha1=sha1.hexdigest(),
                        size=size)

# EOF #
