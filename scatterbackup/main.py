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


def main():
    parser = argparse.ArgumentParser(description='rFactor to GSC2013 converter')
    parser.add_argument('DIRECTORY', action='store', type=str, nargs='+',
                        help='directory containing the mod')
    parser.add_argument('-o', '--output', metavar='DIR', type=str,
                        help="output directory")
    parser.add_argument('-i', '--info', action='store_true', default=False,
                        help="show info on the mod")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="be more verbose")
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                        help="be less verbose")
    args = parser.parse_args()


# EOF #
