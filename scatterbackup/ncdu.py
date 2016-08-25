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
import json
import os
import sys
import time

import scatterbackup.diff


# st_dev is included when it changes
# root directory contains full path
# directory:
# [{"name":"/tmp/test","asize":58,"dev":22,"ino":2203839}, # directory
#  {"name":"1MB.dat","asize":100000,"dsize":102400,"ino":2203840}, # files
#  {"name":"pcmC0D2c","ino":679,"notreg":true}, # device file
#  ...
#  [{"name":"foo","asize":6,"ino":2203947}, # subdirectory
#   {"name":"bar","ino":2203948}],


def ncdu_directory(node):
    # leave the fullpath inside the node, it's cut out later
    return [{"name": node.path,
             "asize": 0,
             "dev": node.dev,
             "ino": node.ino}]


def ncdu_file(node):
    if node.kind == "file":
        return {"name": os.path.basename(node.path),
                "asize": node.size,
                "dsize": node.blocks * 512,
                "ino": node.ino}
    else:
        return {"name": os.path.basename(node.path),
                "ino": node.ino,
                "notreg": True}


def ncdu_from_tree_with_header(tree):
    return [1, 0,
            {"progname": "scatterbackup",
             "progver": "1.10",
             "timestamp": int(time.time())},
            ncdu_from_tree(tree)]


def ncdu_from_tree(tree):
    directories = {d.path: ncdu_directory(d) for k, d in tree.items() if d.kind == "directory"}

    root = None

    # attach directories to themselves
    for k, v in directories.items():
        parent = directories.get(os.path.dirname(k))
        if parent is None:
            if root is None:
                root = v
            else:
                raise Exception("multiple roots in .sbtr")
        else:
            # cut down the fullpath to a relative path, except for root
            v[0]["name"] = os.path.basename(v[0]["name"])
            parent.append(v)

    # attach all the files to the directories
    for k, node in tree.items():
        if node.kind != "directory":
            parent = directories.get(os.path.dirname(node.path))
            if parent is not None:
                parent.append(ncdu_file(node))

    if root is None:
        raise Exception("couldn't find root in .sbtr")

    return root


def main():
    parser = argparse.ArgumentParser(description='Convert .sbtr to ncdu syntax')
    parser.add_argument('FILE', action='store', type=str, nargs=1,
                        help='.sbtr file to load')
    args = parser.parse_args()

    fileinfos = scatterbackup.sbtr.fileinfos_from_sbtr(args.FILE[0])
    ncdu_js = ncdu_from_tree_with_header(fileinfos)
    json.dump(ncdu_js, fp=sys.stdout)


# EOF #
