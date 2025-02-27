# -*- coding: utf-8 -*-
"""
TreeNode URL Configuration

This module defines URL patterns for handling AJAX requests related
to tree-structured data in Django. It includes endpoints for Select2
autocomplete and retrieving child node counts.

Routes:
- `tree-autocomplete/`: Returns JSON data for Select2 hierarchical selection.
- `get-children-count/`: Retrieves the number of children for a given
  parent node.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.urls import path
from .views import TreeNodeAutocompleteView, GetChildrenCountView

urlpatterns = [
    path(
        "tree-autocomplete/",
        TreeNodeAutocompleteView.as_view(),
        name="tree_autocomplete"
    ),
    path(
        "get-children-count/",
        GetChildrenCountView.as_view(),
        name="get_children_count"
    ),
]


# The End
