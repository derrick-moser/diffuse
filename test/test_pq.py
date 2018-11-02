#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', os.path.join('lib', 'python3', 'dist-packages'))))

import diffuse.pq

pq = diffuse.pq.PriorityQueue()
pq.insert(5, 'five')
pq.insert(7, 'seven')
pq.insert(6, 'six')
pq.insert(3, 'three')
pq.insert(4, 'four')
pq.insert(8, 'eight')
pq.insert(1, 'one')
pq.insert(2, 'two')
pq.insert(9, 'nine')
while not pq.empty():
    print(pq)
    print(pq.pop())
