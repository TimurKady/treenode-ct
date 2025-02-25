# -*- coding: utf-8 -*-
"""
TreeNode Application Configuration

This module defines the application configuration for the TreeNode app.
It sets the default auto field and specifies the app's name.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


import logging
from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .utils.db import post_migrate_update

logger = logging.getLogger(__name__)


class TreeNodeConfig(AppConfig):
    """TreeNodeConfig Class."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "treenode"

    def ready(self):
        """
        Attach a post_migrate handler.

        This allows you to perform operations after the migration is complete.
        """
        post_migrate.connect(post_migrate_update, sender=self)
