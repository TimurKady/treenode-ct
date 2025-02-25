# -*- coding: utf-8 -*-
"""
Implementation of the Radix Sort algorithm.

Radix Sort is a non-comparative sorting algorithm. It avoids comparisons by
creating and distributing elements into buckets according to their radix.

It is used as a replacement for numpy when sorting materialized paths and
tree node indices.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from collections import defaultdict


def counting_sort(pairs, index):
    """Sort pairs (key, string) by character at position index."""
    count = defaultdict(list)

    # Distribution of pairs into baskets
    for key, s in pairs:
        key_char = s[index] if index < len(s) else ''
        count[key_char].append((key, s))

    # Collect sorted pairs
    sorted_pairs = []
    for key_char in sorted(count.keys()):
        sorted_pairs.extend(count[key_char])

    return sorted_pairs


def radix_sort_pairs(pairs, max_length):
    """Radical sorting of pairs (key, string) by string."""
    for i in range(max_length - 1, -1, -1):
        pairs = counting_sort(pairs, i)
    return pairs


def quick_sort(pairs):
    """
    Sort tree objects by materialized path.

    pairs = [{obj.id: obj.path} for obj in objs]
    Returns a list of id (pk) objects sorted by their materialized path.
    """
    # Get the maximum length of the string
    max_length = max(len(s) for _, s in pairs)

    # Sort pairs by rows
    sorted_pairs = radix_sort_pairs(pairs, max_length)

    # Access keys in sorted order
    sorted_keys = [key for key, _ in sorted_pairs]
    return sorted_keys
