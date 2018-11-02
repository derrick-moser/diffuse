#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', os.path.join('lib', 'python3', 'dist-packages'))))

import diffuse.acache

class Foo:
    def __init__(self):
        self._data = [2, 3, 4, 5, 6, 7]
        self._cache = diffuse.acache.AccumulationCache(self._get)

    def _get(self, i):
        return self._data[i]

    def set(self, i, v):
        self._data[i] = v
        self._cache.invalidate(i, i+1)

foo = Foo()
print(foo._cache.get_partial_sum(5))
foo.set(3, 10)
print(foo._cache.get_partial_sum(5))
foo.set(3, 4)
foo._cache.truncate(4)
print(foo._cache.get_partial_sum(5))
