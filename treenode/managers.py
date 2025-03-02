# -*- coding: utf-8 -*-
"""
Managers and QuerySets

This module defines custom managers and query sets for the TreeNode model.
It includes optimized bulk operations for handling hierarchical data
using the Closure Table approach.

Features:
- `ClosureQuerySet` and `ClosureModelManager` for managing closure records.
- `TreeNodeQuerySet` and `TreeNodeModelManager` for adjacency model operations.
- Optimized `bulk_create` and `bulk_update` methods with atomic transactions.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from collections import deque, defaultdict
from django.db import models, transaction
from django.db import connection


# ----------------------------------------------------------------------------
# Closere Model
# ----------------------------------------------------------------------------


class ClosureQuerySet(models.QuerySet):
    """QuerySet для ClosureModel."""

    def sort_nodes(self, node_list):
        """
        Sort nodes topologically.

        Returns a list of nodes sorted from roots to leaves.
        A node is considered a root if its tn_parent is None or its
        parent is not in node_list.
        """
        visited = set()  # Will store the ids of already processed nodes
        result = []
        # Set of node ids included in the original list
        node_ids = {node.id for node in node_list}

        def dfs(node):
            if node.id in visited:
                return
            # If there is a parent and it is included in node_list, then
            # process it first
            if node.tn_parent and node.tn_parent_id in node_ids:
                dfs(node.tn_parent)
            visited.add(node.id)
            result.append(node)

        for n in node_list:
            dfs(n)

        return result

    @transaction.atomic
    def bulk_create(self, objs, batch_size=1000, *args, **kwargs):
        """Insert new nodes in bulk."""
        result = []

        # 1. Topological sorting of nodes
        objs = self.sort_nodes(objs)

        # 1. Create self-links for all nodes: (node, node, 0, node).
        self_links = [
            self.model(parent=obj, child=obj, depth=0, node=obj)
            for obj in objs
        ]
        result.extend(
            super().bulk_create(self_links, batch_size, *args, **kwargs)
        )

        # 2. We form a display: parent id -> list of its children.
        children_map = defaultdict(list)
        for obj in objs:
            if obj.tn_parent_id:
                children_map[obj.tn_parent_id].append(obj)

        # 3. We try to determine the root nodes (with tn_parent == None).
        root_nodes = [obj for obj in objs if obj.tn_parent is None]

        # If there are no root nodes, then we insert a subtree.
        if not root_nodes:
            # Define the "top" nodes of the subtree:
            # those whose parent is not included in the list of inserted objects
            objs_ids = {obj.id for obj in objs if obj.id is not None}
            top_nodes = [
                obj for obj in objs if obj.tn_parent_id not in objs_ids
            ]

            # For each such node, if the parent exists, get the closure records
            # for the parent and add new records for (ancestor -> node) with
            # depth = ancestor.depth + 1.
            new_entries = []
            for node in top_nodes:
                if node.tn_parent_id:
                    parent_closures = self.model.objects.filter(
                        child_id=node.tn_parent_id
                    )
                    for ancestor in parent_closures:
                        new_entries.append(
                            self.model(
                                parent=ancestor.parent,
                                child=node,
                                depth=ancestor.depth + 1
                            )
                        )
            if new_entries:
                result.extend(
                    super().bulk_create(
                        new_entries, batch_size, *args, **kwargs
                    )
                )

            # Set the top-level nodes of the subtree as the starting ones for
            # traversal.
            current_nodes = top_nodes
        else:
            current_nodes = root_nodes

        def process_level(current_nodes):
            """Recursive function for traversing levels."""
            next_level = []
            new_entries = []
            for node in current_nodes:
                # For the current node, we get all the closure records
                # (its ancestors).
                ancestors = self.model.objects.filter(child=node)
                for child in children_map.get(node.id, []):
                    for ancestor in ancestors:
                        new_entries.append(
                            self.model(
                                parent=ancestor.parent,
                                child=child,
                                depth=ancestor.depth + 1
                            )
                        )
                    next_level.append(child)
            if new_entries:
                result.extend(
                    super().bulk_create(
                        new_entries, batch_size, *args, **kwargs
                    )
                )
            if next_level:
                process_level(next_level)

        # 4. Run traversing levels.
        process_level(current_nodes)
        return result

    @transaction.atomic
    def bulk_update(self, objs, fields=None, batch_size=1000):
        """
        Update the closure table for objects whose tn_parent has changed.

        It is assumed that all objects from the objs list are already in the
        closure table, but their links (both for parents and for children) may
        have changed.

        Algorithm:
        1. Form a mapping: parent id → list of its children.
        2. Determine the root nodes of the subtree to be updated:
        – A node is considered a root if its tn_parent is None or its
        parent is not in objs.
        3. For each root node, if there is an external parent, get its
        closure from the database.
        Then form closure records for the node (all external links with
        increased depth and self-reference).
        4. Using BFS, traverse the subtree: for each node, for each of its
        children, create records using parent records (increased by 1) and add
        a self-reference for the child.
        5. Remove old closure records for objects from objs and save new ones in
        batches.
        """
        # 1. Topological sorting of nodes
        objs = self.sort_nodes(objs)

        # 2. Let's build a mapping: parent id → list of children
        children_map = defaultdict(list)
        for obj in objs:
            if obj.tn_parent_id:
                children_map[obj.tn_parent_id].append(obj)

        # Set of id's of objects to be updated
        objs_ids = {obj.id for obj in objs}

        # 3. Determine the root nodes of the updated subtree:
        # A node is considered root if its tn_parent is either None or its
        # parent is not in objs.
        roots = [
            obj for obj in objs
            if (obj.tn_parent is None) or (obj.tn_parent_id not in objs_ids)
        ]

        # List for accumulating new closure records
        new_closure_entries = []

        # Queue for BFS: each element is a tuple (node, node_closure), where
        # node_closure is a list of closure entries for that node.
        queue = deque()
        for node in roots:
            if node.tn_parent_id:
                # Get the closure of the external parent from the database
                external_ancestors = list(
                    self.model.objects.filter(child_id=node.tn_parent_id)
                    .values('parent_id', 'depth')
                )
                # For each ancestor found, create an entry for node with
                # depth+1
                node_closure = [
                    self.model(
                        parent_id=entry['parent_id'],
                        child=node,
                        depth=entry['depth'] + 1
                    )
                    for entry in external_ancestors
                ]
            else:
                node_closure = []
            # Add self-reference (node ​​→ node, depth 0)
            node_closure.append(
                self.model(parent=node, child=node, depth=0, node=node)
            )

            # Save records for the current node and put them in a queue for
            # processing its subtree
            new_closure_entries.extend(node_closure)
            queue.append((node, node_closure))

        # 4. BFS subtree traversal: for each node, create a closure for its
        # children
        while queue:
            parent_node, parent_closure = queue.popleft()
            for child in children_map.get(parent_node.id, []):
                # For the child, new closure records:
                # for each parent record, create (ancestor -> child) with
                # depth+1
                child_closure = [
                    self.model(
                        parent_id=entry.parent_id,
                        child=child,
                        depth=entry.depth + 1
                    )
                    for entry in parent_closure
                ]
                # Add a self-link for the child
                child_closure.append(
                    self.model(parent=child, child=child, depth=0)
                )

                new_closure_entries.extend(child_closure)
                queue.append((child, child_closure))

        # 5. Remove old closure records for updatable objects
        self.model.objects.filter(child_id__in=objs_ids).delete()

        # 6. Save new records in batches
        super().bulk_create(new_closure_entries)


class ClosureModelManager(models.Manager):
    """ClosureModel Manager."""

    def get_queryset(self):
        """get_queryset method."""
        return ClosureQuerySet(self.model, using=self._db)

    def bulk_create(self, objs, batch_size=1000):
        """Create objects in bulk."""
        return self.get_queryset().bulk_create(objs, batch_size=batch_size)

    def bulk_update(self, objs, fields=None, batch_size=1000):
        """Move nodes in ClosureModel."""
        return self.get_queryset().bulk_update(
            objs, fields, batch_size=batch_size
        )

# ----------------------------------------------------------------------------
# TreeNode Model
# ----------------------------------------------------------------------------


class TreeNodeQuerySet(models.QuerySet):
    """TreeNodeModel QuerySet."""

    def __init__(self, model=None, query=None, using=None, hints=None):
        """Init."""
        self.closure_model = model.closure_model
        super().__init__(model, query, using, hints)

    def create(self, **kwargs):
        """Ensure that the save logic is executed when using create."""
        obj = self.model(**kwargs)
        obj.save()
        return obj

    @transaction.atomic
    def update(self, **kwargs):
        """Update node."""
        obj = self.filter(**kwargs).first()
        params = {k: v for k, v in kwargs.items() if "__" not in k}
        for key, value in params.items():
            setattr(self, key, value)
        obj.save()
        return obj

    @transaction.atomic
    def get_or_create(self, defaults=None, **kwargs):
        """Ensure that the save logic is executed when using get_or_create."""
        defaults = defaults or {}
        created = False
        obj = self.filter(**kwargs).first()
        if obj is None:
            params = {k: v for k, v in kwargs.items() if "__" not in k}
            params.update(
                {k: v() if callable(v) else v for k, v in defaults.items()}
            )
            obj = self.create(**params)
            created = True
        return obj, created

    def update_or_create(self, defaults=None, create_defaults=None, **kwargs):
        """Update or creat."""
        defaults = defaults or {}
        create_defaults = create_defaults or {}

        with transaction.atomic():
            obj = self.filter(**kwargs).first()
            params = {k: v for k, v in kwargs.items() if "__" not in k}
            if obj is None:
                params.update({
                    k: v()
                    if callable(v) else v
                    for k, v in create_defaults.items()
                })
                obj = self.create(**params)  # Create and save
                created = True
            else:
                params.update({
                    k: v()
                    if callable(v) else v
                    for k, v in defaults.items()
                })
                obj = obj.update(**params)  # Update and save
        return obj, created

    @transaction.atomic
    def bulk_create(self, objs, batch_size=1000, *args, **kwargs):
        """
        Bulk create.

        Method of bulk creation objects with updating and processing of
        the Closuse Model.
        """
        # 1. Bulk Insertion of Nodes in Adjacency Models
        objs = super().bulk_create(objs, batch_size, *args, **kwargs)
        # 2. Synchronization of the Closing Model
        self.closure_model.objects.bulk_create(objs)
        # 3. Clear cache and return result
        self.model.clear_cache()
        return objs

    @transaction.atomic
    def bulk_update(self, objs, fields, batch_size=1000, **kwargs):
        """Bulk update."""
        # 1. Perform an Adjacency Model Update
        result = super().bulk_update(objs, fields, batch_size, **kwargs)
        # 2. Synchronize data in the Closing Model
        if 'tn_parent' in fields:
            # Let's ask ClosureModel to handle move
            self.closure_model.objects.bulk_update(
                objs, ["tn_parent",], batch_size
            )
        return result


class TreeNodeModelManager(models.Manager):
    """TreeNodeModel Manager."""

    def bulk_create(self, objs, batch_size=1000, ignore_conflicts=False):
        """
        Bulk Create.

        Override bulk_create for the adjacency model.
        Here we first clear the cache, then delegate the creation via our
        custom QuerySet.
        """
        self.model.clear_cache()
        result = self.get_queryset().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts
        )
        transaction.on_commit(lambda: self._update_auto_increment())
        return result

    def bulk_update(self, objs, fields=None, batch_size=1000):
        """Bulk Update."""
        self.model.clear_cache()
        result = self.get_queryset().bulk_update(objs, fields, batch_size)
        return result

    def get_queryset(self):
        """Return a sorted QuerySet."""
        queryset = TreeNodeQuerySet(self.model, using=self._db)\
            .select_related("tn_closure")\
            .annotate(depth=models.Max("parents_set__depth"))\
            .order_by("depth", "tn_parent", "tn_priority")
        return queryset

    # Service methods -------------------

    def _bulk_update_tn_closure(self, objs, fields=None, batch_size=1000):
        """Update tn_closure in bulk."""
        self.model.clear_cache()
        super().bulk_update(objs, fields, batch_size)

    def _get_auto_increment_sequence(self):
        """Get auto increment sequence."""
        table_name = self.model._meta.db_table
        pk_column = self.model._meta.pk.column
        with connection.cursor() as cursor:
            query = "SELECT pg_get_serial_sequence(%s, %s)"
            cursor.execute(query, [table_name, pk_column])
            result = cursor.fetchone()
        return result[0] if result else None

    def _update_auto_increment(self):
        """Update auto increment."""
        table_name = self.model._meta.db_table
        with connection.cursor() as cursor:
            db_engine = connection.vendor

            if db_engine == "postgresql":
                sequence_name = self._get_auto_increment_sequence()
                # Get the max id from the table
                cursor.execute(
                    f"SELECT COALESCE(MAX(id), 0) FROM {table_name};"
                )
                max_id = cursor.fetchone()[0]
                next_id = max_id + 1
                # Directly specify the next value of the sequence
                cursor.execute(
                    f"ALTER SEQUENCE {sequence_name} RESTART WITH {next_id};"
                )
            elif db_engine == "mysql":
                cursor.execute(f"SELECT MAX(id) FROM {table_name};")
                max_id = cursor.fetchone()[0] or 0
                next_id = max_id + 1
                cursor.execute(
                    f"ALTER TABLE {table_name} AUTO_INCREMENT = {next_id};"
                )
            elif db_engine == "sqlite":
                cursor.execute(
                    f"UPDATE sqlite_sequence SET seq = (SELECT MAX(id) \
FROM {table_name}) WHERE name='{table_name}';"
                )
            elif db_engine == "mssql":
                cursor.execute(f"SELECT MAX(id) FROM {table_name};")
                max_id = cursor.fetchone()[0] or 0
                cursor.execute(
                    f"DBCC CHECKIDENT ('{table_name}', RESEED, {max_id});"
                )
            else:
                raise NotImplementedError(
                    f"Autoincrement for {db_engine} is not supported."
                )

# The End
