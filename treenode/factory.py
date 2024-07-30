# -*- coding: utf-8 -*-
"""
Model Factory Module

"""

import sys

from django.db import models
from django.db.models.base import ModelBase


class TreeFactory(ModelBase):
    """Metaclass for creating a Closure Table"""

    def __init__(cls, name, bases, dct):
        """Init"""

        super().__init__(name, bases, dct)

        if not (cls._meta.get_parent_list() or cls._meta.abstract):
            from django.apps import apps

            app_name = apps.get_app_config(app_label=cls._meta.app_label).name

            setattr(
                sys.modules[app_name],
                "%sClosureModel" % cls._meta.object_name,
                cls.create_closure_model(),
            )

    def create_closure_model(cls):
        """
        Creates a <Model>ClosureModel model in the same module as the model.
        """

        if hasattr(cls, "closure_model") and cls.closure_model is not None:
            return cls.closure_model

        model_name = "%sClosureModel" % cls._meta.object_name

        meta_dict = dict(
            app_label=cls._meta.app_label,
           
        default_permissions = (),
            unique_together=(
                (
                    "parent",
                    "child",
                ),
            ),
            indexes=[
                models.Index(fields=["parent", "child"]),
                models.Index(fields=["parent"]),
                models.Index(fields=["child"]),
            ],
        )

        fields = dict(
            parent=models.ForeignKey(
                cls._meta.object_name,
                on_delete=models.CASCADE,
                related_name="children_set",
            ),
            child=models.ForeignKey(
                cls._meta.object_name,
                on_delete=models.CASCADE,
                related_name="parents_set",
            ),
            depth=models.IntegerField(),
            __module__=cls._meta.app_label,
            Meta=type("Meta", (object,), meta_dict),
        )

        model = type(model_name, (models.Model,), fields)

        setattr(cls, "closure_model", model)
        return model
