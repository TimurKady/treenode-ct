# -*- coding: utf-8 -*-
"""

DATACORE ™ 6th Static Normal Form Models
Widgets Module

Author: Timur Kady
Email: kaduevtr@gmail.com

"""
from django import forms


class TreeWidget(forms.Select):

    template_name = "widgets/select2tree.html"
    option_template_name = "widgets/options.html"

    class Media:
        css = {
            "all": (
                "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/css/select2.min.css",
                "select2tree/select2tree.css",
            )
        }
        js = (
            "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/js/select2.min.js",
            "select2tree/select2tree.js",
        )

    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        if value:
            # get icon instance

            item = self.choices.queryset.get(pk=value.value)
            if item.tn_parent:
                option["parent"] = item.tn_parent.id
            else:
                option["parent"] = ""
            option["level"] = item.level
            option["leaf"] = item.is_leaf()
        return option
