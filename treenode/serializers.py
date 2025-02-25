# -*- coding: utf-8 -*-
"""
Treenode serialization Module

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import datetime
import decimal
import uuid
from django.db import models


class TreenodeSerializer:
    """
    Treenode serialization class.

    Serializes a node including ManyToMany relationships.
    """

    def serialize_node(self, node):
        """Serialize a node."""
        data = {}
        for field in node._meta.get_fields():
            field_name = field.name
            value = getattr(node, field_name)

            if isinstance(field, models.ForeignKey):
                data[field_name] = getattr(node, field_name + "_id", None)
            elif isinstance(field, models.ManyToManyField):
                data[field_name] = list(value.values_list("id", flat=True))
            elif isinstance(value, (
                    datetime.date,
                    datetime.datetime,
                    uuid.UUID,
                    decimal.Decimal)):
                data[field_name] = str(value)
            else:
                data[field_name] = value
        return data
