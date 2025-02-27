# -*- coding: utf-8 -*-
"""
Class Property Decorator

This module provides a `classproperty` decorator that allows defining
read-only class-level properties.

Features:
- Enables class-level properties similar to instance properties.
- Uses a custom descriptor for property-like behavior.

"""


class classproperty(object):
    """Classproperty class."""

    def __init__(self, getter):
        """Init."""
        self.getter = getter

    def __get__(self, instance, owner):
        """Get."""
        return self.getter(owner)


# The end
