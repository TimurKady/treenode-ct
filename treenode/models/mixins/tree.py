# -*- coding: utf-8 -*-
"""
TreeNode Tree Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import json
from django.db import models, transaction
from collections import OrderedDict
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.json import DjangoJSONDecoder

from ...cache import cached_method
from ...utils.base32 import to_base32


class TreeNodeTreeMixin(models.Model):
    """TreeNode Tree Mixin."""

    @classmethod
    def dump_tree(cls, instance=None):
        """
        Return an n-dimensional dictionary representing the model tree.

        Introduced for compatibility with other packages.
        """
        return cls.get_tree(cls, instance)

    @classmethod
    @cached_method
    def get_tree(cls, instance=None):
        """
        Return an n-dimensional dictionary representing the model tree.

        If instance is passed, returns a subtree rooted at instance (using
        get_descendants_queryset), if not passed, builds a tree for all nodes
        (loads all records in one query).
        """
        # If instance is passed, we get all its descendants (including itself)
        if instance:
            queryset = instance.get_descendants_queryset(include_self=True)
        else:
            # Load all records at once
            queryset = cls.objects.all()

        # Dictionary for quick access to nodes by id and list for iteration
        nodes_by_id = {}
        nodes_list = []

        # Loop through all nodes using an iterator
        for node in queryset.iterator(chunk_size=1000):
            # Create a dictionary for the node.
            # In Python 3.7+, the standard dict preserves insertion order.
            # We'll stick to the order:
            # id, 'tn_parent', 'tn_priority', 'level', then the rest of
            # the fields. Сlose the dictionary with the fields 'level', 'path',
            # 'children'
            node_dict = OrderedDict()
            node_dict['id'] = node.id
            node_dict['tn_parent'] = node.tn_parent_id
            node_dict['tn_priority'] = node.tn_priority
            node_dict['level'] = node.depth
            node_dict['path'] = node.get_breadcrumbs('tn_priority')

            # Добавляем остальные поля модели.
            # Перебираем все поля, полученные через _meta.get_fields()
            for field in node._meta.get_fields():
                # Пропускаем поля, которые уже добавлены или не требуются
                # (например, связь tn_closure или виртуальные связи)
                if field.name in [
                        'id', 'tn_parent', 'tn_priority', 'tn_closure',
                        'children']:
                    continue

                try:
                    value = getattr(node, field.name)
                except Exception:
                    value = None

                # Если поле представляет собой many-to-many – получаем
                # список идентификаторов связанных объектов
                if hasattr(value, 'all'):
                    value = list(value.all().values_list('id', flat=True))

                node_dict[field.name] = value

            # Adding a materialized path
            node_dict['path'] = None
            # Adding a nesting level
            node_dict['level'] = None
            # We initialize the list of children, which we will then fill
            # when assembling the tree
            node_dict['children'] = []

            # Save the node both in the list and in the dictionary by id
            # for quick access
            nodes_by_id[node.id] = node_dict
            nodes_list.append(node_dict)

        # Build a tree: assign each node a list of its children
        tree = []
        for node_dict in nodes_list:
            parent_id = node_dict['tn_parent']
            # If there is a parent and it is present in nodes_by_id, then
            # add the current node to the list of its children
            if parent_id and parent_id in nodes_by_id:
                parent_node = nodes_by_id[parent_id]
                parent_node['children'].append(node_dict)
            else:
                # If there is no parent, this is the root node of the tree
                tree.append(node_dict)

        return tree

    @classmethod
    def get_tree_json(cls, instance=None):
        """Represent the tree as a JSON-compatible string."""
        tree = cls.dump_tree(instance)
        return DjangoJSONEncoder().encode(tree)

    @classmethod
    def load_tree(cls, tree_data):
        """
        Load a tree from a list of dictionaries.

        Loaded nodes are synchronized with the database: existing records
        are updated, new ones are created.
        Each dictionary must contain the 'id' key to identify the record.
        """

        def flatten_tree(nodes, model_fields):
            """
            Recursively traverse the tree and generate lists of nodes.

            Each node in the list is a copy of the dictionary without
            the service keys 'children', 'level', 'path'.
            """
            flat = []
            for node in nodes:
                # Create a copy of the dictionary so as not to affect
                # the original tree
                node_copy = node.copy()
                children = node_copy.pop('children', [])
                # Remove temporary/service fields that are not related to
                # the model
                for key in list(node_copy.keys() - model_fields):
                    del node_copy[key]
                flat.append(node_copy)
                # Recursively add all children
                flat.extend(flatten_tree(children, model_fields))
            return flat

        # Get a flat list of nodes (from root to leaf)
        model_fields = [field.name for field in cls._meta.get_fields()]
        flat_nodes = flatten_tree(tree_data, model_fields)

        # Load all ids for a given model from the database to minimize
        # the number of database requests
        existing_ids = set(cls.objects.values_list('id', flat=True))

        # Lists for nodes to update and create
        nodes_to_update = []
        nodes_to_create = []

        # Determine which model fields should be updated (excluding 'id')
        # This assumes that all model fields are used in serialization
        # (excluding service ones, like children)
        field_names = model_fields.remove('id')

        # Iterate over each node from the flat list
        for node_data in flat_nodes:
            # Collect data for creation/update.
            # There is already an 'id' in node_data, so we can distinguish
            # an existing entry from a new one.
            data = {k: v for k, v in node_data.items()
                    if k in field_names or k == 'id'}

            # Handle the foreign key tn_parent.
            # If the value is None, then there is no parent, otherwise
            # the parent id is expected.
            # Additional checks can be added here if needed.
            if 'tn_parent' in data and data['tn_parent'] is None:
                data['tn_parent'] = None

            # Если id уже есть в базе, то будем обновлять запись,
            # иначе создаем новую.
            if data['id'] in existing_ids:
                nodes_to_update.append(cls(**data))
            else:
                nodes_to_create.append(cls(**data))

        # Perform operations in a transaction to ensure data integrity.
        with transaction.atomic():
            # bulk_create – creating new nodes
            if nodes_to_create:
                cls.objects.bulk_create(nodes_to_create, batch_size=1000)
            # bulk_update – updating existing nodes.
            # When bulk_update, we must specify a list of fields to update.
            if nodes_to_update:
                cls.objects.bulk_update(
                    nodes_to_update,
                    fields=field_names,
                    batch_size=1000
                )
        cls.clear_cache()

    @classmethod
    def load_tree_json(cls, json_str):
        """
        Decode a JSON string into a dictionary.

        Takes a JSON-compatible string and decodes it into a tree structure.
        """
        try:
            # Decode JSON string with DjangoJSONDecoder to handle dates
            # and other things correctly
            tree_data = json.loads(json_str, cls=DjangoJSONDecoder)
        except Exception as e:
            raise ValueError(f"Error decoding JSON: {e}")

        # Additional tree_data validation may be added here in future versions.

        # Call a method that takes a tree as a list of dictionaries and
        # performs the update and creation.
        cls.load_tree(tree_data)

    @classmethod
    @cached_method
    def get_tree_display(cls, symbol="&mdash;"):
        """Get a multiline string representing the model tree."""
        # Load the tree with the required preloads and depth annotation.
        queryset = cls.objects.all()\
            .prefetch_related("tn_children")\
            .annotate(depth=models.Max("parents_set__depth"))\
            .order_by("depth", "tn_parent", "tn_priority")
        # Convert queryset to list for indexed access
        nodes = list(queryset)
        sorted_nodes = cls._sort_node_list(nodes)
        result = []
        for node in sorted_nodes:
            # Insert an indent proportional to the depth of the node
            indent = symbol * node.depth
            result.append(indent + str(node))
        return result

    @classmethod
    @cached_method
    def get_tree_annotated(cls):
        """
        Get an annotated list from a tree branch.

        Something like this will be returned:
        [
            (a,     {'open':True,  'close':[],    'level': 0})
            (ab,    {'open':True,  'close':[],    'level': 1})
            (aba,   {'open':True,  'close':[],    'level': 2})
            (abb,   {'open':False, 'close':[],    'level': 2})
            (abc,   {'open':False, 'close':[0,1], 'level': 2})
            (ac,    {'open':False, 'close':[0],   'level': 1})
        ]

        All nodes are ordered by materialized path.
        This can be used with a template like this:

        {% for item, info in annotated_list %}
            {% if info.open %}
                <ul><li>
            {% else %}
                </li><li>
            {% endif %}

            {{ item }}

            {% for close in info.close %}
                </li></ul>
            {% endfor %}
        {% endfor %}

        """
        # Load the tree with the required preloads and depth annotation.
        queryset = cls.objects.all()\
            .prefetch_related("tn_children")\
            .annotate(depth=models.Max("parents_set__depth"))\
            .order_by("depth", "tn_parent", "tn_priority")
        # Convert queryset to list for indexed access
        nodes = list(queryset)
        total_nodes = len(nodes)
        sorted_nodes = cls._sort_node_list(nodes)

        result = []

        for i, node in enumerate(sorted_nodes):
            # Get the value to display the node
            value = str(node)
            # Determine if there are descendants (use prefetch_related to avoid
            # additional queries)
            value_open = len(node.tn_children.all()) > 0
            level = node.depth

            # Calculate the "close" field
            if i + 1 < total_nodes:
                next_node = nodes[i + 1]
                depth_diff = level - next_node.depth
                # If the next node is at a lower level, then some open
                # levels need to be closed
                value_close = list(range(next_node.depth, level)
                                   ) if depth_diff > 0 else []
            else:
                # For the last node, close all open levels
                value_close = list(range(0, level + 1))

            result.append(
                (value, {
                    "open": value_open,
                    "close": value_close,
                    "level": level
                })
            )
        return result

    @classmethod
    @transaction.atomic
    def update_tree(cls):
        """Rebuilds the closure table."""
        # Clear cache
        cls.clear_cache()
        cls.closure_model.delete_all()
        objs = list(cls.objects.all())
        cls.closure_model.objects.bulk_create(objs, batch_size=1000)

    @classmethod
    def delete_tree(cls):
        """Delete the whole tree for the current node class."""
        cls.clear_cache()
        cls.objects.all().delete()

    @classmethod
    def _sort_node_list(cls, nodes):
        """
        Sort list of nodes by materialized path oreder.

        Collect the materialized path without accessing the DB and perform
        sorting
        """
        # Create a list of tuples: (node, materialized_path)
        nodes_with_path = [(node, node.tn_order) for node in nodes]
        # Sort the list by the materialized path
        nodes_with_path.sort(key=lambda tup: tup[1])
        # Extract sorted nodes
        return [tup[0] for tup in nodes_with_path]

# The end
