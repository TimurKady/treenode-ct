# -*- coding: utf-8 -*-
"""
TreeNode Sorted ChangeList Class for TreeNodeAdminModel.

Version: 2.1.0
Author: Timur Kady
Email: kaduevtr@gmail.com
"""

from django.contrib.admin.views.main import ChangeList
from django.core.serializers import serialize, deserialize

from ..cache import treenode_cache


class SortedChangeList(ChangeList):
    """Custom ChangeList that sorts results in Python (after DB query)."""

    def get_ordering(self, request, queryset):
        """
        Override ordering.

        Overrides the sort order of objects in the list.
        Django Admin sorts by `-pk` (descending) by default.
        This method removes `-pk` so that objects are not sorted by ID.
        """
        # Remove the default '-pk' ordering if present.
        ordering = list(super().get_ordering(request, queryset))
        if '-pk' in ordering:
            ordering.remove('-pk')
        return tuple(ordering)

    def get_queryset(self, request):
        """Get QuerySet with select_related."""
        return super().get_queryset(request).select_related('tn_parent')

    def get_results(self, request):
        """Return sorted results for ChangeList rendering."""
        # Populate self.result_list with objects from the DB.
        super().get_results(request)
        result_list = self.result_list
        result_list_pks = ",".join(map(str, [obj.pk for obj in result_list]))

        cache_key = treenode_cache.generate_cache_key(
            self.model.label,
            self.get_results.__name__,
            id(self.__class__),
            result_list_pks
        )

        json_str = treenode_cache.get(cache_key)
        if json_str:
            sorted_results = [
                obj.object for obj in deserialize("json", json_str)
            ]
            self.result_list = sorted_results
            return

        sorted_result = self.model._sort_node_list(result_list)
        json_str = serialize("json", sorted_result)
        treenode_cache.set(cache_key, json_str)

        self.result_list = sorted_result
