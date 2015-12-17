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


from scatterbackup.fileinfo import FileInfo
import scatterbackup.util
import os


def generate_fileinfos(directory,
                       startdirectory=None,
                       relative=False,
                       prefix=None,
                       checksums=False):

    directory_generator = os.walk(directory)

    scatterbackup.util.advance_walk_to(directory_generator, startdirectory)

    for root, dirs, files in directory_generator:
        if prefix is not None:
            relative = True

        yield FileInfo.from_file(directory)

        fileidx = 1
        for root, dirs, files in os.walk(directory):
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
