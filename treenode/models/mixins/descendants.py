# -*- coding: utf-8 -*-
"""
TreeNode Descendants Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from treenode.cache import treenode_cache, cached_method


class TreeNodeDescendantsMixin(models.Model):
    """TreeNode Descendants Mixin."""

    @cached_method
    def get_descendants_queryset(self, include_self=False, depth=None):
        """Get the descendants queryset."""
        queryset = self._meta.model.objects\
            .annotate(min_depth=models.Min("parents_set__depth"))\
            .filter(parents_set__parent=self.pk)

        if depth is not None:
            queryset = queryset.filter(min_depth__lte=depth)
        if include_self and not queryset.filter(pk=self.pk).exists():
            queryset = queryset | self._meta.model.objects.filter(pk=self.pk)

        return queryset.order_by("min_depth", "tn_priority")

    @cached_method
    def get_descendants_pks(self, include_self=False, depth=None):
        """Get the descendants pks list."""
        cache_key = treenode_cache.generate_cache_key(
            label=self._meta.label,
            func_name=getattr(self, "get_descendants_queryset").__name__,
            unique_id=self.pk,
            arg={
                "include_self": include_self,
                "depth": depth
            }
        )
        queryset = treenode_cache.get(cache_key)
        if queryset is not None:
            return list(queryset.values_list("id", flat=True))
        elif hasattr(self, "closure_model"):
            return self.closure_model.get_descendants_pks(
                self, include_self, depth
            )
        return []

    def get_descendants(self, include_self=False, depth=None):
        """Get a list containing all descendants."""
        queryset = self.get_descendants_queryset(include_self, depth)
        return list(queryset)

    def get_descendants_count(self, include_self=False, depth=None):
        """Get the descendants count."""
        return len(self.get_descendants_pks(include_self, depth))

# The End
