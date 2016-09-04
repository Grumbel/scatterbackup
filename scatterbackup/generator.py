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
import sys

from scatterbackup.fileinfo import FileInfo


def generate_files(path,
                   onerror=None):
    """Generate a list of files and directories below path"""

    yield path

    if os.path.isdir(path):
        for root, dirs, files in os.walk(path, onerror=onerror):
            for f in files + dirs:
                try:
                    yield os.path.normpath(os.path.join(root, f))
                except:
                    if onerror is not None:
                        onerror(sys.exc_info()[1])


def generate_fileinfos(path,
                       relative=False,
                       prefix=None,
                       onerror=None,
                       checksums=False):
    for p in generate_files(path=path, onerror=onerror):
        try:
            fileinfo = FileInfo.from_file(p,
                                          checksums=checksums,
                                          relative=relative)
            if prefix is not None:
                fileinfo.path = os.path.join(prefix, fileinfo.path)

            yield fileinfo

        except:
            if onerror is not None:
                onerror(sys.exc_info()[1])


# EOF #
