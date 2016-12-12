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


from scatterbackup.units import bytes2human, units


class Bytes:

    def __init__(self, count):
        self.count = count

    def __format__(self, spec):
        r = spec.rsplit(":", maxsplit=1)
        str_spec, unit = r if len(r) == 2 else (r[0], "h")
        return format(self.as_str(unit), str_spec)

    def as_str(self, unit):
        if unit == "h":  # FIXME: allow 'H' for non-si units
            return bytes2human(self.count)
        elif unit == "r":
            return "{}".format(self.count)
        elif unit == "B":
            return "{}{}".format(self.count, unit)
        elif unit in units:
            return "{:.2f}{}".format(self.count / units[unit], unit)
        else:
            raise Exception("unknown unit: {}".format(unit))


class FileInfoFormater:

    def __init__(self, fileinfo):
        self.fileinfo = fileinfo

    def __getitem__(self, key):
        return self.__getattribute__(key)()

    def size(self):
        return Bytes(59202398)


# EOF #
