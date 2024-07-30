# -*- coding: utf-8 -*-

from django import forms

from .widgets import TreeWidget


class TreeNodeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super(TreeNodeForm, self).__init__(*args, **kwargs)

        if "tn_parent" not in self.fields:
            return
        exclude_pks = []
        obj = self.instance
        if obj.pk:
            exclude_pks += [obj.pk]
            # tn_get_descendants_pks changed to get_descendants_pks()
            # exclude_pks += split_pks(obj.get_descendants_pks())
            exclude_pks += obj.get_descendants_pks()

        # Cheaged to "legal" call
        manager = obj._meta.model.objects

        self.fields["tn_parent"].queryset = manager.prefetch_related(
            "tn_children"
        ).exclude(pk__in=exclude_pks)

    class Meta:
        widgets = {
            "tn_parent": TreeWidget(attrs={"style": "min-width:400px"}),
        }
