# -*- coding: utf-8 -*-
"""
TreeNode Roots Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from treenode.cache import cached_method


class TreeNodeRootsMixin(models.Model):
    """TreeNode Roots Mixin."""

    @classmethod
    def add_root(cls, position=None, **kwargs):
        """
        Add a root node to the tree.

        Adds a new root node at the specified position. If no position is
        specified, the new node will be the last element in the root.
        Parameters:
        position: can be 'first-root', 'last-root', 'sorted-root' or integer
        value.
        **kwargs – Object creation data that will be passed to the inherited
          Node model
        instance – Instead of passing object creation data, you can pass
          an already-constructed (but not yet saved) model instance to be
          inserted into the tree.

        Returns:
        The created node object. It will be save()d by this method.
        """
        if isinstance(position, int):
            priority = position
        else:
            if position not in ['first-root', 'last-root', 'sorted-root']:
                raise ValueError(f"Invalid position format: {position}")

            parent, priority = cls._get_place(None, position)

        instance = kwargs.get("instance")
        if instance is None:
            instance = cls(**kwargs)

        parent, priority = cls._get_place(None, position)
        instance.tn_parent = None
        instance.tn_priority = priority
        instance.save()
        return instance

    @classmethod
    @cached_method
    def get_roots_queryset(cls):
        """Get root nodes queryset with preloaded children."""
        qs = cls.objects.filter(tn_parent=None).prefetch_related('tn_children')
        return qs

    @classmethod
    @cached_method
    def get_roots_pks(cls):
        """Get a list with all root nodes."""
        pks = cls.objects.filter(tn_parent=None).values_list("id", flat=True)
        return list(pks)

    @classmethod
    def get_roots(cls):
        """Get a list with all root nodes."""
        qs = cls.get_roots_queryset()
        return list(qs)

    @classmethod
    def get_roots_count(cls):
        """Get a list with all root nodes."""
        return cls.get_roots_queryset().count()

    @classmethod
    def get_first_root(cls):
        """Return the first root node in the tree or None if it is empty."""
        roots = cls.get_roots_queryset()
        return roots.fiest() if roots.count() > 0 else None

    @classmethod
    def get_last_root(cls):
        """Return the last root node in the tree or None if it is empty."""
        roots = cls.get_roots_queryset()
        return roots.last() if roots.count() > 0 else None

# The End
