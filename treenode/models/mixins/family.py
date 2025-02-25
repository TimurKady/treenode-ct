# -*- coding: utf-8 -*-
"""
TreeNode Descendants Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from treenode.cache import cached_method


class TreeNodeFamilyMixin(models.Model):
    """TreeNode Family Mixin."""

    @cached_method
    def get_family_queryset(self):
        """
        Return node family.

        Return a QuerySet containing the ancestors, itself and the descendants,
        in tree order.
        """
        model = self._meta.model
        queryset = model.objects.filter(
            models.Q(tn_closure__child=self.pk) |
            models.Q(tn_closure__parent=self.pk) |
            models.Q(pk=self.pk)
        ).distinct().order_by("tn_closure__depth", "tn_parent", "tn_priority")
        return queryset

    @cached_method
    def get_family_pks(self):
        """
        Return node family.

        Return a pk-list containing the ancestors, the model itself and
        the descendants, in tree order.
        """
        pks = self.get_family_queryset().values_list("id", flat=True)
        return list(pks)

    def get_family(self):
        """
        Return node family.

        Return a list containing the ancestors, the model itself and
        the descendants, in tree order.
        """
        queryset = self.get_family_queryset()
        return list(queryset)

    def get_family_count(self):
        """
        Return node family.

        Return a pk-list containing the ancestors, the model itself and
        the descendants, in tree order.
        """
        return self.get_family_queryset().count()
