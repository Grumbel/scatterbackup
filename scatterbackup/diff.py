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


def same_file(fileinfo1, fileinfo2):
    if fileinfo1.kind != fileinfo2.kind:
        return False
    elif fileinfo1.blob is not None and fileinfo2.blob is not None:
        return same_content(fileinfo1, fileinfo2)
    else:
        return (fileinfo1.mtime == fileinfo2.mtime and
                fileinfo1.size == fileinfo2.size)


def same_content(fileinfo1, fileinfo2):
    if fileinfo1.blob is None or fileinfo2.blob is None:
        return True  # this is wobbly
    else:
        return fileinfo1.blob == fileinfo2.blob


def filter_tree(tree, prefix):
    result = {}
    for k, v in tree.items():
        if k.startswith(prefix):
            result[k] = v
    return result


def diff(tree1, tree2):
    paths = set()
    paths.update(tree1.keys())
    paths.update(tree2.keys())

    for k in sorted(paths):
        if k not in tree1:
            if tree2[k].blob is not None:
                print(tree2[k].blob.md5, "added", k)
        elif k not in tree2:
            print("deleted", k)
        else:
            if same_file(tree2[k], tree1[k]):
                pass
            else:
                if tree1[k].size != tree2[k].size:
                    print(tree1[k].size - tree2[k].size, "modified", k, "size:", tree1[k].size, tree2[k].size)


def main():
    parser = argparse.ArgumentParser(description='Compare two .sbtr files')
    parser.add_argument('FILE1', action='store', type=str, nargs=1,
                        help='.sbtr file or directory')
    parser.add_argument('FILE2', action='store', type=str, nargs=1,
                        help='.sbtr file or directory')
    parser.add_argument('-p', '--prefix', type=str, default=None, metavar="PREFIX",
                        help="Limit comparism to files under PREFIX")
    args = parser.parse_args()

    tree1 = scatterbackup.sbtr.fileinfos_from_path(args.FILE1[0])
    tree2 = scatterbackup.sbtr.fileinfos_from_path(args.FILE2[0])

    if args.prefix is not None:
        prefix = os.path.normpath(args.prefix)
        tree1 = filter_tree(tree1, prefix)
        tree2 = filter_tree(tree2, prefix)

    diff(tree1, tree2)


# EOF #
