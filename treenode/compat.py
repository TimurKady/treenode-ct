# -*- coding: utf-8 -*-
"""
File to handle compatibility issues
"""
import django

if django.VERSION >= (3, 0):
    from django.utils.encoding import force_str
else:
    from django.utils.encoding import force_text as force_str
