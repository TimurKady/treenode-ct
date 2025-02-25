# -*- coding: utf-8 -*-
"""
Base16 Utility Module

This module provides a utility function for converting integers
to Base16 string representation.

Features:
- Converts integers into a more compact Base36 format.
- Maintains lexicographic order when padded with leading zeros.
- Supports negative numbers.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


def to_base16(num):
    """
    Convert an integer to a base16 string.

    For example: 10 -> 'A', 11 -> 'B', etc.
    """
    digits = "0123456789ABCDEF"

    if num == 0:
        return '0'
    sign = '-' if num < 0 else ''
    num = abs(num)
    result = []
    while num:
        num, rem = divmod(num, 16)
        result.append(digits[rem])
    return sign + ''.join(reversed(result))
