# ScatterBackup - A chaotic backup solution
# Copyright (C) 2016 Ingo Ruhnke <grumbel@gmail.com>
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


from scatterbackup.units import bytes2human_decimal, bytes2human_binary, units


class Bytes:

    def __init__(self, count):
        self.count = count

    def __format__(self, spec):
        r = spec.rsplit(":", maxsplit=1)
        str_spec, unit = r if len(r) == 2 else (r[0], "h")
        return format(self.as_str(unit), str_spec)

    def as_str(self, unit):
        if unit == "h":
            return bytes2human_decimal(self.count)
        elif unit == "H":
            return bytes2human_binary(self.count)
        elif unit == "r":
            return "{}".format(self.count)
        elif unit == "B":
            return "{}{}".format(self.count, unit)
        elif unit in units:
            return "{:.2f}{}".format(self.count / units[unit], unit)
        else:
            raise Exception("unknown unit: {}".format(unit))


class Checksum:

    def __init__(self, checksum):
        self.checksum = checksum

    def __format__(self, spec):
        r = spec.rsplit(":", maxsplit=1)
        if len(r) == 2:
            str_spec = r[0]
            cut = int(r[1])
        else:
            str_spec = r[0]
            cut = None

        return format(self.checksum[0:cut], str_spec)


class FileInfoFormatter:

    def __init__(self, fileinfo):
        self.fileinfo = fileinfo

    def __getitem__(self, key):
        # FIXME: potential security hole
        return self.__getattribute__(key)()

    def path(self): return self.fileinfo.path

    def dev(self): return self.fileinfo.dev
    def ino(self): return self.fileinfo.ino

    def mode(self): return self.fileinfo.mode
    def nlink(self): return self.fileinfo.nlink

    def uid(self): return self.fileinfo.uid
    def gid(self): return self.fileinfo.gid

    def rdev(self): return self.fileinfo.rdev

    def size(self): return Bytes(self.fileinfo.size)
    def blksize(self): return self.fileinfo.blksize
    def blocks(self): return self.fileinfo.blocks

    def atime(self): return self.fileinfo.atime
    def ctime(self): return self.fileinfo.ctime
    def mtime(self): return self.fileinfo.mtime

    def time(self): return self.fileinfo.time

    def birth(self): return self.fileinfo.birth
    def death(self): return self.fileinfo.death

    def sha1(self): return Checksum(self.fileinfo.blob.sha1 if self.fileinfo.blob else "<sha1:unknown>")
    def md5(self): return Checksum(self.fileinfo.blob.md5 if self.fileinfo.blob else "<md5:unknown>")

    def target(self): return self.fileinfo.target


# EOF #
