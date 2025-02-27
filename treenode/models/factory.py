# -*- coding: utf-8 -*-
"""
TreeNode Factory for Closure Table

This module provides a metaclass `TreeFactory` that automatically binds
a model to a Closure Table for hierarchical data storage.

Features:
- Ensures non-abstract, non-proxy models get a corresponding Closure Table.
- Dynamically creates and assigns a Closure Model for each TreeNodeModel.
- Facilitates the management of hierarchical relationships.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


import sys
from django.db import models
from .closure import ClosureModel


class TreeFactory(models.base.ModelBase):
    """
    Metaclass for binding a model to a Closure Table.

    For each non-abstract, non-proxy, and "top" (without parents) model,
    assigns the `ClosureModel` as the closure table.
    """

    def __init__(cls, name, bases, dct):
        """Class initialization.

        We check that the model:
            - is not abstract
            - is not a proxy
            - is not a child
        and only then assign the ClosureModel.
        """
        super().__init__(name, bases, dct)

        if (cls._meta.abstract or cls._meta.proxy or
                cls._meta.get_parent_list()):
            return

        closure_name = f"{cls._meta.object_name}ClosureModel"
        if getattr(cls, "closure_model", None) is not None:
            return

        fields = {
            "parent": models.ForeignKey(
                cls._meta.model,
                related_name="children_set",
                on_delete=models.CASCADE
            ),

            "child": models.ForeignKey(
                cls._meta.model,
                related_name="parents_set",
                on_delete=models.CASCADE,
            ),

            "node": models.OneToOneField(
                cls._meta.model,
                related_name="tn_closure",
                on_delete=models.CASCADE,
                null=True,
                blank=True,
            ),

            "__module__": cls.__module__
        }

        closure_model = type(closure_name, (ClosureModel,), fields)
        setattr(sys.modules[cls.__module__], closure_name, closure_model)

        cls.closure_model = closure_model


# The End
