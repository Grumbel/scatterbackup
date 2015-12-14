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
import scatterbackup


def same_content(fileinfo1, fileinfo2):
    if fileinfo1.blob is None or fileinfo2.blob is None:
        return True
    else:
        return fileinfo1.blob == fileinfo2.blob


def fileinfos_from_file(filename):
    result = {}
    with open(filename, "r") as fin:
        for line in fin:
            fileinfo = scatterbackup.FileInfo.from_json(line)
            result[fileinfo.path] = fileinfo
    return result


def diff(tree1, tree2):
    paths = set()
    paths.update(tree1.keys())
    paths.update(tree2.keys())

    for k in sorted(paths):
        if k not in tree1:
            print("added", k)
        elif k not in tree2:
            print("deleted", k)
        else:
            if same_content(tree2[k], tree1[k]):
                pass
            else:
                print("modified", k)


def main():
    parser = argparse.ArgumentParser(description='Compare two .sbtr files')
    parser.add_argument('FILE1', action='store', type=str, nargs=1,
                        help='directory containing the mod')
    parser.add_argument('FILE2', action='store', type=str, nargs=1,
                        help='directory containing the mod')
    args = parser.parse_args()

    tree1 = fileinfos_from_file(args.FILE1[0])
    tree2 = fileinfos_from_file(args.FILE2[0])

    diff(tree1, tree2)


# EOF #
