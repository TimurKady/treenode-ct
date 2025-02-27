# -*- coding: utf-8 -*-
"""
TreeNode Node Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from ...cache import cached_method, treenode_cache
from ...utils.base32 import to_base36


class TreeNodeNodeMixin(models.Model):
    """TreeNode Node Mixin."""

    @cached_method
    def get_breadcrumbs(self, attr='pk'):
        """Optimized breadcrumbs retrieval with direct cache check."""
        if attr not in self._meta.get_fields():
            raise ValueError(f"Invalid attribute name: {attr}")

        # Easy logics for roots
        if self.tn_parent is None:
            return [getattr(self, attr)]

        # Generate parents cache key
        cache_key = treenode_cache.generate_cache_key(
            self._meta.label,
            self.get_breadcrumbs.__name__,
            self.tn_parent.pk,
            attr
        )

        # Try get value from cache
        breadcrumbs = treenode_cache.get(cache_key)
        if breadcrumbs is not None:
            return breadcrumbs + [getattr(self, attr)]

        queryset = self.get_ancestors_queryset(include_self=True).only(attr)
        return [getattr(item, attr) for item in queryset]

    @cached_method
    def get_depth(self):
        """Get the node depth (self, how many levels of descendants)."""
        return self.closure_model.get_depth(self)

    @cached_method
    def get_index(self):
        """Get the node index (self, index in node.parent.children list)."""
        if self.tn_parent is None:
            return self.tn_priority
        source = list(self.tn_parent.tn_children.all())
        return source.index(self) if self in source else self.tn_priority

    @cached_method
    def get_level(self):
        """Get the node level (self, starting from 1)."""
        return self.closure_model.get_level(self)

    def get_order(self):
        """Return the materialized path."""
        path = self.get_breadcrumbs(attr='tn_priority')
        segments = [to_base36(i).rjust(6, '0') for i in path]
        return ''.join(segments)

    def insert_at(self, target, position='first-child', save=False):
        """
        Insert a node into the tree relative to the target node.

        Parameters:
        target: еhe target node relative to which this node will be placed.

        position – the position, relative to the target node, where the
        current node object will be moved to, can be one of:

        - first-root: the node will be the first root node;
        - last-root: the node will be the last root node;
        - sorted-root: the new node will be moved after sorting by
          the treenode_sort_field field;

        - first-sibling: the node will be the new leftmost sibling of the
          target node;
        - left-sibling: the node will take the target node’s place, which will
          be moved to the target position with shifting follows nodes;
        - right-sibling: the node will be moved to the position after the
          target node;
        - last-sibling: the node will be the new rightmost sibling of the
          target node;
        - sorted-sibling: the new node will be moved after sorting by
          the treenode_sort_field field;

        - first-child: the node will be the first child of the target node;
        - last-child: the node will be the new rightmost child of the target
        - sorted-child: the new node will be moved after sorting by
          the treenode_sort_field field.

        save : if `save=true`, the node will be saved in the tree. Otherwise,
        the method will return a model instance with updated fields: parent
        field and position in sibling list.

        Before using this method, the model instance must be correctly created
        with all required fields defined. If the model has required fields,
        then simply creating an object and calling insert_at() will not work,
        because Django will raise an exception.
        """
        # This method seems to have very dubious practical value.
        parent, priority = self._meta.model._get_place(target, position)
        self.tn_parent = parent
        self.tn_priority = priority

        if save:
            self.save()

    def move_to(self, target, position=0):
        """
        Move node relative to target node and position.

        Moves the model instance relative to the target node and sets its
        position (if necessary).

        position – the position, relative to the target node, where the
        current node object will be moved to, can be one of:

        - first-root: the node will be the first root node;
        - last-root: the node will be the last root node;
        - sorted-root: the new node will be moved after sorting by
          the treenode_sort_field field;
          Note: if `position` contains `root`, then `target` parametr is ignored

        - first-sibling: the node will be the new leftmost sibling of the
          target node;
        - left-sibling: the node will take the target node’s place, which will
          be moved to the target position with shifting follows nodes;
        - right-sibling: the node will be moved to the position after the
          target node;
        - last-sibling: the node will be the new rightmost sibling of the
          target node;
        - sorted-sibling: the new node will be moved after sorting by
          the treenode_sort_field field;

        - first-child: the node will be the first child of the target node;
        - last-child: the node will be the new rightmost child of the target
        - sorted-child: the new node will be moved after sorting by
          the treenode_sort_field field;
        """
        parent, priority = self._meta.model._get_place(target, position)
        self.tn_parent = parent
        self.tn_priority = priority
        self.save()

    def get_path(self, prefix='', suffix='', delimiter='.', format_str=''):
        """Return Materialized Path of node."""
        priorities = self.get_breadcrumbs(attr='tn_priority')
        if not priorities or all(p is None for p in priorities):
            return prefix + suffix

        str_ = "{%s}" % format_str
        path = delimiter.join([
            str_.format(p)
            for p in priorities
            if p is not None
        ])
        return prefix + path + suffix

    @cached_method
    def get_parent(self):
        """Get the parent node."""
        return self.tn_parent

    def set_parent(self, parent_obj):
        """Set the parent node."""
        self.tn_parent = parent_obj
        self.save()

    def get_parent_pk(self):
        """Get the parent node pk."""
        return self.get_parent().pk if self.tn_parent else None

    @cached_method
    def get_priority(self):
        """Get the node priority."""
        return self.tn_priority

    def set_priority(self, priority=0):
        """Set the node priority."""
        self.tn_priority = priority
        self.save()

    @cached_method
    def get_root(self):
        """Get the root node for the current node."""
        return self.closure_model.get_root(self)

    def get_root_pk(self):
        """Get the root node pk for the current node."""
        root = self.get_root()
        return root.pk if root else None

# The End
