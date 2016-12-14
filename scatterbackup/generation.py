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


import re


class Generation:

    def __init__(self, generation, start_time, end_time, command):
        self.generation = generation
        self.start_time = start_time
        self.end_time = end_time
        self.command = command


class GenerationRange:

    @staticmethod
    def from_string(text):
        start = None
        end = None

        if text:
            text = text.strip()
            m = re.match(r"^([0-9]+):([0-9]+)$", text)
            if m:
                start, end = m.groups()
            else:
                m = re.match(r"^([0-9]+):$", text)
                if m:
                    start, = m.groups()
                else:
                    m = re.match(r"^:([0-9]+)$", text)
                    if m:
                        end, = m.groups()
                        start = None
                    else:
                        m = re.match(r"^([0-9]+)$", text)
                        if m:
                            start, = m.groups()
                            end = str(int(start) + 1)
                        elif text == ":":
                            start = None
                            end = None
                        else:
                            raise Exception("invalid generation string: {}".format(text))

            start = int(start) if start else None
            end = int(end) if end else None

            if start is not None and end is not None and start >= end:
                raise Exception("invalid generation range: {}-{}".format(start, end))

        return GenerationRange(start, end)

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, rhs):
        return (self.start == rhs.start and
                self.end == rhs.end)

    def __str__(self):
        return "{}:{}".format(self.start, self.end)

    def __repr__(self):
        return "GenerationRange({}:{})".format(self.start, self.end)

GenerationRange.MATCH_ALL = GenerationRange(None, None)


# EOF #
