# -*- coding: utf-8 -*-
"""
TreeNode Logical methods Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models


class TreeNodeLogicalMixin(models.Model):
    """TreeNode Logical Mixin."""

    def is_ancestor_of(self, target_obj):
        """Return True if the current node is ancestor of target_obj."""
        return self in target_obj.get_ancestors(include_self=False)

    def is_child_of(self, target_obj):
        """Return True if the current node is child of target_obj."""
        return self in target_obj.get_children()

    def is_descendant_of(self, target_obj):
        """Return True if the current node is descendant of target_obj."""
        return self in target_obj.get_descendants()

    def is_first_child(self):
        """Return True if the current node is the first child."""
        return self.tn_priority == 0

    def is_last_child(self):
        """Return True if the current node is the last child."""
        return self.tn_priority == self.get_siblings_count() - 1

    def is_leaf(self):
        """Return True if the current node is a leaf."""
        return self.tn_children.count() == 0

    def is_parent_of(self, target_obj):
        """Return True if the current node is parent of target_obj."""
        return self == target_obj.tn_parent

    def is_root(self):
        """Return True if the current node is root."""
        return self.tn_parent is None

    def is_root_of(self, target_obj):
        """Return True if the current node is root of target_obj."""
        return self == target_obj.get_root()

    def is_sibling_of(self, target_obj):
        """Return True if the current node is sibling of target_obj."""
        if target_obj.tn_parent is None and self.tn_parent is None:
            # Both objects are roots
            return True
        return (self.tn_parent == target_obj.tn_parent)

# The End
