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


import sys
import argparse
from scatterbackup.generator import generate_fileinfos
from scatterbackup.units import size2bytes


class DupfinderState:

    def __init__(self, filename, fd):
        self.filename = filename
        self.fd = fd
        self.block = None


def find_duplicates_fd(files):
    if len(files) == 1:
        return [files]

    for f in files:
        f.block = f.fd.read(1024 * 1024)

    groups = []
    for f in files:
        found = False
        for g in groups:
            if g[0].block == f.block:
                g.append(f)
                found = True
                break
        if not found:
            groups.append([f])

    ngroups = []
    for g in groups:
        if g[0].block == b'':
            ngroups.append(g)
        else:
            # FIXME: This recursion goes over the stack limit on big files
            ngroups += find_duplicates_fd(g)

    return ngroups


def find_duplicates(filenames):
    fds = []
    try:
        for filename in filenames:
            fds.append(DupfinderState(filename,
                                      open(filename, "rb")))
        groups = find_duplicates_fd(fds)
        return [[p.filename for p in g] for g in groups]

    finally:
        for fd in fds:
            fd.fd.close()


def parse_args():
    parser = argparse.ArgumentParser(description='Find duplicate files')
    parser.add_argument('FILES', action='store', type=str, nargs='+',
                        help='files or directories to search')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="be more verbose")
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                        help="be less verbose")
    parser.add_argument('-s', '--size-only', action='store_true', default=False,
                        help="Only compare file size, don't compare actual content")
    parser.add_argument('-l', '--limit', type=size2bytes, default=0, metavar="SIZE",
                        help="Only compare files larger then SIZE")
    return parser.parse_args()


def main():
    # FIXME: this is a hack, see find_duplicates_fd() above
    sys.setrecursionlimit(10000)

    args = parse_args()

    fileinfos = []
    for path in args.FILES:
        for fileinfo in generate_fileinfos(path, relative=False, prefix=None, checksums=False):
            if fileinfo.kind == "file":
                fileinfos.append(fileinfo)
            else:
                pass  # ignore non-files

    fileinfos_by_size = {}
    for fileinfo in fileinfos:
        if fileinfo.size not in fileinfos_by_size:
            fileinfos_by_size[fileinfo.size] = []
        fileinfos_by_size[fileinfo.size].append(fileinfo)

    for size, fileinfos in fileinfos_by_size.items():
        if len(fileinfos) > 1 and size >= args.limit:
            if args.verbose:
                print("potential duplicates: {} bytes".format(size))
                for fileinfo in fileinfos:
                    print("  {}".format(fileinfo.path))
                print()

            groups = find_duplicates([p.path for p in fileinfos])
            for g in groups:
                if len(g) > 1:
                    print("duplicates:")
                    for f in g:
                        print("  {}".format(f))
                    print()


# EOF #
