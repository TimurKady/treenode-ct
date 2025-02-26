# -*- coding: utf-8 -*-
"""
TreeNode Closure Model

This module defines the Closure Table implementation for hierarchical
data storage in the TreeNode model. It supports efficient queries for
retrieving ancestors, descendants, breadcrumbs, and tree depth.

Features:
- Uses a Closure Table for efficient tree operations.
- Implements cached queries for improved performance.
- Provides bulk operations for inserting, moving, and deleting nodes.

Version: 2.0.11
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.db import models, transaction
from django.db.models.signals import pre_save, post_save

from ..managers import ClosureModelManager
from ..sinals import disable_signals


class ClosureModel(models.Model):
    """
    Model for Closure Table.

    Implements hierarchy storage using the Closure Table method.
    """

    parent = models.ForeignKey(
        'TreeNodeModel',
        related_name='children_set',
        on_delete=models.CASCADE,
    )

    child = models.ForeignKey(
        'TreeNodeModel',
        related_name='parents_set',
        on_delete=models.CASCADE,
    )

    depth = models.PositiveIntegerField()

    node = models.OneToOneField(
        'TreeNodeModel',
        related_name="tn_closure",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    objects = ClosureModelManager()

    class Meta:
        """Meta Class."""

        abstract = True
        unique_together = (("parent", "child"),)
        indexes = [
            models.Index(fields=["parent", "child"]),
            models.Index(fields=["child", "parent"]),
            models.Index(fields=["parent", "child", "depth"]),
        ]

    def __str__(self):
        """Display information about a class object."""
        return f"{self.parent} — {self.child} — {self.depth}"

    # ----------- Methods of working with tree structure ----------- #

    @classmethod
    def get_ancestors_pks(cls, node, include_self=True, depth=None):
        """Get the ancestors pks list."""
        options = dict(child_id=node.pk, depth__gte=0 if include_self else 1)
        if depth:
            options["depth__lte"] = depth
        queryset = cls.objects.filter(**options)\
            .order_by('depth')\
            .values_list('parent_id', flat=True)
        return list(queryset.values_list("parent_id", flat=True))

    @classmethod
    def get_descendants_pks(cls, node, include_self=False, depth=None):
        """Get a list containing all descendants."""
        options = dict(parent_id=node.pk, depth__gte=0 if include_self else 1)
        if depth:
            options.update({'depth__lte': depth})
        queryset = cls.objects.filter(**options)\
            .order_by('depth')\
            .values_list('child_id', flat=True)
        return queryset

    @classmethod
    def get_root(cls, node):
        """Get the root node pk for the current node."""
        queryset = cls.objects.filter(child=node).order_by('-depth')
        return queryset.first().parent if queryset.count() > 0 else None

    @classmethod
    def get_depth(cls, node):
        """Get the node depth (how deep the node is in the tree)."""
        result = cls.objects.filter(child__pk=node.pk).aggregate(
            models.Max("depth")
        )["depth__max"]
        return result if result is not None else 0

    @classmethod
    def get_level(cls, node):
        """Get the node level (starting from 1)."""
        return cls.objects.filter(child__pk=node.pk).aggregate(
            models.Max("depth"))["depth__max"] + 1

    @classmethod
    @transaction.atomic
    def insert_node(cls, node):
        """Add a node to a Closure table."""
        # Call bulk_create passing a single object
        cls.objects.bulk_create([node], batch_size=1000)

    @classmethod
    @transaction.atomic
    def move_node(cls, nodes):
        """Move a nodes (node and its subtree) to a new parent."""
        # Call bulk_update passing a single object
        cls.objects.bulk_update(nodes, batch_size=1000)
        # Clear cache
        cls.clear_cache()

    @classmethod
    @transaction.atomic
    def delete_all(cls):
        """Clear the Closure Table."""
        cls.objects.all().delete()

    def save(self, force_insert=False, *args, **kwargs):
        """Save method."""
        with (disable_signals(pre_save, self._meta.model),
              disable_signals(post_save, self._meta.model)):
            super().save(force_insert, *args, **kwargs)

# The End
