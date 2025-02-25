# -*- coding: utf-8 -*-
"""
TreeNode Signals Module

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from contextlib import contextmanager


@contextmanager
def disable_signals(signal, sender):
    """Temporarily disable execution of signal generation."""
    # Save current signal handlers
    old_receivers = signal.receivers[:]
    signal.receivers = []
    try:
        yield
    finally:
        # Restore handlers
        signal.receivers = old_receivers
