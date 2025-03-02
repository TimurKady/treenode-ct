# -*- coding: utf-8 -*-
"""
DB Vendor Utility Module

This module provides a utility function for converting integers
to Base36 string representation.

Features:
- Converts integers into a more compact Base36 format.
- Maintains lexicographic order when padded with leading zeros.
- Supports negative numbers.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import logging
from django.apps import apps
from django.db import connection

from .models import TreeNodeModel

logger = logging.getLogger(__name__)


def create_indexes(model):
    """Create indexes for the descendants of TreeNodeModel."""
    vendor = connection.vendor
    sender = "Django Fast TeeNode"
    table = model._meta.db_table

    with connection.cursor() as cursor:
        if vendor == "postgresql":
            # Если GIN-индекс отсутствует, создаём его
            cursor.execute(
                "SELECT indexname FROM pg_indexes WHERE tablename = %s AND indexname = %s;",
                [table, f"idx_{table}_gin"]
            )
            if not cursor.fetchone():
                cursor.execute(
                    f"CREATE INDEX idx_{table}_gin ON {table} USING gin (id);"
                )
                logger.info(f"{sender}: GIN index for table {table} created.")

            # Если существует первичный ключ, выполняем кластеризацию
            cursor.execute(
                "SELECT relname FROM pg_class WHERE relname = %s;",
                [f"{table}_pkey"]
            )
            if cursor.fetchone():
                cursor.execute(f"CLUSTER {table} USING {table}_pkey;")
                logger.info(f"{sender}: Table {table} is clustered.")

        elif vendor == "mysql":
            cursor.execute("SHOW TABLE STATUS WHERE Name = %s;", [table])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                table_status = dict(zip(columns, row))
                engine = table_status.get("Engine", "").lower()
                if engine != "innodb":
                    cursor.execute(f"ALTER TABLE {table} ENGINE = InnoDB;")
                    logger.info(
                        f"{sender}: Table {table} has been converted to InnoDB."
                    )

        elif vendor in ["microsoft", "oracle"]:
            if vendor == "microsoft":
                cursor.execute(
                    "SELECT name FROM sys.indexes WHERE name = %s AND object_id = OBJECT_ID(%s);",
                    [f"idx_{table}_cluster", table]
                )
            else:
                cursor.execute(
                    "SELECT index_name FROM user_indexes WHERE index_name = %s;",
                    [f"IDX_{table.upper()}_CLUSTER"]
                )
            if not cursor.fetchone():
                cursor.execute(
                    f"CREATE CLUSTERED INDEX idx_{table}_cluster ON {table} (id);")
                logger.info(
                    f"{sender}: CLUSTERED index for table {table} created."
                )

        elif vendor == "sqlite":
            # Kick those on SQLite
            logger.warning(
                f"{sender} Unable to create GIN and CLUSTER indexes for SQLite."
            )
        else:
            logger.warning(
                f"{sender}: Unknown vendor. Index creation cancelled."
            )


def post_migrate_update(sender, **kwargs):
    """Update indexes and tn_closure field only when necessary."""
    # Перебираем все зарегистрированные модели
    for model in apps.get_models():
        # Check that the model inherits from TreeNodeModel and
        # is not abstract
        if issubclass(model, TreeNodeModel) and not model._meta.abstract:
            # Create GIN and CLUSTER indexrs
            create_indexes(model)
            # Get ClosureModel
            closure_model = model.closure_model
            # Check node counts
            al_count = model.objects.exists()
            cl_counts = closure_model.objects.exclude(node=None).exists()

            if al_count and not cl_counts:
                # Call update_tree()
                model.update_tree()


# The End
