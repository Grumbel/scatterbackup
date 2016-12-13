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


import stat
import datetime
from pwd import getpwuid
from grp import getgrgid

from scatterbackup.units import bytes2human_decimal, bytes2human_binary, units
from scatterbackup.time import format_time


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


class Time:

    def __init__(self, time):
        self.time = time

    def __format__(self, spec):
        r = spec.rsplit(":", maxsplit=1)
        str_spec, time_spec = r if len(r) == 2 else (r[0], "h")

        return format(self.as_str(time_spec), str_spec)

    def as_str(self, spec):
        if spec == 'r':
            return str(self.time)
        elif spec == 'iso' or spec == 'i':
            return format_time(self.time)
        elif spec == 'h':
            if self.time is None:
                return "     <unknown>     "
            else:
                dt = datetime.datetime.fromtimestamp(self.time / 1000**3)
                return dt.strftime("%F %T")
        else:
            if self.time is None:
                return "<unknown>"
            else:
                dt = datetime.datetime.fromtimestamp(self.time / 1000**3)
                return dt.strftime(spec)


class Mode:

    def __init__(self, mode):
        self.mode = mode

    def __format__(self, spec):
        r = spec.rsplit(":", maxsplit=1)
        str_spec, spec = r if len(r) == 2 else (r[0], "h")
        return format(self.as_str(spec), str_spec)

    def as_str(self, spec):
        if spec == 'h':
            return self.as_str_human()
        else:
            return str(self.mode)

    def as_str_human(self):
        mode = self.mode
        s = ""

        if stat.S_ISDIR(mode):
            s += "d"
        elif stat.S_ISCHR(mode):
            s += "c"
        elif stat.S_ISBLK(mode):
            s += "b"
        elif stat.S_ISREG(mode):
            s += "-"
        elif stat.S_ISFIFO(mode):
            s += "p"
        elif stat.S_ISLNK(mode):
            s += "l"
        elif stat.S_ISSOCK(mode):
            s += "s"
        else:
            s += "?"

        if mode & stat.S_IRUSR:
            s += "r"
        else:
            s += "-"

        if mode & stat.S_IWUSR:
            s += "w"
        else:
            s += "-"

        if mode & stat.S_IXUSR:
            s += "s" if mode & stat.S_ISGID else "x"
        else:
            s += "S" if mode & stat.S_ISGID else "-"

        if mode & stat.S_IRGRP:
            s += "r"
        else:
            s += "-"
        if mode & stat.S_IWGRP:
            s += "w"
        else:
            s += "-"

        if mode & stat.S_IXGRP:
            s += "s" if mode & stat.S_ISGID else "x"
        else:
            s += "S" if mode & stat.S_ISGID else "-"

        if mode & stat.S_IROTH:
            s += "r"
        else:
            s += "-"

        if mode & stat.S_IWOTH:
            s += "w"
        else:
            s += "-"

        if mode & stat.S_IXOTH:  # stat.S_ISVTX:
            s += "t" if mode & stat.S_ISGID else "x"
        else:
            s += "T" if mode & stat.S_ISGID else "-"

        return s


class FileInfoFormatter:

    def __init__(self, fileinfo):
        self.fileinfo = fileinfo

    def __getitem__(self, key):
        # FIXME: potential security hole
        return self.__getattribute__(key)()

    def path(self): return self.fileinfo.path

    def dev(self): return self.fileinfo.dev
    def ino(self): return self.fileinfo.ino

    def mode(self): return Mode(self.fileinfo.mode)
    def nlink(self): return self.fileinfo.nlink

    def uid(self): return self.fileinfo.uid
    def gid(self): return self.fileinfo.gid

    def owner(self): return getpwuid(self.fileinfo.uid).pw_name  # FIXME: maybe cache this?
    def group(self): return getgrgid(self.fileinfo.gid).gr_name  # FIXME: maybe cache this?

    def rdev(self): return self.fileinfo.rdev

    def size(self): return Bytes(self.fileinfo.size)
    def blksize(self): return self.fileinfo.blksize
    def blocks(self): return self.fileinfo.blocks

    def atime(self): return Time(self.fileinfo.atime)
    def ctime(self): return Time(self.fileinfo.ctime)
    def mtime(self): return Time(self.fileinfo.mtime)

    def time(self): return Time(self.fileinfo.time)

    def birth(self): return self.fileinfo.birth
    def death(self): return self.fileinfo.death

    def sha1(self): return Checksum(self.fileinfo.blob.sha1 if self.fileinfo.blob else "<sha1:unknown>")
    def md5(self): return Checksum(self.fileinfo.blob.md5 if self.fileinfo.blob else "<md5:unknown>")

    def target(self): return self.fileinfo.target


# EOF #
