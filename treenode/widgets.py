# -*- coding: utf-8 -*-
"""
TreeNode Widgets Module

This module defines custom form widgets for handling hierarchical data
within Django's admin interface. It includes a Select2-based widget
for tree-structured data selection.

Features:
- `TreeWidget`: A custom Select2 widget that enhances usability for
  hierarchical models.
- Automatically fetches hierarchical data via AJAX.
- Supports dynamic model binding for reusable implementations.
- Integrates with Django’s form system.

Version: 2.0.11
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django import forms


class TreeWidget(forms.Select):
    """Custom Select2 widget for hierarchical data."""

    class Media:
        """Mrta class."""

        css = {
            "all": (
                "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css",
                "treenode/css/tree_widget.css",
            )
        }
        js = (
            "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js",
            "treenode/js/tree_widget.js",
        )

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Add attributes for Select2 integration."""
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-url", "/treenode/tree-autocomplete/")
        existing_class = attrs.get("class", "")
        attrs["class"] = f"{existing_class} tree-widget".strip()
        if "placeholder" in attrs:
            del attrs["placeholder"]

        # Force passing `model`
        if "data-forward" not in attrs:
            model = getattr(self, "model", None)
            if not model and hasattr(self.choices, "queryset"):
                model = self.choices.queryset.model
            if model is None:
                raise ValueError("TreeWidget: model not passed or not defined")

            try:
                label = model._meta.label
                attrs["data-forward"] = f'{{"model": "{label}"}}'
            except AttributeError as e:
                raise ValueError(
                    "TreeWidget: model object is not a valid Django model"
                ) from e

        # Force focus to current value
        if self.choices:
            try:
                current_value = self.value()
                if current_value:
                    attrs["data-selected"] = str(current_value)
            except Exception:
                # In case the value is missing
                pass

        return attrs

# The End
