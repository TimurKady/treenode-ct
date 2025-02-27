# -*- coding: utf-8 -*-
"""
TreeNode Views Module

This module provides API views for handling AJAX requests related to
tree-structured data in Django. It supports Select2 autocomplete
and retrieving child node counts.

Features:
- `TreeNodeAutocompleteView`: Returns JSON data for Select2 with hierarchical
   structure.
- `GetChildrenCountView`: Retrieves the number of children for a given
   parent node.
- Uses optimized QuerySets for efficient database queries.
- Handles validation and error responses gracefully.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.http import JsonResponse
from django.views import View
from django.apps import apps
from django.core.serializers import serialize, deserialize
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from .cache import treenode_cache


class TreeNodeAutocompleteView(View):
    """
    Return JSON data for Select2 with tree structure.

    Lazy load tree nodes for Select2 scrolling with reference node support.
    """

    def get(self, request):
        """
        Process an AJAX request to lazily load tree nodes.

        Changes:
        1. If a node is not selected (selected_id is missing), the first
           2*limit nodes are returned.
        2. The full list of nodes is loaded, sorted by the calculated tn_order,
           and then the required portion is selected relative to the index of
           the selected node.
        3. For the "up" and "down" directions, a reference node is determined,
           which is returned in the reference_id field.
        4. Optimization: since tn_order is not a DB field, it cannot be filtered
           by it - so the entire selection occurs in memory.
        """
        # Model
        model_label = request.GET.get("model")
        # Search string
        q = request.GET.get("q", "")
        # ID of the current node (if selected)
        selected_id = request.GET.get("selected_id")
        # "up", "down" or "center"
        direction = request.GET.get("direction", "center")
        # Number of nodes to load
        limit = int(request.GET.get("limit", 10))

        if not model_label:
            return JsonResponse(
                {"error": "Missing model parameter"},
                status=400
            )

        try:
            model = apps.get_model(model_label)
        except LookupError:
            return JsonResponse(
                {"error": f"Invalid model: {model_label}"},
                status=400
            )

        # Load all nodes through cache
        sorted_queryset = self.get_sorted_queryset(model, q)

        if not selected_id:
            # If the node is not selected, return the first 2*limit nodes
            nodes = sorted_queryset[:(2 * limit)]
            reference_node = nodes[-1] if nodes else None
        else:
            try:
                selected_node = model.objects.get(pk=selected_id)
            except ObjectDoesNotExist:
                return JsonResponse(
                    {"error": "Selected node not found"},
                    status=404
                )

            # Find the index of the selected node in the sorted list
            selected_index = None
            for i, node in enumerate(sorted_queryset):
                if node.pk == selected_node.pk:
                    selected_index = i
                    break
            if selected_index is None:
                return JsonResponse(
                    {"error": "Selected node not found in sorted list"},
                    status=404
                )

            if direction == "up":
                # Nodes with indices from (selected_index - limit) to
                # selected_index (not including selected)
                start = max(0, selected_index - limit)
                nodes = sorted_queryset[start:selected_index]
                reference_node = nodes[0] if nodes else selected_node
            elif direction == "down":
                # Nodes with indices from selected_index+1 to
                # selected_index + limit
                end = min(len(sorted_queryset), selected_index + 1 + limit)
                nodes = sorted_queryset[selected_index + 1:end]
                reference_node = nodes[-1] if nodes else selected_node
            else:  # center
                # Nodes around selected: from (selected_index - limit) to
                # (selected_index + limit)
                start = max(0, selected_index - limit)
                end = min(len(sorted_queryset), selected_index + limit + 1)
                nodes = sorted_queryset[start:end]
                reference_node = selected_node

        results = [
            {
                "id": node.pk,
                "text": node.name,
                "level": node.get_level(),
                "is_leaf": node.is_leaf(),
            }
            for node in nodes
        ]

        if q == '':
            root_option = {
                "id": "",
                "text": _("Root"),
                "level": 0,
                "is_leaf": True,
            }
            results.insert(0, root_option)

        response_data = {"results": results}

        if reference_node:
            response_data["reference_id"] = reference_node.pk

        return JsonResponse(response_data)

    def get_sorted_queryset(self, model, q):
        """Return sorted node list from cache."""
        cache_key = treenode_cache.generate_cache_key(
            self._meta.label,
            self.get_sorted_queryset.__name__,
            id(self.__class__),
            str(q)
        )

        json_str = treenode_cache.get(cache_key)
        if json_str:
            sorted_queryset = [
                obj.object for obj in deserialize("json", json_str)
            ]
            return sorted_queryset

        queryset = model.objects.filter(name__icontains=q)
        queryset_list = list(queryset)
        if not queryset_list:
            return JsonResponse({"results": []})

        sorted_queryset = model._sort_node_list(queryset_list)
        json_str = serialize("json", sorted_queryset)
        treenode_cache.set(cache_key, sorted_queryset)

        return sorted_queryset

# The End
