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


import os

from scatterbackup.fileinfo import FileInfo
import scatterbackup.util


def generate_fileinfos(path,
                       startdirectory=None,
                       relative=False,
                       prefix=None,
                       checksums=False):
    if os.path.isdir(path):
        yield from generate_fileinfos_from_directory(path, startdirectory, relative, prefix, checksums)
    else:
        yield FileInfo.from_file(path,
                                 checksums=checksums,
                                 relative=relative)


def generate_fileinfos_from_directory(directory,
                                      startdirectory=None,
                                      relative=False,
                                      prefix=None,
                                      checksums=False):

    directory_generator = os.walk(directory)
    scatterbackup.util.advance_walk_to(directory_generator, startdirectory)

    if prefix is not None:
        relative = True

    yield FileInfo.from_file(directory)

    fileidx = 1
    for root, dirs, files in directory_generator:
        for f in files + dirs:
            p = os.path.normpath(os.path.join(root, f))
            fileinfo = scatterbackup.FileInfo.from_file(p,
                                                        checksums=checksums,
                                                        relative=relative)

            if prefix is not None:
                fileinfo.path = os.path.join(prefix, fileinfo.path)

            yield fileinfo

            fileidx += 1


# EOF #
