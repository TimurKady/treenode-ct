# -*- coding: utf-8 -*-
"""
TreeNode Proxy Model

This module defines an abstract base model `TreeNodeModel` that
implements hierarchical data storage using the Adjacency Table method.
It integrates with a Closure Table for optimized tree operations.

Features:
- Supports Adjacency List representation with parent-child relationships.
- Integrates with a Closure Table for efficient ancestor and descendant
  queries.
- Provides a caching mechanism for performance optimization.
- Includes methods for tree traversal, manipulation, and serialization.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models, transaction
from django.db.models.signals import pre_save, post_save

from .factory import TreeFactory
import treenode.models.mixins as mx
from ..managers import TreeNodeModelManager
from ..cache import treenode_cache, cached_method
from ..signals import disable_signals
import logging

logger = logging.getLogger(__name__)


class TreeNodeModel(
        mx.TreeNodeAncestorsMixin, mx.TreeNodeChildrenMixin,
        mx.TreeNodeFamilyMixin, mx.TreeNodeDescendantsMixin,
        mx.TreeNodeLogicalMixin, mx.TreeNodeNodeMixin,
        mx.TreeNodePropertiesMixin, mx.TreeNodeRootsMixin,
        mx.TreeNodeSiblingsMixin, mx.TreeNodeTreeMixin,
        models.Model, metaclass=TreeFactory):
    """
    Abstract TreeNode Model.

    Implements hierarchy storage using the Adjacency Table method.
    To increase performance, it has an additional attribute - a model
    that stores data from the Adjacency Table in the form of
    a Closure Table.
    """

    treenode_display_field = None
    treenode_sort_field = None  # not now
    closure_model = None

    tn_parent = models.ForeignKey(
        'self',
        related_name='tn_children',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    tn_priority = models.PositiveIntegerField(default=0)

    objects = TreeNodeModelManager()

    class Meta:
        """Meta Class."""

        abstract = True
        indexes = [
            models.Index(fields=["tn_parent"]),
            models.Index(fields=["tn_parent", "id"]),
            models.Index(fields=["tn_parent", "tn_priority"]),
        ]

    def __str__(self):
        """Display information about a class object."""
        if self.treenode_display_field:
            return str(getattr(self, self.treenode_display_field))
        else:
            return 'Node %d' % self.pk

    # ---------------------------------------------------
    # Public methods
    # ---------------------------------------------------

    @classmethod
    def clear_cache(cls):
        """Clear cache for this model only."""
        treenode_cache.invalidate(cls._meta.label)

    @classmethod
    def get_closure_model(cls):
        """Return ClosureModel for class."""
        return cls.closure_model

    def delete(self, cascade=True):
        """Delete node."""
        model = self._meta.model

        if not cascade:
            # Get a list of children
            children = self.get_children()
            # Move them to one level up
            for child in children:
                child.tn_parent = self.tn_parent
            # Udate both models in bulk
            model.objects.bulk_update(
                children,
                ("tn_parent",),
                batch_size=1000
            )
        # All descendants and related records in the ClosingModel will be
        # cleared by cascading the removal of ForeignKeys.
        super().delete()
        # Can be excluded. The cache has already been cleared by the manager.
        model.clear_cache()

    def save(self, force_insert=False, *args, **kwargs):
        """Save a model instance with sync closure table."""
        model = self._meta.model
        # Send signal pre_save
        pre_save.send(
            sender=model,
            instance=self,
            raw=False,
            using=self._state.db,
            update_fields=kwargs.get("update_fields", None)
        )

        # If the object already exists, get the old parent and priority values
        is_new = self.pk is None
        if not is_new:
            old_parent, old_priority = model.objects\
                .filter(pk=self.pk)\
                .values_list('tn_parent', 'tn_priority')\
                .first()
            is_move = (old_priority != self.tn_priority)
        else:
            force_insert = True
            is_move = False
            old_parent = None

        # Check if we are trying to move a node to a child
        if old_parent and old_parent != self.tn_parent and self.tn_parent:
            # Get pk of children via values_list to avoid creating full
            # set of objects
            if self.tn_parent.pk in self.get_descendants_pks():
                raise ValueError("You cannot move a node into its own child.")

        # Save the object and synchronize with the closing table
        with transaction.atomic():
            # Disable signals
            with (disable_signals(pre_save, model),
                  disable_signals(post_save, model)):
                super().save(force_insert=force_insert, *args, **kwargs)
                # Run synchronize
                if is_new:
                    self.closure_model.insert_node(self)
                elif is_move:
                    subtree_nodes = self.get_descendants(include_self=True)
                    self.closure_model.move_node(subtree_nodes)
                # Update priorities among neighbors or clear cache if there was
                # no movement
                if is_new or is_move:
                    self._update_priority()
        # Clear model cache
        model.clear_cache()
        # Send signal post_save
        post_save.send(sender=model, instance=self, created=is_new)

    # ---------------------------------------------------
    # Prived methods
    #
    # The usage of these methods is only allowed by developers. In future
    # versions, these methods may be changed or removed without any warning.
    # ---------------------------------------------------

    def _update_priority(self):
        """Update tn_priority field for siblings."""
        if self.tn_parent is None:
            # Node is a root
            parent = None
            queryset = self._meta.model.get_roots_queryset()
        else:
            # Node isn't a root
            parent = self.tn_parent
            queryset = parent.tn_children.all()

        siblings = list(queryset.exclude(pk=self.pk))
        sorted_siblings = sorted(siblings, key=lambda x: x.tn_priority)
        insert_pos = min(self.tn_priority, len(sorted_siblings))
        sorted_siblings.insert(insert_pos, self)
        for index, node in enumerate(sorted_siblings):
            node.tn_priority = index
        # Save changes
        model = self._meta.model
        with transaction.atomic():
            model.objects.bulk_update(sorted_siblings, ('tn_priority',))
        super().save(update_fields=['tn_priority'])
        model.clear_cache()

    def _get_place(cls, target, position=None):
        """
        Get position relative to the target node.

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

        """
        if not isinstance(position, str) or '-' not in position:
            raise ValueError(f"Invalid position format: {position}")

        part1, part2 = position.split('-')

        if part1 not in {'first', 'last', 'left', 'right', 'sorted'} or \
           part2 not in {'root', 'child', 'sibling'}:
            raise ValueError(f"Unknown position type: {position}")

        parent = (
            None if part2 == 'root' else
            target.tn_parent if part2 == 'sibling' else
            target if part2 == 'child' else None
        )

        count = cls.objects.filter(tn_parent=parent).count() if target else 0

        priority = (
            0 if part1 == 'first'else
            target.tn_priority if part1 == 'left' else
            target.tn_priority + 1 if part1 == 'right' else count
        )

        return parent, priority

    @classmethod
    @cached_method
    def _sort_node_list(cls, nodes):
        """
        Sort list of nodes by materialized path oreder.

        Collect the materialized path without accessing the DB and perform
        sorting
        """
        # Create a list of tuples: (node, materialized_path)
        nodes_with_path = [(node, node.tn_order) for node in nodes]
        # Sort the list by the materialized path
        nodes_with_path.sort(key=lambda tup: tup[1])
        # Extract sorted nodes
        return [tup[0] for tup in nodes_with_path]


# The end
