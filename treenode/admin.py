# -*- coding: utf-8 -*-
"""
TreeNode Admin Module

"""

from typing import Any

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models import Max, OuterRef, Subquery
from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.safestring import mark_safe

from .forms import TreeNodeForm


class NoPkDescOrderedChangeList(ChangeList):
    def get_ordering(self, request, queryset):
        rv = super().get_ordering(request, queryset)
        rv = list(rv)
        rv.remove("-pk") if "-pk" in rv else None
        return tuple()

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)

        ClosureModel = self.model.closure_model

        max_depth_subquery = (
            ClosureModel.objects.filter(parent=OuterRef("pk"))
            .values("parent")
            .annotate(max_depth=Max("depth"))
            .values("max_depth")
        )

        max_level_subquery = (
            ClosureModel.objects.filter(child=OuterRef("pk"))
            .values("child")
            .annotate(max_depth=Max("depth"))
            .values("max_depth")
        )

        # Annotating the original queryset where `tn_depth` and `tn_level`
        # are to be used in _get_treenode_field_display_with_accordion
        # instead of accessing level and depth instance methods
        qs = qs.annotate(
            tn_depth=Subquery(max_depth_subquery), tn_level=Subquery(max_level_subquery)
        ).select_related("tn_parent")

        return qs


class TreeNodeModelAdmin(admin.ModelAdmin):

    TREENODE_DISPLAY_MODE_ACCORDION = "accordion"
    TREENODE_DISPLAY_MODE_BREADCRUMBS = "breadcrumbs"
    TREENODE_DISPLAY_MODE_INDENTATION = "indentation"

    treenode_display_mode = TREENODE_DISPLAY_MODE_INDENTATION

    form = TreeNodeForm
    list_per_page = 1000

    def get_list_display(self, request):
        base_list_display = super(TreeNodeModelAdmin, self).get_list_display(request)
        base_list_display = list(base_list_display)

        def treenode_field_display(obj):
            return self._get_treenode_field_display(request, obj)

        treenode_field_display.short_description = self.model._meta.verbose_name
        treenode_field_display.allow_tags = True

        if len(base_list_display) == 1 and base_list_display[0] == "__str__":
            return (treenode_field_display,)
        else:
            treenode_display_field = getattr(self.model, "treenode_display_field")
            if (
                len(base_list_display) >= 1
                and base_list_display[0] == treenode_display_field
            ):
                base_list_display.pop(0)
            return (treenode_field_display,) + tuple(base_list_display)

        return base_list_display  # unreachaable code to be removed

    def get_changelist(self, request):
        return NoPkDescOrderedChangeList

    def get_ordering(self, request):
        return None

    def list_to_queryset(self, model, data):

        if not isinstance(model, ModelBase):
            raise ValueError("%s must be Model" % model)
        if not isinstance(data, list):
            raise ValueError("%s must be List Object" % data)

        pk_list = [obj.pk for obj in data]
        return model.objects.filter(pk__in=pk_list)

    def _use_treenode_display_mode(self, request, obj):
        querystring = request.GET.urlencode() or ""
        return len(querystring) <= 2

    def _get_treenode_display_mode(self, request, obj):
        return self.treenode_display_mode

    def _get_treenode_field_default_display(self, obj):
        return self._get_treenode_field_display_with_breadcrumbs(obj)

    def _get_treenode_field_display(self, request, obj):
        if not self._use_treenode_display_mode(request, obj):
            return self._get_treenode_field_default_display(obj)
        display_mode = self._get_treenode_display_mode(request, obj)
        if display_mode == TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_ACCORDION:
            return self._get_treenode_field_display_with_accordion(obj)
        elif display_mode == TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_BREADCRUMBS:
            return self._get_treenode_field_display_with_breadcrumbs(obj)
        elif display_mode == TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_INDENTATION:
            return self._get_treenode_field_display_with_indentation(obj)
        else:
            return self._get_treenode_field_default_display(obj)

    def _get_treenode_field_display_with_accordion(self, obj):
        tn_namespace = "%s.%s" % (
            obj.__module__,
            obj.__class__.__name__,
        )
        tn_namespace_key = tn_namespace.lower().replace(".", "_")
        return mark_safe(
            ""
            '<span class="treenode"'
            ' data-treenode-type="%s"'
            ' data-treenode-pk="%s"'
            ' data-treenode-accordion="1"'
            ' data-treenode-depth="%s"'
            ' data-treenode-level="%s"'
            ' data-treenode-parent="%s">%s</span>'
            % (
                tn_namespace_key,
                str(obj.pk),
                # tn_depth and tn_level are obtained from  annotation on ChangeList.get_queryset
                str(obj.tn_depth),
                str(obj.tn_level),
                str(obj.tn_parent_id or ""),
                obj.get_display(indent=False),
            )
        )

    def _get_treenode_field_display_with_breadcrumbs(self, obj):
        obj_display = ""
        for obj_ancestor in obj.get_ancestors():
            obj_ancestor_display = obj_ancestor.get_display(indent=False)
            obj_display += '<span class="treenode-breadcrumbs">%s</span>' % (
                obj_ancestor_display,
            )
        obj_display += obj.get_display(indent=False)
        return mark_safe('<span class="treenode">%s</span>' % (obj_display,))

    def _get_treenode_field_display_with_indentation(self, obj):
        obj_display = (
            '<span class="treenode-indentation">&mdash;</span>' * obj.ancestors_count
        )
        obj_display += obj.get_display(indent=False)
        return mark_safe('<span class="treenode">%s</span>' % (obj_display,))

    class Media:
        css = {"all": ("treenode/css/treenode.css",)}
        js = ["treenode/js/treenode.js"]
