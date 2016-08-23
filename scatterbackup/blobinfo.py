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
import zlib


class BlobInfo:

    def __init__(self, size, md5=None, sha1=None, crc32=None):
        self.size = size
        self.sha1 = sha1
        self.md5 = md5
        self.crc32 = crc32

    def __eq__(self, other):
        sha1_ok = ((self.sha1 is not None and other.sha1 is not None) and
                   self.sha1 == other.sha1)
        md5_ok = ((self.md5 is not None and other.md5 is not None) and
                  self.md5 == other.md5)
        crc32_ok = ((self.crc32 is not None and other.crc32 is not None) and
                    self.crc32 == other.crc32)

        return (self.size == other.size and
                (sha1_ok or md5_ok or crc32_ok))

    @staticmethod
    def from_file(path):
        """Calculate size, md5 and sha1 for a given file"""
        size = 0
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        crc32 = 0
        with open(path, 'rb') as fin:
            data = fin.read(65536)
            while data:
                size += len(data)
                md5.update(data)
                sha1.update(data)
                crc32 = zlib.crc32(data, crc32)
                data = fin.read(65536)

        md5_hex = md5.hexdigest()
        sha1_hex = sha1.hexdigest()

        return BlobInfo(size, md5_hex, sha1_hex, crc32)


# EOF #
