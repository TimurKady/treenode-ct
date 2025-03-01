# -*- coding: utf-8 -*-
"""
TreeNode Admin Module

This module provides Django admin integration for the TreeNode model.
It includes custom tree-based sorting, optimized queries, and
import/export functionality for hierarchical data structures.

Version: 2.1.0
Author: Timur Kady
Email: kaduevtr@gmail.com
"""


import importlib
from django.contrib import admin
from django.db import models
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe


from .changelist import SortedChangeList
from .mixins import AdminMixin
from ..forms import TreeNodeForm
from ..widgets import TreeWidget

import logging

logger = logging.getLogger(__name__)


class TreeNodeAdminModel(AdminMixin, admin.ModelAdmin):
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

    def drag(self, obj):
        """Display an empty column with an icon for future drag-and-drop."""
        icon = "↕"  # &nbsp;"
        return mark_safe(f'<span class="treenode-drag-handle">{icon}</span>')

    drag.short_description = ""

    def toggle(self, obj):
        """Добавление кнопки для открытия/закрытия поддерева, если есть дети."""
        icon = "▶"  # ▼ - for open; reserve set: 📁 📂
        if obj.children.exists():
            return mark_safe(
                f'<button class="treenode-toggle" '
                f'data-node-id="{obj.pk}">'
                f'{icon}'
                f'</button>')
        return '<div class="treenode-space">&nbsp;</div>'

    toggle.short_description = ""

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
        """
        Get QuerySet.

        Redefine the query so that by default only root nodes (nodes with
        tn_parent=None) are loaded. If there is a search query (parameter "q"),
        return the full list.
        """
        qs = super().get_queryset(request)
        if not request.GET.get("q"):
            qs = qs.filter(tn_parent__isnull=True)
        field_name = getattr(self.model, 'treenode_display_field')
        if not field_name:
            return qs.none()
        return qs.select_related('tn_parent')\
            .filter(**{f"{field_name}__icontains: q"})

    def get_form(self, request, obj=None, **kwargs):
        """Get Form method."""
        form = super().get_form(request, obj, **kwargs)
        if "tn_parent" in form.base_fields:
            form.base_fields["tn_parent"].widget = TreeWidget()
        return form

    def get_search_fields(self, request):
        """Return the correct search field."""
        return [self.model.treenode_display_field]

    def get_list_display(self, request):
        """Generate list_display dynamically with user-defined preferences."""
        change_view_cols = (self.drag, self.toggle)
        user_list_display = list(super().get_list_display(request))

        treenode_display_field = getattr(
            self.model,
            'treenode_display_field',
            '__str__'
        )

        def treenode_field(obj):
            return self._get_treenode_field_display(request, obj)

        treenode_field.short_description = self.model._meta.verbose_name
        treenode_field.allow_tags = True

        # If the custom list is empty or contains only '__str__'
        if not user_list_display or user_list_display == ['__str__']:
            result = (treenode_field,)
        else:
            # Remove `treenode_display_field` if it is the first one and
            # insert `treenode_field`
            if user_list_display[0] == treenode_display_field:
                clean_list = user_list_display[1:]
            else:
                clean_list = user_list_display

            # Гарантируем, что treenode_field есть в списке
            if treenode_field not in clean_list:
                clean_list.insert(0, treenode_field)

            result = tuple(clean_list)

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

    # ------------------------------------------------------------------------

    def _get_treenode_field_display(self, request, obj):
        """
        Return the HTML display of the accordion node.

        Modes:
        - ACCORDION: '&nbsp;' * level + icon + str(node),
          where icon = "📁 " if obj.is_leaf() returns True, otherwise "📄 ".
        - BREADCRUMBS: " / ".join(obj.get_breadcrumbs(attr=field)),
          where field = getattr(self.model, 'treenode_display_field', None)
          or "tn_priority" if None.
        - INDENTATION: '&mdash;' * level + str(node)
        """
        # Determine the node level
        level = obj.get_depth()

        mode = self.treenode_display_mode
        if mode == self.TREENODE_DISPLAY_MODE_ACCORDION:
            icon = "📁 " if obj.is_leaf() else "📄 "
            content = "&nbsp;" * level + icon + str(obj)
        elif mode == self.TREENODE_DISPLAY_MODE_BREADCRUMBS:
            field = getattr(
                self.model,
                'treenode_display_field',
                None) or "tn_priority"
            content = " / ".join(obj.get_breadcrumbs(attr=field))
        elif mode == self.TREENODE_DISPLAY_MODE_INDENTATION:
            content = "&mdash;" * level + str(obj)
        else:
            # Just in case mode is not recognized, then use breadcrumbs
            field = getattr(
                self.model,
                'treenode_display_field',
                None) or "tn_priority"
            content = " / ".join(obj.get_breadcrumbs(attr=field))

        parent = str(getattr(obj, "tn_parent_id", "") or "")
        html = (
            f'<div class="treenode-wrapper" '
            f'data-treenode-pk="{obj.pk}" '
            f'data-treenode-depth="{level}" '
            f'data-treenode-parent="{parent}">'
            f'<span class="treenode-content">{content}</span>'
            f'</div>'
        )
        return mark_safe(html)


# The End
