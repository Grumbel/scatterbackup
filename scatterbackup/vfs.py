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


import fnmatch
import logging
import re
from collections import defaultdict

import scatterbackup.sbtr


class VFS:

    @staticmethod
    def from_sbtr(filename):
        vfs = VFS()
        fileinfos = scatterbackup.sbtr.fileinfos_from_sbtr(filename)
        for path, fileinfo in fileinfos.items():
            vfs.add(fileinfo)
        return vfs

    def __init__(self):
        self.fileinfos = []
        self.path_to_fileinfo = {}
        self.md5_to_fileinfo = defaultdict(list)
        self.sha1_to_fileinfo = defaultdict(list)

    def add(self, fileinfo):
        if fileinfo.path in self.path_to_fileinfo:
            logging.warning("%s: file already in vfs", fileinfo.path)

        self.fileinfos.append(fileinfo)

        self.path_to_fileinfo[fileinfo.path] = fileinfo

        if fileinfo.blob is not None and fileinfo.blob.md5 is not None:
            self.md5_to_fileinfo[fileinfo.blob.md5].append(fileinfo)

        if fileinfo.blob is not None and fileinfo.blob.sha1 is not None:
            self.sha1_to_fileinfo[fileinfo.blob.sha1].append(fileinfo)

    def get_fileinfo_by_md5(self, md5):
        if md5 in self.md5_to_fileinfo:
            return self.md5_to_fileinfo[md5]
        else:
            return []

    def get_fileinfo_by_sha1(self, sha1):
        if sha1 in self.sha1_to_fileinfo:
            return self.sha1_to_fileinfo[sha1]
        else:
            return []

    def get_fileinfo_by_path(self, path):
        if path in self.path_to_fileinfo:
            return self.path_to_fileinfo[path]
        else:
            return None

    def get_fileinfos_by_glob(self, pattern):
        return [fileinfo for fileinfo in self.fileinfos
                if fnmatch.fnmatch(fileinfo.path, pattern)]

    def get_fileinfos_by_regex(self, pattern):
        rx = re.compile(pattern)
        return [fileinfo for fileinfo in self.fileinfos
                if rx.match(fileinfo.path, pattern)]


# EOF #
