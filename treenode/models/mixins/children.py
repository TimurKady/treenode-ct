# -*- coding: utf-8 -*-
"""
TreeNode Children Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from treenode.cache import cached_method


class TreeNodeChildrenMixin(models.Model):
    """TreeNode Ancestors Mixin."""

    def add_child(self, position=None, **kwargs):
        """
        Add a child to the node.

        position:
        Can be 'first-child', 'last-child', 'sorted-child' or integer value.

        Parameters:
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
            parent = self
        else:
            if position not in ['first-child', 'last-child', 'sorted-child']:
                raise ValueError(f"Invalid position format: {position}")
            parent, priority = self._meta.model._get_place(self, position)

        instance = kwargs.get("instance")
        if instance is None:
            instance = self._meta.model(**kwargs)
        instance.tn_parent = parent
        instance.tn_priority = priority
        instance.save()
        return instance

    @cached_method
    def get_children_pks(self):
        """Get the children pks list."""
        return list(self.get_children_queryset().values_list("id", flat=True))

    @cached_method
    def get_children_queryset(self):
        """Get the children queryset with prefetch."""
        return self.tn_children.prefetch_related('tn_children')

    def get_children(self):
        """Get a list containing all children."""
        return list(self.get_children_queryset())

    def get_children_count(self):
        """Get the children count."""
        return len(self.get_children_pks())

    def get_first_child(self):
        """Get the first child node or None if it has no children."""
        return self.get_children_queryset().first() if self.is_leaf else None

    def get_last_child(self):
        """Get the last child node or None if it has no children."""
        return self.get_children_queryset().last() if self.is_leaf else None
