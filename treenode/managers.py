# -*- coding: utf-8 -*-
"""
TreeNode Managers Module

"""

from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Cast, LPad


class TreeNodeQuerySet(models.QuerySet):
    """TreeNode Manager QuerySet Class"""

    def __init__(self, model=None, query=None, using=None, hints=None):
        self.closure_model = model.closure_model
        super().__init__(model, query, using, hints)

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        objs = super().bulk_create(objs, batch_size, ignore_conflicts)

        objs = self.model.closure_model.bulk_create(
            [self.model.closure_model(parent=item, child=item, depth=0)]
            for item in objs
        )

        for node in objs:
            qs = self.model.closure_model.objects.all()
            parents = qs.filter(child=node.tn_parent).values("parent", "depth")
            children = qs.filter(parent=node).values("child", "depth")
            objects = [
                self.model.closure_model(
                    parent_id=p["parent"],
                    child_id=c["child"],
                    depth=p["depth"] + c["depth"] + 1,
                )
                for p in parents
                for c in children
            ]
            node._closure_model.objects.bulk_create(objects)

        self.model._update_orders()
        return objs


class TreeNodeManager(models.Manager):
    """TreeNode Manager Class"""

    def get_queryset(self):
        """
        Forms a QuerySet ordered by the materialized path.
        """

        ClosureModel = self.model.closure_model
        # TODO:add a Mysql compatible and check for db engine to select an appropiate query

        tn_order_subquery = (
            ClosureModel.objects.filter(child=OuterRef("pk"))
            .values("child")
            .annotate(
                tn_order=StringAgg(
                    LPad(Cast("parent__tn_priority", models.TextField()), 6), ""
                )
            )
            .values("tn_order")
        )

        qs = TreeNodeQuerySet(self.model, using=self._db)

        # Retrieve the queryset with the desired ordering
        qs = qs.annotate(tn_order_str=Subquery(tn_order_subquery)).order_by(
            models.expressions.OrderBy(models.F("tn_order_str"), nulls_first=True),
            "id",
        )

        return qs
