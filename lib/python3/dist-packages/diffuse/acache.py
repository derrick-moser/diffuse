#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Derrick Moser <derrick_moser@yahoo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import diffuse.pq

class AccumulationCache:
    def __init__(self, f):
        self._partial_sums = []
        self._dirty = diffuse.pq.PriorityQueue()
        self._func = f

    def get_partial_sum(self, i):
        p = self._partial_sums
        d = self._dirty
        while 1:
            n = len(p)
            if d.empty():
                if i < n:
                    return p[i]
                v = self._func(n)
                if n:
                    v += p[n - 1]
                p.append(v)
            else:
                m = -d.max_priority()
                if m < n:
                    if i < m:
                        return p[i]
                    d.pop()
                    v = self._func(m)
                    if m:
                        v += p[m - 1]
                    if p[m] != v:
                        p[m] = v
                        self.truncate(m + 1)
                else:
                    d.clear()

    def invalidate(self, start, end=-1):
        if end < 0:
            end = start + 1
        n = len(self._partial_sums)
        if start < n:
            if end > n:
                end = n
            for i in range(start, end):
                self._dirty.insert(-i, i)

    def truncate(self, i):
        if i < len(self._partial_sums):
            del self._partial_sums[i:]
        if not self._dirty.empty() and i <= -self._dirty.max_priority():
            self._dirty.clear()

    def clear(self):
        self.truncate(0)

    def lookup(self, row):
        p = self._partial_sums
        pa = p.append
        d = self._dirty
        de = d.empty
        f = self._func
        n = len(p)
        while 1:
            if de():
                v = p[n - 1] if n else 0
                if row <= v:
                    break
                v += f(n)
                pa(v)
            else:
                m = -d.max_priority()
                if m < n:
                    v = p[m - 1] if m else 0
                    if row <= v:
                        n = m
                        break
                    d.pop()
                    v += f(m)
                    if p[m] != v:
                        p[m] = v
                        self.truncate(m + 1)
                else:
                    d.clear()
        low = 0
        while low < n:
            mid = (low + n) // 2
            v = p[mid]
            if row < v:
                n = mid
            else:
                low = mid + 1
        return low
