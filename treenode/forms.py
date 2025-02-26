"""
TreeNode Form Module.

This module defines the TreeNodeForm class, which dynamically determines
the TreeNode model.
It utilizes TreeWidget and automatically excludes the current node and its
descendants from the parent choices.

Functions:
- __init__: Initializes the form and filters out invalid parent choices.
- factory: Dynamically creates a form class for a given TreeNode model.

Version: 2.0.11
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django import forms
from django.forms.models import ModelChoiceField, ModelChoiceIterator
from django.utils.translation import gettext_lazy as _

from .widgets import TreeWidget


class SortedModelChoiceIterator(ModelChoiceIterator):
    """Iterator Class for ModelChoiceField."""

    def __iter__(self):
        """Return sorted choices based on tn_order."""
        qs_list = list(self.queryset.all())

        # Sort objects
        sorted_objects = self.queryset.model._sort_node_list(qs_list)

        # Iterate yield (value, label) pairs.
        for obj in sorted_objects:
            yield (
                self.field.prepare_value(obj),
                self.field.label_from_instance(obj)
            )


class SortedModelChoiceField(ModelChoiceField):
    """ModelChoiceField Class for tn_paret field."""

    to_field_name = None

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        choices = list(SortedModelChoiceIterator(self))
        if self.empty_label is not None:
            choices.insert(0, ("", self.empty_label))
        return choices

    def _set_choices(self, value):
        self._choices = value

    choices = property(_get_choices, _set_choices)


class TreeNodeForm(forms.ModelForm):
    """
    TreeNode Form Class.

    ModelForm for dynamically determined TreeNode model.
    Uses TreeWidget and excludes self and descendants from the parent choices.
    """

    class Meta:
        """Meta Class."""

        model = None
        fields = "__all__"
        widgets = {
            "tn_parent": TreeWidget()
        }

    def __init__(self, *args, **kwargs):
        """Init Method."""
        super().__init__(*args, **kwargs)

        model = self._meta.model

        if "tn_parent" in self.fields:
            self.fields["tn_parent"].required = False
            self.fields["tn_parent"].empty_label = _("Root")
            queryset = model.objects.all()

            original_field = self.fields["tn_parent"]
            self.fields["tn_parent"] = SortedModelChoiceField(
                queryset=queryset,
                label=original_field.label,
                widget=original_field.widget,
                empty_label=original_field.empty_label,
                required=False
            )
            self.fields["tn_parent"].widget.model = queryset.model

            # Если есть текущее значение, устанавливаем его
            if self.instance and self.instance.pk and self.instance.tn_parent:
                self.fields["tn_parent"].initial = self.instance.tn_parent

    @classmethod
    def factory(cls, model):
        """
        Create a form class dynamically for the given TreeNode model.

        This ensures that the form works with different concrete models.
        """
        class Meta:
            model = model
            fields = "__all__"
            widgets = {
                "tn_parent": TreeWidget(
                    attrs={
                        "data-autocomplete-light": "true",
                        "data-url": "/tree-autocomplete/",
                    }
                )
            }

        return type(f"{model.__name__}Form", (cls,), {"Meta": Meta})


# The End
