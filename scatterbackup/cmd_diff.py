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


import argparse
import os

import scatterbackup.sbtr
from scatterbackup.fileinfo import FileInfo
from scatterbackup.blobinfo import BlobInfo


def same_file(fileinfo1: FileInfo, fileinfo2: FileInfo) -> bool:
    if fileinfo1.kind != fileinfo2.kind:
        return False
    elif fileinfo1.blob is not None and fileinfo2.blob is not None:
        return same_content(fileinfo1, fileinfo2)
    else:
        return (fileinfo1.mtime == fileinfo2.mtime and
                fileinfo1.size == fileinfo2.size)


def same_content(fileinfo1: FileInfo, fileinfo2: FileInfo) -> bool:
    if fileinfo1.blob is None or fileinfo2.blob is None:
        return True  # this is wobbly
    else:
        return fileinfo1.blob == fileinfo2.blob


def filter_tree(tree: dict[str, FileInfo], prefix: str) -> dict[str, FileInfo]:
    result: dict[str, FileInfo] = {}
    for k, v in tree.items():
        if k.startswith(prefix):
            result[k] = v
    return result


def diff(tree1: dict[str, FileInfo], tree2: dict[str, FileInfo]) -> None:
    paths: set[str] = set()
    paths.update(tree1.keys())
    paths.update(tree2.keys())

    for k in sorted(paths):
        if k not in tree1:
            if tree2[k].blob is not None:
                blob_info: BlobInfo = tree2[k].blob  # type: ignore
                print(blob_info.md5, "added", k)
        elif k not in tree2:
            print("deleted", k)
        else:
            if same_file(tree2[k], tree1[k]):
                pass
            else:
                if tree1[k].size != tree2[k].size:
                    print(tree1[k].size - tree2[k].size,  # type: ignore
                          "modified", k, "size:",
                          tree1[k].size, tree2[k].size)


def main() -> None:
    parser = argparse.ArgumentParser(description='Compare two .sbtr files')
    parser.add_argument('FILE1', action='store', type=str, nargs=1,
                        help='.sbtr file or directory')
    parser.add_argument('FILE2', action='store', type=str, nargs=1,
                        help='.sbtr file or directory')

    # This is a bit of a mess, .sbtr files contain a path, so there
    # needs to be an option to select a sub-path from them.
    # Directories on the other side are already relative to their
    # origin, so this isn't needed

    # Allow four arguments: foo.sbtr / bar.sbtr /backup/
    parser.add_argument('-p', '--prefix', type=str, default=None, metavar="PREFIX",
                        help="Limit comparism to files under PREFIX")

    # FIXME: the top level directory is still part of the path with
    # this option, not a good thing
    parser.add_argument('-R', '--relative', action='store_true', default=False,
                        help="Compare relative path instead of absolute")

    parser.add_argument('-c', '--checksums', action='store_true', default=False,
                        help="Generate checksums for an exact comparism")

    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="Be more verbose")

    args = parser.parse_args()

    tree1 = scatterbackup.sbtr.fileinfos_from_path(args.FILE1[0], relative=args.relative, checksums=args.checksums)
    tree2 = scatterbackup.sbtr.fileinfos_from_path(args.FILE2[0], relative=args.relative, checksums=args.checksums)

    if args.prefix is not None:
        prefix = os.path.normpath(args.prefix)
        tree1 = filter_tree(tree1, prefix)
        tree2 = filter_tree(tree2, prefix)

    print(tree1)
    diff(tree1, tree2)


# EOF #
