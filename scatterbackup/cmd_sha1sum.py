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
import scatterbackup.diff


def main():
    parser = argparse.ArgumentParser(description='Convert .sbtr to sha1sum syntax')
    parser.add_argument('FILE', action='store', type=str, nargs=1,
                        help='.sbtr file to load')
    args = parser.parse_args()

    fileinfos = scatterbackup.sbtr.fileinfos_from_sbtr(args.FILE[0])
    for fileinfo in sorted(fileinfos.values(), key=lambda x: x.path):
        if fileinfo.blob is not None:
            print("{}  {}".format(fileinfo.blob.sha1, fileinfo.path))


# EOF #
