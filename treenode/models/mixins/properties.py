# -*- coding: utf-8 -*-
"""
TreeNode Properties Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from ..classproperty import classproperty


class TreeNodePropertiesMixin:
    """
    TreeNode Properties Mixin.

    Public properties.
    All properties map a get_{{property}}() method.
    """

    @property
    def ancestors(self):
        """Get a list with all ancestors; self included."""
        return self.get_ancestors()

    @property
    def ancestors_count(self):
        """Get the ancestors count."""
        return self.get_ancestors_count()

    @property
    def ancestors_pks(self):
        """Get the ancestors pks list; self included."""
        return self.get_ancestors_pks()

    @property
    def breadcrumbs(self):
        """Get the breadcrumbs to current node(self, included)."""
        return self.get_breadcrumbs()

    @property
    def children(self):
        """Get a list containing all children; self included."""
        return self.get_children()

    @property
    def children_count(self):
        """Get the children count."""
        return self.get_children_count()

    @property
    def children_pks(self):
        """Get the children pks list."""
        return self.get_children_pks()

    @property
    def depth(self):
        """Get the node depth."""
        return self.get_depth()

    @property
    def descendants(self):
        """Get a list containing all descendants; self not included."""
        return self.get_descendants()

    @property
    def descendants_count(self):
        """Get the descendants count; self not included."""
        return self.get_descendants_count()

    @property
    def descendants_pks(self):
        """Get the descendants pks list; self not included."""
        return self.get_descendants_pks()

    @property
    def first_child(self):
        """Get the first child node."""
        return self.get_first_child()

    @property
    def index(self):
        """Get the node index."""
        return self.get_index()

    @property
    def last_child(self):
        """Get the last child node."""
        return self.get_last_child()

    @property
    def level(self):
        """Get the node level."""
        return self.get_level()

    @property
    def parent(self):
        """Get node parent."""
        return self.tn_parent

    @property
    def parent_pk(self):
        """Get node parent pk."""
        return self.get_parent_pk()

    @property
    def priority(self):
        """Get node priority."""
        return self.get_priority()

    @classproperty
    def roots(cls):
        """Get a list with all root nodes."""
        return cls.get_roots()

    @property
    def root(self):
        """Get the root node for the current node."""
        return self.get_root()

    @property
    def root_pk(self):
        """Get the root node pk for the current node."""
        return self.get_root_pk()

    @property
    def siblings(self):
        """Get a list with all the siblings."""
        return self.get_siblings()

    @property
    def siblings_count(self):
        """Get the siblings count."""
        return self.get_siblings_count()

    @property
    def siblings_pks(self):
        """Get the siblings pks list."""
        return self.get_siblings_pks()

    @classproperty
    def tree(cls):
        """Get an n-dimensional dict representing the model tree."""
        return cls.get_tree()

    @classproperty
    def tree_display(cls):
        """Get a multiline string representing the model tree."""
        return cls.get_tree_display()

    @property
    def tn_order(self):
        """Return the materialized path."""
        return self.get_order()

# The End
