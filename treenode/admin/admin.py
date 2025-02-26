# -*- coding: utf-8 -*-
"""
TreeNode Admin Module

This module provides Django admin integration for the TreeNode model.
It includes custom tree-based sorting, optimized queries, and
import/export functionality for hierarchical data structures.

Version: 2.0.11
Author: Timur Kady
Email: kaduevtr@gmail.com
"""


import importlib
from django.contrib import admin
from django.db import models
from django.http import HttpResponseRedirect
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


from .changelist import SortedChangeList
from .import_export import ImportExportMixin
from ..forms import TreeNodeForm
from ..widgets import TreeWidget

import logging

logger = logging.getLogger(__name__)


class TreeNodeAdminModel(ImportExportMixin, admin.ModelAdmin):
    """
    TreeNodeAdmin class.

    Admin configuration for TreeNodeModel with import/export functionality.
    """

    TREENODE_DISPLAY_MODE_ACCORDION = 'accordion'
    TREENODE_DISPLAY_MODE_BREADCRUMBS = 'breadcrumbs'
    TREENODE_DISPLAY_MODE_INDENTATION = 'indentation'

    treenode_display_mode = TREENODE_DISPLAY_MODE_ACCORDION
    import_export = False  # Track import/export availability
    change_list_template = "admin/tree_node_changelist.html"
    ordering = []
    list_per_page = 1000
    list_sorting_mode_session_key = "treenode_sorting_mode"

    form = TreeNodeForm
    formfield_overrides = {
        models.ForeignKey: {"widget": TreeWidget()},
    }

    class Media:
        """Include custom CSS and JavaScript for admin interface."""

        css = {"all": (
            "treenode/css/treenode_admin.css",
        )}
        js = (
            'admin/js/jquery.init.js',
            'treenode/js/treenode_admin.js',
        )

    def drag_handle(self, obj):
        """Display an empty column with an icon for future drag-and-drop."""
        icon = "&nbsp;"
        return mark_safe(
            f'<span class="drag-handle" '
            f'style="cursor: grab; opacity: 0.25;">'
            f'{icon}</span>'
        )

    drag_handle.short_description = ""

    def toggle_children(self, obj):
        """Добавление кнопки для открытия/закрытия поддерева, если есть дети."""
        icon = "&nbsp;"
        if obj.children.exists():
            return mark_safe(
                f'<button class="toggle-children" '
                f'data-node-id="{obj.pk}" '
                f'style="cursor: pointer;">{icon}'
                f'</button>')
        return ""

    toggle_children.short_description = ""

    def __init__(self, model, admin_site):
        """Init method."""
        super().__init__(model, admin_site)

        # If `list_display` is empty, take all `fields`
        if not self.list_display:
            self.list_display = [field.name for field in model._meta.fields]

        # Check for necessary dependencies
        self.import_export = all([
            importlib.util.find_spec(pkg) is not None
            for pkg in ["openpyxl", "yaml", "xlsxwriter"]
        ])
        if not self.import_export:
            check_results = [
                pkg for pkg in ["openpyxl", "pyyaml", "xlsxwriter"]
                if importlib.util.find_spec(pkg) is not None
            ]
            logger.info("Packages" + ", ".join(check_results) + " are \
not installed. Export and import functions are disabled.")

        if self.import_export:
            from .utils import TreeNodeImporter, TreeNodeExporter

            self.TreeNodeImporter = TreeNodeImporter
            self.TreeNodeExporter = TreeNodeExporter
        else:
            self.TreeNodeImporter = None
            self.TreeNodeExporter = None

    def get_queryset(self, request):
        """Override get_queryset to simply return an optimized queryset."""
        queryset = super().get_queryset(request)
        # If a search term is present, leave the queryset as is.
        if request.GET.get("q"):
            return queryset
        return queryset.select_related('tn_parent')

    def get_search_fields(self, request):
        """Return the correct search field."""
        return [self.model.treenode_display_field]

    def get_list_display(self, request):
        """
        Generate list_display dynamically.

        Return list or tuple of field names that will be displayed in the
        change list view.
        """
        change_view_cols = tuple(self.drag_handle, self.toggle_children)
        base_list_display = list(super().get_list_display(request))

        def treenode_field_display(obj):
            return self._get_treenode_field_display(request, obj)

        verbose_name = self.model._meta.verbose_name
        treenode_field_display.short_description = verbose_name
        treenode_field_display.allow_tags = True

        if len(base_list_display) == 1 and base_list_display[0] == '__str__':
            base_list_display[2] = treenode_field_display
            result = tuple(treenode_field_display,)
        else:
            treenode_display_field = getattr(
                self.model,
                'treenode_display_field',
                '__str__'
            )
            if base_list_display[0] == treenode_display_field:
                base_list_display.pop(0)
            result = tuple(treenode_field_display,) + tuple(base_list_display)
        return change_view_cols + result

    def get_changelist(self, request):
        """Use SortedChangeList to sort the results at render time."""
        return SortedChangeList

    def changelist_view(self, request, extra_context=None):
        """Changelist View."""
        extra_context = extra_context or {}
        extra_context['import_export_enabled'] = self.import_export

        response = super().changelist_view(request, extra_context=extra_context)

        # If response is a redirect, then there is no point in updating
        # ChangeList
        if isinstance(response, HttpResponseRedirect):
            return response

        if request.GET.get("import_done"):
            # Create a ChangeList instance manually
            ChangeListClass = self.get_changelist(request)

            cl = ChangeListClass(
                request, self.model, self.list_display, self.list_display_links,
                self.list_filter, self.date_hierarchy, self.search_fields,
                self.list_select_related, self.list_per_page,
                self.list_max_show_all, self.list_editable, self
            )

            # Force queryset update and apply sorting
            cl.get_queryset(request)
            cl.get_results(request)

            # Add updated ChangeList to context
            response.context_data["cl"] = cl

        return response

    def get_ordering(self, request):
        """Get Ordering."""
        return None

    def _get_row_display(self, obj):
        """Return row display for accordion mode."""
        field = getattr(self.model, 'treenode_display_field')
        return force_str(getattr(obj, field, obj.pk))

    def _get_treenode_field_display(self, request, obj):
        """Define how to display nodes depending on the mode."""
        display_mode = self.treenode_display_mode
        if display_mode == self.TREENODE_DISPLAY_MODE_ACCORDION:
            return self._display_with_accordion(obj)
        elif display_mode == self.TREENODE_DISPLAY_MODE_BREADCRUMBS:
            return self._display_with_breadcrumbs(obj)
        elif display_mode == self.TREENODE_DISPLAY_MODE_INDENTATION:
            return self._display_with_indentation(obj)
        else:
            return self._display_with_breadcrumbs(obj)

    def _display_with_accordion(self, obj):
        """Display a tree in accordion style."""
        parent = str(obj.tn_parent_id or '')
        text = self._get_row_display(obj)
        html = (
            f'<div class="treenode-wrapper" '
            f'data-treenode-pk="{obj.pk}" '
            f'data-treenode-depth="{obj.depth}" '
            f'data-treenode-parent="{parent}">'
            f'<span class="treenode-content">{text}</span>'
            f'</div>'
        )
        return mark_safe(html)

    def _display_with_breadcrumbs(self, obj):
        """Display a tree as breadcrumbs."""
        field = getattr(self.model, 'treenode_display_field')
        if field is not None:
            obj_display = " / ".join(obj.get_breadcrumbs(attr=field))
        else:
            obj_display = obj.get_path(
                prefix=_("Node "),
                suffix=" / " + obj.__str__()
            )
        display = f'<span class="treenode-breadcrumbs">{obj_display}</span>'
        return mark_safe(display)

    def _display_with_indentation(self, obj):
        """Display tree with indents."""
        indent = '&mdash;' * obj.get_depth()
        display = f'<span class="treenode-indentation">{indent}</span> {obj}'
        return mark_safe(display)

    def get_form(self, request, obj=None, **kwargs):
        """Get Form method."""
        form = super().get_form(request, obj, **kwargs)
        if "tn_parent" in form.base_fields:
            form.base_fields["tn_parent"].widget = TreeWidget()
        return form


# The End
