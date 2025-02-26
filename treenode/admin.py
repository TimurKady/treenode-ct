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


import os
import importlib
from datetime import datetime
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.views.main import ChangeList
from django.core.serializers import serialize, deserialize
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.shortcuts import resolve_url
from django.urls import path
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


from .forms import TreeNodeForm
from .widgets import TreeWidget
from .cache import treenode_cache

import logging

logger = logging.getLogger(__name__)


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


class TreeNodeAdminModel(admin.ModelAdmin):
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
        base_list_display = super().get_list_display(request)
        base_list_display = list(base_list_display)

        def treenode_field_display(obj):
            return self._get_treenode_field_display(request, obj)

        verbose_name = self.model._meta.verbose_name
        treenode_field_display.short_description = verbose_name
        treenode_field_display.allow_tags = True

        if len(base_list_display) == 1 and base_list_display[0] == '__str__':
            return (treenode_field_display,)
        else:
            treenode_display_field = getattr(
                self.model,
                'treenode_display_field',
                '__str__'
            )
            if base_list_display[0] == treenode_display_field:
                base_list_display.pop(0)
            return (treenode_field_display,) + tuple(base_list_display)

    def get_changelist(self, request):
        """Use SortedChangeList to sort the results at render time."""
        return SortedChangeList

    def changelist_view(self, request, extra_context=None):
        """Changelist View."""
        extra_context = extra_context or {}
        extra_context['import_export_enabled'] = self.import_export

        response = super().changelist_view(request, extra_context=extra_context)

        # Если response — это редирект, то нет смысла обновлять ChangeList
        if isinstance(response, HttpResponseRedirect):
            return response

        if request.GET.get("import_done"):
            # Создаём экземпляр ChangeList вручную
            ChangeListClass = self.get_changelist(request)

            cl = ChangeListClass(
                request, self.model, self.list_display, self.list_display_links,
                self.list_filter, self.date_hierarchy, self.search_fields,
                self.list_select_related, self.list_per_page,
                self.list_max_show_all, self.list_editable, self
            )

            # Принудительно обновляем queryset и применяем сортировку
            cl.get_queryset(request)
            cl.get_results(request)

            # Добавляем обновлённый ChangeList в контекст
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

    def get_urls(self):
        """
        Extend admin URLs with custom import/export routes.

        Register these URLs only if all the required packages are installed.
        """
        urls = super().get_urls()
        if self.import_export:
            custom_urls = [
                path('import/', self.import_view, name='tree_node_import'),
                path('export/', self.export_view, name='tree_node_export'),
            ]
        else:
            custom_urls = []
        return custom_urls + urls

    def import_view(self, request):
        """
        Import View.

        File upload processing, auto-detection of format, validation and data
        import.
        """
        if not self.import_export:
            self.message_user(
                request,
                "Import functionality is disabled because required \
packages are not installed."
            )
            return redirect("..")

        if request.method == 'POST':
            if 'file' not in request.FILES:
                return render(
                    request,
                    "admin/tree_node_import.html",
                    {"errors": ["No file uploaded."]}
                )

            file = request.FILES['file']
            ext = os.path.splitext(file.name)[-1].lower().strip(".")

            allowed_formats = {"csv", "json", "xlsx", "yaml", "tsv"}
            if ext not in allowed_formats:
                return render(
                    request,
                    "admin/tree_node_import.html",
                    {"errors": [f"Unsupported file format: {ext}"]}
                )

            # Import data from file
            importer = self.TreeNodeImporter(self.model, file, ext)
            raw_data = importer.import_data()
            clean_result = importer.finalize(raw_data)

            errors = clean_result.get("errors", [])
            created_count = len(clean_result.get("create", []))
            updated_count = len(clean_result.get("update", []))

            if errors:
                return render(
                    request,
                    "admin/tree_node_import_report.html",
                    {
                        "errors": errors,
                        "created_count": created_count,
                        "updated_count": updated_count,
                    }
                )

            # If there are no errors, redirect to the list of objects with
            # a message
            messages.success(
                request,
                f"Successfully imported {created_count} records. "
                f"Successfully updated {updated_count} records."
            )

            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            admin_changelist_url = f"admin:{app_label}_{model_name}_changelist"
            path = resolve_url(admin_changelist_url) + "?import_done=1"
            return redirect(path)

        # If the request is not POST, simply display the import form
        return render(request, "admin/tree_node_import.html")

    def export_view(self, request):
        """
        Export view.

        - If the GET parameters include download, we send the file directly.
        - If the format parameter is missing, we render the format selection
          page.
        - If the format is specified, we perform a test export to catch errors.

        If there are no errors, we render the success page with a message, a
        link for manual download,
        and a button to go to the model page.
        """
        if not self.import_export:
            self.message_user(
                request,
                "Export functionality is disabled because required \
packages are not installed."
            )
            return redirect("..")

        # If the download parameter is present, we give the file directly
        if 'download' in request.GET:
            # Get file format
            export_format = request.GET.get('format', 'csv')
            # Filename
            now = force_str(datetime.now().strftime("%Y-%m-%d %H-%M"))
            filename = self.model._meta.label + " " + now
            # Init
            exporter = self.TreeNodeExporter(
                self.get_queryset(request),
                filename=filename
            )
            # Export working
            response = exporter.export(export_format)
            logger.debug("DEBUG: File response generated.")
            return response

        # If the format parameter is not passed, we show the format
        # selection page
        if 'format' not in request.GET:
            return render(request, "admin/tree_node_export.html")

        # If the format is specified, we try to perform a test export
        # (without returning the file)
        export_format = request.GET['format']
        exporter = self.TreeNodeExporter(
            self.model.objects.all(),
            filename=self.model._meta.model_name
        )
        try:
            # Test call to check for export errors (result not used)
            exporter.export(export_format)
        except Exception as e:
            logger.error("Error during test export: %s", e)
            errors = [str(e)]
            return render(
                request,
                "admin/tree_node_export.html",
                {"errors": errors}
            )

        # Form the correct download URL. If the URL already contains
        # parameters, add them via &download=1, otherwise via ?download=1
        current_url = request.build_absolute_uri()
        if "?" in current_url:
            download_url = current_url + "&download=1"
        else:
            download_url = current_url + "?download=1"

        context = {
            "download_url": download_url,
            "message": "Your file is ready for export. \
The download should start automatically.",
            "manual_download_label": "If the download does not start, \
click this link.",
            # Can be replaced with the desired URL to return to the model
            "redirect_url": "../",
            "button_text": "Return to model"
        }
        return render(request, "admin/export_success.html", context)

# The End
