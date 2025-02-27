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

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import json
from django import forms
from django.utils.translation import gettext_lazy as _


class TreeWidget(forms.Select):
    """Custom Select2 widget for hierarchical data."""

    class Media:
        """Meta Class."""

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
        """
        Buld attributes for widget.

        Add attributes for Select2 integration and pass model label via
        data-forward.
        """
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-url", "/treenode/tree-autocomplete/")
        existing_class = attrs.get("class", "")
        attrs["class"] = f"{existing_class} tree-widget".strip()
        if "placeholder" in attrs:
            del attrs["placeholder"]

        # Ensure the model is passed. Use it to send the model's label in
        # JSON format.
        if "data-forward" not in attrs:
            model = getattr(self, "model", None)
            if not model and hasattr(self.choices, "queryset"):
                model = self.choices.queryset.model
            if model is None:
                raise ValueError("TreeWidget: model not passed or not defined")
            try:
                label = model._meta.label
                forward_data = {"model": label}
                attrs["data-forward"] = json.dumps(forward_data)
            except AttributeError as e:
                raise ValueError(
                    "TreeWidget: model object is not a valid Django model"
                ) from e

        # If there is a current value, set it to data-selected
        if self.choices:
            try:
                current_value = self.value()
                if current_value:
                    attrs["data-selected"] = str(current_value)
            except Exception:
                pass

        return attrs

    def optgroups(self, name, value, attrs=None):
        """
        Option Generation.

        Redefine option generation to return only three items:
        1. "Select node" – hint option.
        2. "Root" – to select the root node (value "0").
        3. If the value is set and is not equal to an empty string or "0",
           then add the selected option.
        """
        groups = []
        subgroup = []

        # Опция 1: подсказка
        prompt_option = self.create_option(
            name,
            "",
            index=0,
            label=_("--- Select value ---"),
            selected=(not value or value[0] == "")
        )
        subgroup.append(prompt_option)

        # Option 2: root node ("Root")
        root_selected = (value and value[0] == "0")
        root_option = self.create_option(
            name,
            "0",
            index=1,
            label=_("Root"),
            selected=root_selected
        )
        subgroup.append(root_option)

        # Option 3: If a value other than an empty string or "0" is selected
        if value and value[0] not in ("", "0"):
            selected_label = None
            # Find the label of the selected item in the choices list
            for opt in list(self.choices):
                opt_value, opt_label = opt
                if str(opt_value) == str(value[0]):
                    selected_label = opt_label
                    break
            if not selected_label:
                selected_label = value[0]
            selected_option = self.create_option(
                name,
                value[0],
                index=2,
                label=selected_label,
                selected=True
            )
            subgroup.append(selected_option)

        groups.append(("", subgroup, 0))
        return groups

# The End
