# -*- coding: utf-8 -*-
"""
TreeNode Ancestors Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from treenode.cache import treenode_cache, cached_method


class TreeNodeAncestorsMixin(models.Model):
    """TreeNode Ancestors Mixin."""

    @cached_method
    def get_ancestors_queryset(self, include_self=True, depth=None):
        """Get the ancestors queryset (ordered from root to parent)."""
        qs = self._meta.model.objects.filter(tn_closure__child=self.pk)

        if depth is not None:
            qs = qs.filter(tn_closure__depth__lte=depth)

        if include_self:
            qs = qs | self._meta.model.objects.filter(pk=self.pk)

        return qs.distinct().order_by("tn_closure__depth")

    @cached_method
    def get_ancestors_pks(self, include_self=True, depth=None):
        """Get the ancestors pks list."""
        cache_key = treenode_cache.generate_cache_key(
            label=self._meta.label,
            func_name=getattr(self, "get_ancestors_queryset").__name__,
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
            return self.closure_model.get_ancestors_pks(
                self, include_self, depth
            )
        return []

    def get_ancestors(self, include_self=True, depth=None):
        """Get a list with all ancestors (ordered from root to self/parent)."""
        queryset = self.get_ancestors_queryset(include_self, depth)
        return list(queryset)

    def get_ancestors_count(self, include_self=True, depth=None):
        """Get the ancestors count."""
        return len(self.get_ancestors_pks(include_self, depth))
