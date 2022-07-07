#   libdict.py
#   Copyright (C) 2022  Philippe Warren
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import TypeVar, Iterable
from functools import reduce, partial

T = TypeVar("T")


def merge_dicts_of_lists(
    dicts_of_lists: Iterable[dict[str, list[T]]],
) -> dict[str, list[T]]:
    def keys_union(s: set[str], d: dict[str, list[T]]) -> set[str]:
        return s | d.keys()

    empty_set: set[str] = set()
    keys = reduce(keys_union, dicts_of_lists, empty_set)
    empty_list: list[T] = []

    def merge_lists_for_key(l: list[T], d: dict[str, list[T]], k: str) -> list[T]:
        return l + d.get(k, empty_list)

    return {
        k: reduce(partial(merge_lists_for_key, k=k), dicts_of_lists, empty_list)
        for k in keys
    }
