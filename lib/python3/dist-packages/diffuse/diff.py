#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2006-2018 Derrick Moser <derrick_moser@yahoo.com>
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

# longest common subsequence of unique elements common to 'a' and 'b'
def _patience_subsequence(a, b):
    # value unique lines by their order in each list
    value_a, value_b = {}, {}
    # find unique values in 'a'
    for i, s in enumerate(a):
        if s in value_a:
            value_a[s] = -1
        else:
            value_a[s] = i
    # find unique values in 'b'
    for i, s in enumerate(b):
        if s in value_b:
            value_b[s] = -1
        else:
            value_b[s] = i
    # lay down items in 'b' as if playing patience if the item is unique in
    # 'a' and 'b'
    pile, pointers, atob = [], {}, {}
    get, append = value_a.get, pile.append
    for s in b:
        v = get(s, -1)
        if v != -1:
            vb = value_b[s]
            if vb != -1:
                atob[v] = vb
                # find appropriate pile for v
                start, end = 0, len(pile)
                # optimisation as values usually increase
                if end and v > pile[-1]:
                    start = end
                else:
                    while start < end:
                        mid = (start + end) // 2
                        if v < pile[mid]:
                            end = mid
                        else:
                            start = mid + 1
                if start < len(pile):
                    pile[start] = v
                else:
                    append(v)
                if start:
                    pointers[v] = pile[start-1]
    # examine our piles to determine the longest common subsequence
    result = []
    if pile:
        v, append = pile[-1], result.append
        append((v, atob[v]))
        while v in pointers:
            v = pointers[v]
            append((v, atob[v]))
        result.reverse()
    return result

# difflib-style approximation of the longest common subsequence
def _lcs_approx(a, b):
    count1, lookup = {}, {}
    # count occurances of each element in 'a'
    for s in a:
        count1[s] = count1.get(s, 0) + 1
    # construct a mapping from a element to where it can be found in 'b'
    for i, s in enumerate(b):
        if s in lookup:
            lookup[s].append(i)
        else:
            lookup[s] = [ i ]
    if set(lookup).intersection(count1):
        # we have some common elements
        # identify popular entries
        popular = {}
        n = len(a)
        if n > 200:
            for k, v in count1.items():
                if 100 * v > n:
                    popular[k] = 1
        n = len(b)
        if n > 200:
            for k, v in lookup.items():
                if 100 * len(v) > n:
                    popular[k] = 1
        # while walk through entries in 'a', incrementally update the list of
        # matching subsequences in 'b' and keep track of the longest match
        # found
        prev_matches, matches, max_length, max_indices = {}, {}, 0, []
        for ai, s in enumerate(a):
            if s in lookup:
                if s in popular:
                    # we only extend existing previously found matches to avoid
                    # performance issues
                    for bi in prev_matches:
                        if bi + 1 < n and b[bi + 1] == s:
                            matches[bi] = v = prev_matches[bi] + 1
                            # check if this is now the longest match
                            if v >= max_length:
                                if v == max_length:
                                    max_indices.append((ai, bi))
                                else:
                                    max_length = v
                                    max_indices = [ (ai, bi) ]
                else:
                    prev_get = prev_matches.get
                    for bi in lookup[s]:
                        matches[bi] = v = prev_get(bi - 1, 0) + 1
                        # check if this is now the longest match
                        if v >= max_length:
                            if v == max_length:
                                max_indices.append((ai, bi))
                            else:
                                max_length = v
                                max_indices = [ (ai, bi) ]
            prev_matches, matches = matches, {}
        if max_indices:
            # include any popular entries at the beginning
            aidx, bidx, nidx = 0, 0, 0
            for ai, bi in max_indices:
                n = max_length
                ai += 1 - n
                bi += 1 - n
                while ai and bi and a[ai - 1] == b[bi - 1]:
                    ai -= 1
                    bi -= 1
                    n += 1
                if n > nidx:
                    aidx, bidx, nidx = ai, bi, n
            return aidx, bidx, nidx

# patinence diff with difflib-style fallback
def patience_diff(a, b):
    matches, len_a, len_b = [], len(a), len(b)
    if len_a and len_b:
        blocks = [ (0, len_a, 0, len_b, 0) ]
        while blocks:
            start_a, end_a, start_b, end_b, match_idx = blocks.pop()
            aa, bb = a[start_a:end_a], b[start_b:end_b]
            # try patience
            pivots = _patience_subsequence(aa, bb)
            if pivots:
                offset_a, offset_b = start_a, start_b
                for pivot_a, pivot_b in pivots:
                    pivot_a += offset_a
                    pivot_b += offset_b
                    if start_a <= pivot_a:
                        # extend before
                        idx_a, idx_b = pivot_a, pivot_b
                        while start_a < idx_a and start_b < idx_b and a[idx_a - 1] == b[idx_b - 1]:
                            idx_a -= 1
                            idx_b -= 1
                        # if anything is before recurse on the section
                        if start_a < idx_a and start_b < idx_b:
                            blocks.append((start_a, idx_a, start_b, idx_b, match_idx))
                        # extend after
                        start_a, start_b = pivot_a + 1, pivot_b + 1
                        while start_a < end_a and start_b < end_b and a[start_a] == b[start_b]:
                            start_a += 1
                            start_b += 1
                        # record match
                        matches.insert(match_idx, (idx_a, idx_b, start_a - idx_a))
                        match_idx += 1
                # if anything is after recurse on the section
                if start_a < end_a and start_b < end_b:
                    blocks.append((start_a, end_a, start_b, end_b, match_idx))
            else:
                # fallback if patience fails
                pivots = _lcs_approx(aa, bb)
                if pivots:
                    idx_a, idx_b, n = pivots
                    idx_a += start_a
                    idx_b += start_b
                    # if anything is before recurse on the section
                    if start_a < idx_a and start_b < idx_b:
                        blocks.append((start_a, idx_a, start_b, idx_b, match_idx))
                    # record match
                    matches.insert(match_idx, (idx_a, idx_b, n))
                    match_idx += 1
                    idx_a += n
                    idx_b += n
                    # if anything is after recurse on the section
                    if idx_a < end_a and idx_b < end_b:
                        blocks.append((idx_a, end_a, idx_b, end_b, match_idx))
    # try matching from begining to first match block
    if matches:
        end_a, end_b = matches[0][:2]
    else:
        end_a, end_b = len_a, len_b
    i = 0
    while i < end_a and i < end_b and a[i] == b[i]:
        i += 1
    if i:
        matches.insert(0, (0, 0, i))
    # try matching from last match block to end
    if matches:
        start_a, start_b, n = matches[-1]
        start_a += n
        start_b += n
    else:
        start_a, start_b = 0, 0
    end_a, end_b = len_a, len_b
    while start_a < end_a and start_b < end_b and a[end_a - 1] == b[end_b - 1]:
        end_a -= 1
        end_b -= 1
    if end_a < len_a:
        matches.append((end_a, end_b, len_a - end_a))
    # add a zero length block to the end
    matches.append((len_a, len_b, 0))
    return matches
