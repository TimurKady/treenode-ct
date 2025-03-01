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


def get_database_vendor():
    """Return DB vendors nsme."""
    vendor = connection.vendor
    if vendor == "postgresql":
        vendor_msg = "✔ PostgreSQL"
    elif vendor == "mysql":
        vendor_msg = "✔ MySQL/MariaDB"
    elif vendor in ["microsoft", "oracle"]:
        vendor_msg = "✔ " + vendor.upper()
    elif vendor == "sqlite":
        vendor_msg = "❌ SQLite"
    else:
        vendor_msg = "⚠ Unknown DBMS vendor"
    logger.info(f"Django Fast TeeNode: {vendor_msg} detected.")
    return vendor


def create_indexes(model):
    """Create indexes for all non-abstract descendants of TreeNodeModel."""
    vendor = get_database_vendor()
    sender = "Django Fast TeeNode:"
    info = ""

    with connection.cursor() as cursor:
        # We go through all the models registered in the application
        table = model._meta.db_table
        logger.info(f"{sender} Setting up indexes for a table '{table}'")

        if vendor == "postgresql":
            # Check for the presence of a GIN index
            cursor.execute(
                f"SELECT indexname FROM pg_indexes WHERE tablename = '{table}' AND indexname = 'idx_{table}_gin';"
            )
            if not cursor.fetchone():
                cursor.execute(
                    f"CREATE INDEX idx_{table}_gin ON {table} USING gin (id);"
                )
                info = f"✔ GIN-index for '{table}' is created."
            else:
                info = f"ℹ GIN-index for '{table}' already exist."

            # Primary Key Clustering
            cursor.execute(
                f"SELECT relname FROM pg_class WHERE relname = '{table}_pkey';"
            )
            if cursor.fetchone():
                cursor.execute(f"CLUSTER {table} USING {table}_pkey;")
                info = f"✔ Table '{table}' is clustered."
            else:
                info = f"ℹ Primary key for table '{table}' not found."

        elif vendor == "mysql":
            cursor.execute(f"SHOW TABLE STATUS WHERE Name = '{table}';")
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                table_status = dict(zip(columns, row))
                engine = table_status.get("Engine")
                if engine and engine.lower() != "innodb":
                    cursor.execute(
                        f"ALTER TABLE {table} ENGINE = InnoDB;")
                info = "✔ ENGINE of table '%s' is InnoDB!" % table

        elif vendor in ["microsoft", "oracle"]:
            if vendor == "microsoft":
                cursor.execute(
                    f"SELECT name FROM sys.indexes WHERE name = 'idx_{table}_cluster' AND object_id = OBJECT_ID('{table}');"
                )
            else:
                cursor.execute(
                    f"SELECT index_name FROM user_indexes WHERE index_name = 'IDX_{table.upper()}_CLUSTER'"
                )
            if not cursor.fetchone():
                cursor.execute(
                    f"CREATE CLUSTERED INDEX idx_{table}_cluster ON {table} (id);")
                info = f"✔ Table '{table}' is clustered."
            else:
                info = f"ℹ CLUSTER-index for '{table}' already exist."

        elif vendor == "sqlite":
            # SQLite - the user is an idiot, let him suffer 😆
            info = "❌ SQLite: DB retrievals will be slow. There is no cure!"
        else:
            info = f"❌ Indexes cannot be created for table '{table}'."
    logger.info(f"{sender} {info}")


def post_migrate_update(sender, **kwargs):
    """Update indexes and tn_closure field."""
    for model in apps.get_models():
        # Check that the model inherits from TreeNodeModel and
        # is not abstract
        if issubclass(model, TreeNodeModel) and not model._meta.abstract:
            # Indexes
            create_indexes(model)
            # update gjango-treenode
            closure_model = getattr(model, "closure_model", None)
            if closure_model is None:
                raise AttributeError(
                    f"{model} does not have a closure_model attribute."
                )
            if model.closure_model.objects.only("pk").count() == 0:
                model.update_tree()
            # update django-fast-treenode
            model.update_tree()

# The End

