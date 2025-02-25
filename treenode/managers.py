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

        Возвращает список узлов, отсортированных от корней к листьям.
        Узел считается корневым, если его tn_parent равен None или его
        родитель отсутствует в node_list.
        """
        visited = set()  # будем хранить id уже обработанных узлов
        result = []
        # Множество id узлов, входящих в исходный список
        node_ids = {node.id for node in node_list}

        def dfs(node):
            if node.id in visited:
                return
            # Если родитель есть и он входит в node_list – обрабатываем его
            # первым
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

        # 1. Топологическая сортировка узлов
        objs = self.sort_nodes(objs)

        # 1. Создаем self-ссылки для всех узлов: (node, node, 0).
        self_links = [
            self.model(parent=obj, child=obj, depth=0, node=obj)
            for obj in objs
        ]
        result.extend(
            super().bulk_create(self_links, batch_size, *args, **kwargs)
        )

        # 2. Формируем отображение: id родителя -> список его детей.
        children_map = defaultdict(list)
        for obj in objs:
            if obj.tn_parent_id:
                children_map[obj.tn_parent_id].append(obj)

        # 3. Пробуем определить корневые узлы (с tn_parent == None).
        root_nodes = [obj for obj in objs if obj.tn_parent is None]

        # Если корневых узлов нет, значит вставляем поддерево.
        if not root_nodes:
            # Определяем "верхние" узлы поддерева:
            # те, чей родитель не входит в список вставляемых объектов.
            objs_ids = {obj.id for obj in objs if obj.id is not None}
            top_nodes = [
                obj for obj in objs if obj.tn_parent_id not in objs_ids
            ]

            # Для каждого такого узла, если родитель существует, получаем
            # записи замыкания для родителя и добавляем новые записи для
            # (ancestor -> node) с depth = ancestor.depth + 1.
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

            # Устанавливаем узлы верхнего уровня поддерева как начальные
            # для обхода.
            current_nodes = top_nodes
        else:
            current_nodes = root_nodes

        # 4. Рекурсивная функция для обхода уровней.
        def process_level(current_nodes):
            next_level = []
            new_entries = []
            for node in current_nodes:
                # Для текущего узла получаем все записи замыкания (его предков).
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

        process_level(current_nodes)
        return result

    @transaction.atomic
    def bulk_update(self, objs, fields=None, batch_size=1000):
        """
        Обновляет таблицу замыкания для объектов, у которых изменился tn_parent.

        Предполагается, что все объекты из списка objs уже есть в таблице
        замыкания, но их связи (как для родителей, так и для детей) могли
        измениться.

        Алгоритм:
        1. Формируем отображение: id родителя → список его детей.
        2. Определяем корневые узлы обновляемого поддерева:
           – Узел считается корневым, если его tn_parent равен None или его
           родитель не входит в objs.
        3. Для каждого корневого узла, если есть внешний родитель, получаем его
           замыкание из базы.
           Затем формируем записи замыкания для узла (все внешние связи с
           увеличенным depth и self-ссылка).
        4. С помощью BFS обходим поддерево: для каждого узла для каждого его
           ребёнка создаём записи, используя родительские записи (увеличенные
           на 1) и добавляем self-ссылку для ребёнка.
        5. Удаляем старые записи замыкания для объектов из objs и сохраняем
           новые пакетно.
        """
        # 1. Топологическая сортировка узлов
        objs = self.sort_nodes(objs)

        # 2. Построим отображение: id родителя → список детей
        children_map = defaultdict(list)
        for obj in objs:
            if obj.tn_parent_id:
                children_map[obj.tn_parent_id].append(obj)

        # Множество id обновляемых объектов
        objs_ids = {obj.id for obj in objs}

        # 3. Определяем корневые узлы обновляемого поддерева:
        # Узел считается корневым, если его tn_parent либо равен None, либо
        # его родитель не входит в objs.
        roots = [
            obj for obj in objs
            if (obj.tn_parent is None) or (obj.tn_parent_id not in objs_ids)
        ]

        # Список для накопления новых записей замыкания
        new_closure_entries = []

        # Очередь для BFS: каждый элемент — кортеж (node, node_closure),
        # где node_closure — список записей замыкания для этого узла.
        queue = deque()
        for node in roots:
            if node.tn_parent_id:
                # Получаем замыкание внешнего родителя из базы
                external_ancestors = list(
                    self.model.objects.filter(child_id=node.tn_parent_id)
                    .values('parent_id', 'depth')
                )
                # Для каждого найденного предка создаём запись для node с
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
            # Добавляем self-ссылку (node → node, depth 0)
            node_closure.append(self.model(parent=node, child=node, depth=0))

            # Сохраняем записи для текущего узла и кладем в очередь для
            # обработки его поддерева
            new_closure_entries.extend(node_closure)
            queue.append((node, node_closure))

        # 4. BFS-обход поддерева: для каждого узла создаём замыкание для его
        # детей
        while queue:
            parent_node, parent_closure = queue.popleft()
            for child in children_map.get(parent_node.id, []):
                # Для ребенка новые записи замыкания:
                # для каждого записи родителя создаем (ancestor -> child)
                # с depth+1
                child_closure = [
                    self.model(
                        parent_id=entry.parent_id,
                        child=child,
                        depth=entry.depth + 1
                    )
                    for entry in parent_closure
                ]
                # Добавляем self-ссылку для ребенка
                child_closure.append(
                    self.model(parent=child, child=child, depth=0)
                )

                new_closure_entries.extend(child_closure)
                queue.append((child, child_closure))

        # 5. Удаляем старые записи замыкания для обновляемых объектов
        self.model.objects.filter(child_id__in=objs_ids).delete()

        # 6. Сохраняем новые записи пакетно
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

    def get_or_create(self, defaults=None, **kwargs):
        """Ensure that the save logic is executed when using get_or_create."""
        defaults = defaults or {}
        created = False

        with transaction.atomic():
            obj = self.filter(**kwargs).first()
            if obj is None:
                params = {k: v for k, v in kwargs.items() if "__" not in k}
                params.update(
                    {k: v() if callable(v) else v for k, v in defaults.items()}
                )
                obj = self.create(**params)
                created = True
        return obj, created

    @transaction.atomic
    def bulk_create(self, objs, batch_size=1000, *args, **kwargs):
        """
        Bulk create.

        Method of bulk creation objects with updating and processing of
        the Closuse Model.
        """
        # 1. Массовая вставка узлов в Модели Смежности
        objs = super().bulk_create(objs, batch_size, *args, **kwargs)

        # 2. Синхронизация Модели Закрытия
        self.closure_model.objects.bulk_create(objs)

        # 3. Очиска кэша и возрат результата
        self.model.clear_cache()
        return objs

    @transaction.atomic
    def bulk_update(self, objs, fields, batch_size=1000, **kwargs):
        """Bulk update."""
        # 1. Выполняем обновление Модели Смежности
        result = super().bulk_update(objs, fields, batch_size, **kwargs)

        # 2. Синхронизируем данные в Модели Закрытия
        if 'tn_parent' in fields:
            # Попросим ClosureModel обработать move
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
                # Получаем максимальный id из таблицы
                cursor.execute(
                    f"SELECT COALESCE(MAX(id), 0) FROM {table_name};"
                )
                max_id = cursor.fetchone()[0]
                next_id = max_id + 1
                # Прямо указываем следующее значение последовательности
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
