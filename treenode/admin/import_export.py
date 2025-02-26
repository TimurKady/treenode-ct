# -*- coding: utf-8 -*-
"""
Inport/Export Mixin for TreeNodeAdminModel

Version: 2.1.0
Author: Timur Kady
Email: kaduevtr@gmail.com
"""

import os
from django.contrib import admin
from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from django.shortcuts import resolve_url
from django.utils.encoding import force_str
from django.urls import path

import logging

logger = logging.getLogger(__name__)


class ImportExportMixin(admin.ModelAdmin):
    """Inport/Export Mixin."""

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
