# -*- coding: utf-8 -*-
"""
TreeNode Exporter Module

This module provides functionality for exporting tree-structured data
to various formats, including CSV, JSON, XLSX, YAML, and TSV.

Features:
- Supports exporting ForeignKey fields as IDs and ManyToMany fields as JSON
  lists.
- Handles complex field types (lists, dictionaries) with proper serialization.
- Provides optimized data extraction for QuerySets.
- Generates downloadable files with appropriate HTTP responses.

Version: 2.0.11
Author: Timur Kady
Email: timurkady@yandex.com
"""


import csv
import json
import yaml
import xlsxwriter
import numpy as np
import uuid
from io import BytesIO
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


class TreeNodeExporter:
    """Exporter for tree-structured data to various formats."""

    def __init__(self, queryset, filename="tree_nodes"):
        """
        Init.

        :param queryset: QuerySet of objects to export.
        :param filename: Filename without extension.
        """
        self.queryset = queryset
        self.filename = filename
        self.fields = [field.name for field in queryset.model._meta.fields]
        self.fields = self.get_ordered_fields()

    def export(self, format):
        """Determine the export format and calls the corresponding method."""
        exporters = {
            "csv": self.to_csv,
            "json": self.to_json,
            "xlsx": self.to_xlsx,
            "yaml": self.to_yaml,
            "tsv": self.to_tsv,
        }
        if format not in exporters:
            raise ValueError("Unsupported export format")
        return exporters[format]()

    def process_complex_fields(self, record):
        """Convert complex fields (lists, dictionaries) into JSON strings."""
        for key, value in record.items():
            if isinstance(value, uuid.UUID):
                record[key] = str(value)
            elif isinstance(value, (list, dict)):
                try:
                    record[key] = json.dumps(value, ensure_ascii=False)
                except Exception as e:
                    logger.warning("Error serializing field %s: %s", key, e)
                    record[key] = None
        return record

    def get_ordered_fields(self):
        """Return fields in the desired order.

        Order: id, tn_parent, tn_priority, then the rest.
        """
        required_fields = ["id", "tn_parent", "tn_priority"]
        other_fields = [
            field for field in self.fields if field not in required_fields]
        return required_fields + other_fields

    def get_sorted_queryset(self):
        """Quick sort queryset by tn_order."""
        queryset = self.queryset
        tn_orders = np.array([obj.tn_order for obj in queryset])
        sorted_indices = np.argsort(tn_orders)
        queryset_list = list(queryset.iterator())
        result = [queryset_list[int(idx)] for idx in sorted_indices]
        return result

    def get_data(self):
        """Return a list of data from QuerySet as dictionaries."""
        data = []
        for obj in self.get_sorted_queryset():
            record = {}
            for field in self.fields:
                value = getattr(obj, field, None)
                field_object = obj._meta.get_field(field)
                if field_object.is_relation:
                    if field_object.many_to_many:
                        # ManyToMany - save as a JSON string
                        record[field] = json.dumps(
                            list(value.values_list('id', flat=True)),
                            ensure_ascii=False)
                    elif field_object.many_to_one:
                        # ForeignKey - save as ID
                        record[field] = getattr(value, "id", None)
                    else:
                        record[field] = value
                else:
                    record[field] = value
            record = self.process_complex_fields(record)
            data.append(record)
        return data

    def to_csv(self):
        """Export to CSV with proper UTF-8 encoding."""
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.csv"'
        response.write("\ufeff")  # Добавляем BOM для Excel

        writer = csv.DictWriter(response, fieldnames=self.fields)
        writer.writeheader()
        for row in self.get_data():
            writer.writerow({key: str(value)
                            for key, value in row.items()})  # Приводим к строкам

        return response

    def to_json(self):
        """Export to JSON with proper UTF-8 encoding."""
        response = HttpResponse(content_type="application/json; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.json"'
        json_str = json.dumps(self.get_data(), ensure_ascii=False, indent=4)
        response.write(json_str)
        return response

    def to_xlsx(self):
        """Export to XLSX with UTF-8 encoding."""
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.xlsx"'

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Заголовки
        headers = list(self.fields)
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Данные
        for row_num, row in enumerate(self.get_data(), start=1):
            for col_num, key in enumerate(headers):
                worksheet.write(
                    row_num,
                    col_num,
                    str(row[key]) if row[key] is not None else ""
                )

        workbook.close()
        output.seek(0)
        response.write(output.read())
        return response

    def to_yaml(self):
        """Export to YAML with proper UTF-8 encoding."""
        response = HttpResponse(
            content_type="application/x-yaml; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.yaml"'
        yaml_str = yaml.dump(
            self.get_data(), allow_unicode=True, default_flow_style=False)
        response.write(yaml_str)
        return response

    def to_tsv(self):
        """Export to TSV with UTF-8 encoding."""
        response = HttpResponse(
            content_type="text/tab-separated-values; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.tsv"'
        response.write("\ufeff")  # Добавляем BOM

        writer = csv.DictWriter(
            response, fieldnames=self.fields, delimiter="\t")
        writer.writeheader()
        for row in self.get_data():
            writer.writerow({key: str(value) for key, value in row.items()})

        return response

# The End
