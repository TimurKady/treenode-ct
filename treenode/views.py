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
import numpy as np
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
        Обрабатывает AJAX-запрос для ленивой загрузки узлов дерева.

        Изменения:
          1. Если узел не выбран (selected_id отсутствует), возвращаются первые 2*limit узлов.
          2. Загружается полный список узлов, сортируется по вычисляемому tn_order (через numpy),
             после чего выбирается нужная порция относительно индекса выбранного узла.
          3. Для направления "up" и "down" определяется reference-узел, который возвращается в поле reference_id.
          4. URL остаётся прежним.
          5. Оптимизация: поскольку tn_order – не поле БД, фильтровать по нему нельзя – поэтому вся выборка происходит в памяти.
             Если дерево очень большое, стоит задуматься о переходе к материализованному пути.
        """
        # Model
        model_label = request.GET.get("model")
        # Search string
        q = request.GET.get("q", "")
        # ID текущего узла (если выбран)
        selected_id = request.GET.get("selected_id")
        # "up", "down" или "center"
        direction = request.GET.get("direction", "center")
        # Количество узлов для загрузки
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

        # Загружаем все узлы через кэш
        sorted_queryset = self.get_sorted_queryset(model, q)

        if not selected_id:
            # Если узел не выбран – возвращаем первые 2*limit узлов
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

            # Находим индекс выбранного узла в отсортированном списке
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
                # Узлы с индексами от (selected_index - limit) до selected_index (не включая выбранный)
                start = max(0, selected_index - limit)
                nodes = sorted_queryset[start:selected_index]
                reference_node = nodes[0] if nodes else selected_node
            elif direction == "down":
                # Узлы с индексами от selected_index+1 до selected_index+limit
                end = min(len(sorted_queryset), selected_index + 1 + limit)
                nodes = sorted_queryset[selected_index + 1:end]
                reference_node = nodes[-1] if nodes else selected_node
            else:  # center
                # Узлы вокруг выбранного: от (selected_index - limit) до (selected_index + limit)
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
            q
        )

        sorted_queryset = treenode_cache.get(cache_key)
        if sorted_queryset is not None:
            return sorted_queryset

        queryset = model.objects.filter(name__icontains=q)
        qs = list(queryset)
        if not qs:
            return JsonResponse({"results": []})

        tn_orders = np.array([node.tn_order for node in qs])
        sorted_indices = np.argsort(tn_orders)
        sorted_queryset = [qs[int(idx)] for idx in sorted_indices]

        treenode_cache.set(cache_key, sorted_queryset)
        return sorted_queryset


class GetChildrenCountView(View):
    """Return the number of children for a given parent node."""

    def get(self, request):
        """Get method."""
        parent_id = request.GET.get("parent_id")
        model_label = request.GET.get("model")  # Получаем модель

        if not model_label or not parent_id:
            return JsonResponse({"error": "Missing parameters"}, status=400)

        try:
            model = apps.get_model(model_label)
        except LookupError:
            return JsonResponse(
                {"error": f"Invalid model: {model_label}"},
                status=400
            )

        try:
            parent_node = model.objects.get(pk=parent_id)
            children_count = parent_node.get_children_count()
        except ObjectDoesNotExist:
            return JsonResponse(
                {"error": "Parent node not found"},
                status=404
            )

        return JsonResponse({"children_count": children_count})
