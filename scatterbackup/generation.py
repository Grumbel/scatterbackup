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


from typing import Optional

import re


class Generation:

    def __init__(self, generation: int, start_time: int, end_time: int, command: str) -> None:
        self.generation = generation
        self.start_time = start_time
        self.end_time = end_time
        self.command = command


class GenerationRange:

    INCLUDE_ALIVE = 1
    INCLUDE_CHANGED = 2

    MATCH_ALL: 'GenerationRange'

    @staticmethod
    def from_string(text: str, dbrange: Optional['GenerationRange'] = None) -> 'GenerationRange':
        start_text: Optional[str] = None
        end_text: Optional[str] = None

        start: Optional[int] = None
        end: Optional[int] = None

        if text:
            text = text.strip()
            text = text.replace("^", "-")
            m = re.match(r"^(-?[0-9]+):(-?[0-9]+)$", text)
            if m:
                start_text, end_text = m.groups()
            else:
                m = re.match(r"^(-?[0-9]+):$", text)
                if m:
                    start_text, = m.groups()
                else:
                    m = re.match(r"^:(-?[0-9]+)$", text)
                    if m:
                        end_text, = m.groups()
                        start_text = None
                    else:
                        m = re.match(r"^(-?[0-9]+)$", text)
                        if m:
                            start_text, = m.groups()
                            end_text = str(int(start_text) + 1)  # type: ignore
                        elif text == ":":
                            start_text = None
                            end_text = None
                        else:
                            raise Exception("invalid generation string: {}".format(text))

            start = int(start_text) if start_text else None
            end = int(end_text) if end_text else None

            if start is not None and \
               end is not None and \
               start >= end:
                raise Exception("invalid generation range: {}-{}".format(start, end))

        if dbrange is None:
            return GenerationRange(start, end)
        else:
            # handle negative generations
            if start is not None and start < 0:
                assert dbrange.end is not None
                start = dbrange.end + start

            if end is not None and end < 0:
                assert dbrange.end is not None
                end = dbrange.end + end

            gen = GenerationRange(start, end)
            gen.clip_to(dbrange)
            return gen

    def __init__(self, start: Optional[int], end: Optional[int], include_rule: int = INCLUDE_ALIVE) -> None:
        self.start = start
        self.end = end
        self.include_rule = include_rule

    def clip_to(self, grange: 'GenerationRange') -> None:
        if self.start is None:
            self.start = grange.start
        else:
            assert grange.start is not None
            self.start = max(self.start, grange.start)

        if self.end is None:
            self.end = grange.end
        else:
            assert grange.end is not None
            self.end = min(self.end, grange.end)

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, GenerationRange):
            return False

        return (self.start == rhs.start and
                self.end == rhs.end)

    def __str__(self) -> str:
        return "{}:{}".format(self.start, self.end)

    def __repr__(self) -> str:
        return "GenerationRange({}:{})".format(self.start, self.end)


GenerationRange.MATCH_ALL = GenerationRange(None, None)


# EOF #
