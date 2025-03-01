## API Reference

### Overview
The `django-fast-treenode` package provides a **comprehensive set of methods and properties** for working with hierarchical data structures in Django. These methods are designed to simplify tree management, optimize performance, and facilitate migration from other tree-based Django packages.

The API is divided into several logical groups, each serving a specific purpose:

- **[TreeNodeModel Methods](#treenodemodel-methods)** – Core methods for managing tree nodes, including saving, deleting, and caching.
- **[Ancestor Methods](#ancestor-methods)** – Retrieve and manipulate ancestor nodes.
- **[Children Methods](#children-methods)** – Manage direct child nodes efficiently.
- **[Descendant Methods](#descendant-methods)** – Work with entire subtrees of nodes.
- **[Family Methods](#family-methods)** – Retrieve and analyze relationships within a node's family (ancestors, siblings, descendants).
- **[Node Utility Methods](#node-utility-methods)** – Additional methods for retrieving node order, paths, levels, and priorities.
- **[Root Node Methods](#root-node-methods)** – Manage and retrieve root nodes of trees.
- **[Sibling Methods](#sibling-methods)** – Handle relationships between sibling nodes.
- **[Tree Methods](#tree-methods)** – Serialize and manipulate the entire tree structure, including JSON export/import.
- **[Logical Methods](#logical-methods)** – Determine relationships between nodes (e.g., is ancestor, is sibling, is leaf).
- **[Property Accessors](#property-accessors)** – Shortcut properties for commonly used methods like `parent`, `children`, `siblings`, `depth`, and `priority`.

Each section below briefly describes the purpose of the respective method group.

---

### TreeNodeModel Methods
These methods handle the basic operations of the tree structure. They ensure that the data in the Adjacency Table and the Closure Table are synchronized. This section covers:

- Clearing the model cache.
- Deleting a node with different strategies.
- Saving a node while maintaining tree integrity.

#### clear_cache(cls):
A class method that **invalidates** (clears) the cache for a given model only.
```python
cls.clear_cache()
```
For more information on caching, see [Caching and Cache Management](cache.md)


#### delete
**Delete a node** provides two deletion strategies:
- **Cascade Delete (`cascade=True`)**: Removes the node along with all its descendants.
- **Reparenting (`cascade=False`)**: Moves the children of the deleted node up one level in the hierarchy before removing the node itself.

```python
obj.delete(cascade=True)   # Deletes node and all its descendants
obj.delete(cascade=False)  # Moves children up and then deletes the node
```
This ensures greater flexibility in managing tree structures while preventing orphaned nodes.


#### save
**Save a node** with Adjacency Sheet and Closure Tablet synchronizations.

```python
obj.save()
```

---

### Ancestor Methods
These methods allow retrieving **all ancestor nodes**, ordered from root to parent. They provide filtering options by depth, retrieval of primary keys for optimized queries, and counting functionality for analysis.

#### get_ancestors_queryset
Returns the **ancestors queryset** (ordered from parent to root):
```python
obj.get_ancestors_queryset(include_self=True, depth=None)
```

#### get_ancestors_pks
Returns the **ancestors pks** list:
```python
obj.get_ancestors_pks(include_self=True, depth=None)
```

#### get_ancestors
Returns a **list with all ancestors** (ordered from root to parent):
```python
obj.get_ancestors(include_self=True, depth=None)
```

#### get_ancestors_count
Returns the **ancestors count**:
```python
obj.get_ancestors_count(include_self=True, depth=None)
```

---

### Children Methods
These methods are designed to manage **direct child nodes** within the tree structure. They allow retrieving child nodes, counting them, and adding new children in a specific order (`first-child`, `last-child`, etc.).

#### add_child
```python
obj.add_child(position=None, **kwargs)
```
`position` specifies the order position of the object being added in the list of children of this node. It can be `'first-child'`, `'last-child'`, `'sorted-child'`, or an integer value.
The `**kwargs` parameters contain the object creation data that will be passed to the inherited node model. Instead of passing the object creation data, you can pass an already created (but not yet saved) model instance to insert into the tree using the `instance` keyword.

```python
obj.add_child(potision='first-child', instance=node)
```

The method returns the created node object. It will be saved by this method.

#### get_children_queryset
Returns the **children queryset**:
```python
obj.get_children_queryset()
```

#### get_children_pks
Returns the **children pks** list:
```python
obj.get_children_pks()
```

#### get_children
Returns a **list containing all children**:
```python
obj.get_children()
```

#### get_children_count
Returns the **children count**:
```python
obj.get_children_count()
```

#### get_first_child
Returns the **first child node** or `None` if it has no children:
```python
obj.get_first_child()
```

#### get_last_child
Returns the **last child node** or `None` if it has no children:
```python
obj.get_last_child()
```

---

### Descendant Methods
These methods enable working with **entire subtrees**. You can retrieve all descendants, filter by depth, count them, and fetch their primary keys for optimized queries.

#### get_descendants_queryset
Returns the **descendants queryset**:
```python
obj.get_descendants_queryset(include_self=False, depth=None)
```

#### get_descendants
Returns a **list containing all descendants**:
```python
obj.get_descendants(include_self=False, depth=None)
```

#### get_descendants_count
Returns the **descendants count**:
```python
obj.get_descendants_count(include_self=False, depth=None)
```

#### get_descendants_pks
Returns the **descendants pks** list:
```python
obj.get_descendants_pks(include_self=False, depth=None)
```

---

### Family Methods
These methods provide a comprehensive way to retrieve all related nodes within a tree, including ancestors, descendants, and siblings. They help analyze relationships while maintaining the correct tree order.

#### get_family_queryset
Returns a QuerySet containing the ancestors, itself and the descendants,  in tree order.
```python
obj.get_family_queryset()
```

#### get_family_pks
Returns a pk-list containing the ancestors, the model itself and the descendants, in tree order:
```python
obj.get_family_pks()
```

#### get_family
Returns a list containing the ancestors, the model itself and the descendants, in tree order:
```python
obj.get_family()
```

#### get_family_count
Return number of nodes in family:
```python
obj.get_family()
```

---

### Node Utility Methods
This set of methods helps manage node-related operations such as:

- **Breadcrumbs generation**
- **Depth, index, and level calculations**
- **Materialized path retrieval for sorting**
- **Dynamic node positioning within the tree** 

#### get_breadcrumbs
Returns the **breadcrumbs** to current node (included):
```python
obj.get_breadcrumbs(attr=None)
```

If `attr` is not specified, the method will return a list of pks ancestors, including itself.

#### get_depth
Returns the **node depth** (how deep is this level from the root of the tree; starting from 0):
```python
obj.get_depth()
```

#### get_level
Returns the **node level** (starting from 1):
```python
obj.get_level()
```

#### get_order
Returns the **order value** used for ordering:
```python
obj.get_order()
```

#### get_index
Returns the **node index** (index in children list):
```python
obj.get_index()
```

#### insert_at
Insert a node into the tree relative to the target node.

```python
obj.insert_at(target, position='first-child', save=False)
```

Parameters:
- `target`: еhe target node relative to which this node will be placed.
- `position`: the position, relative to the target node, where the current node object will be moved to, can be one of:
  - `first-root`: the node will be the first root node;
  - `last-root`: the node will be the last root node;
  - `sorted-root`: the new node will be moved after sorting by the treenode_sort_field field;
  - `first-sibling`: the node will be the new leftmost sibling of the target node;
  - `left-sibling`: the node will take the target node’s place, which will be moved to the target position with shifting follows nodes;
  - `right-sibling`: the node will be moved to the position after the target node;
  - `last-sibling`: the node will be the new rightmost sibling of the target node;
  - `sorted-sibling`: the new node will be moved after sorting by the treenode_sort_field field;
  - first-child: the node will be the first child of the target node;
  - last-child: the node will be the new rightmost child of the target
  - sorted-child: the new node will be moved after sorting by the treenode_sort_field field.
- `save` : if `save=true`, the node will be saved in the tree. Otherwise,  the method will return a model instance with updated fields: parent field and position in sibling list.

Before using this method, the model instance must be correctly created with all required fields defined. If the model has required fields, then simply creating an object and calling insert_at() will not work, because Django will raise an exception.

#### move_to
Moves the model instance relative to the target node and sets its position (if necessary).
```python
obj.move_to(target, position=0)
```
Parameters:
- `target`: еhe target node relative to which this node will be placed.
- `position` – the position, relative to the target node, where the current node object will be moved to. For detals see [insert_at](#insert_at) method.

#### get_path
Returns Materialized Path of node. The materialized path is constructed by recording the position of each node within its parent's list of children, tracing this sequence back through all its ancestors.
```python
obj.get_path(prefix='', suffix='', delimiter='.', format_str='')
```

#### get_parent
Returns the parent node.
```python
obj.get_parent()
```

#### set_parent
Sets the parent node.
```python
obj.set_parent(parent_obj)
```

#### get_parent_pk
Returns the parent node pk.
```python
obj.get_parent_pk()
```

#### get_priority
Returns the ordinal position of a node in its parent's list.
```python
obj.get_priority()
```

#### set_priority
Sets the ordinal position of a node in its parent's list. Takes an integer value as the `priority` parameter.
```python
obj.set_priority(priority=0)
```

If the `priority` value is found to be greater than the number of siblings, the node will be placed last in the list.

#### get_root
Returns the root node for the current node.
```python
obj.get_root()
```

#### get_root_pk
Returns the root node pk for the current node.
```python
obj.get_root_pk()
```

---

### Root Node Methods
These methods allow managing **root nodes** efficiently. They provide retrieval, counting, and manipulation of the first and last root nodes in the tree.

#### add_root
Adds a root node to the tree.
```python
cls.add_root(position=None, **kwargs)
```

Adds a new root node at the specified position. If no position is specified, the new node will be the last element in the root.

`position` specifies the order position of the object being added in the list of children of this node. It can be `'first-root'`, `'last-root'`, `'sorted-root'`, or an integer value.

The `**kwargs` parameters contain the object creation data that will be passed to the inherited node model. Instead of passing the object creation data, you can pass an already created (but not yet saved) model instance to insert into the tree using the `instance` keyword.

Returns the created node object. It will be saved by this method.


#### get_roots_queryset
Returns **root nodes queryset**:
```python
cls.get_roots_queryset()
```

#### get_roots
Returns a **list with all root nodes**:
```python
cls.get_roots()
```

#### get_roots_pks
Returns a **list with all root nodes pks**:
```python
cls.get_roots_pks()
```

#### get_roots_count
Returns **count of roots**:
```python
cls.get_roots_pks()
```

#### get_first_root
Returns the first root node in the tree or `None` if it is empty.
```python
cls.get_first_root()
```

#### get_last_root
Returns the last root node in the tree or `None` if it is empty.
```python
cls.get_last_root()
```

---

### Sibling Methods
These methods facilitate working with **sibling nodes** within the same hierarchy level. You can retrieve siblings, count them, or add new sibling nodes while maintaining the correct order.

#### add_sibling
Add a new node as a sibling to the current node object.

```python
obj.add_sibling(position=None, **kwargs):
```

`position` specifies the order position of the object being added in the list of children of this node. It can be `'first-sibling'`, `'left-sibling'`, `'right-sibling'`, `'last-sibling'`, `'sorted-sibling'`, or an integer value.

The `**kwargs` parameters contain the object creation data that will be passed to the inherited node model. Instead of passing the object creation data, you can pass an already created (but not yet saved) model instance to insert into the tree using the `instance` keyword.

Returns the created node object or `None` if failed. It will be saved by this method.

#### get_siblings_queryset
Returns the **siblings queryset**:
```python
obj.get_siblings_queryset()
```

#### get_siblings
Returns a **list with all the siblings**:
```python
obj.get_siblings()
# or
obj.siblings
```

#### get_siblings_pks
Returns the **siblings pks** list:
```python
obj.get_siblings_pks()
```

#### get_siblings_count
Returns the **siblings count**:
```python
obj.get_siblings_count()
```

#### get_first_sibling
Returns the fist node’s sibling.

```python
obj.get_first_sibling()
```

Method can return the node itself if it was the leftmost sibling.

#### get_previous_sibling
Returns the previous sibling in the tree, or `None`.

```python
obj.get_previous_sibling()
```

#### get_next_sibling
Returns the next sibling in the tree, or `None`.

```python
obj.get_next_sibling()
```

#### get_last_sibling
Returns the fist node's sibling.

```python
obj.get_next_sibling()
```

Method can return the node itself if it was the leftmost sibling.

---

### Tree Methods
These methods provide functionality for **serialization and manipulation of entire tree structures**. They include:

- Exporting the tree as a **JSON structure**
- Loading a tree from serialized data
- Generating **annotated representations** for UI display
- Rebuilding or deleting the entire tree structure

#### dump_tree
Return an **n-dimensional dictionary** representing the model tree.

```python
cls.dump_tree(instance=None)
```

Introduced for compatibility with other packages. See [`get_tree()`](#get_tree) method.

#### get_tree
Return an **n-dimensional dictionary** representing the model tree.

```python
cls.get_tree(instance=None)
```

If instance is passed, returns a subtree rooted at instance (using `get_descendants_queryset`), if not passed, builds a tree for all nodes (loads all records in one query).

 #### get_tree_json(cls, instance=None):
Represent the **tree as a JSON-compatible string**.

```python
cls.get_tree_json(instance=None)
```

#### load_tree(cls, tree_data):
**Load a tree** from a list of dictionaries.

```python
cls.load_tree(tree_data)
```

Loaded nodes are synchronized with the database: existing records are updated, new ones are created. Each dictionary must contain the `id` key to identify the record.


#### load_tree_json
Takes a JSON-compatible string and decodes it into a tree structure.

```python
cls.load_tree_json(json_str)
```

#### get_tree_display
Returns a **multiline string representing** the model tree.

```python
cls.get_tree_display(instance=None, symbol="&mdash;")
```

Inserts an indentation proportional to the node depth, filling it with the value of the `symbol` parameter.

#### get_tree_annotated
Returns an **annotated list** from a tree branch.

```python
cls.get_tree_annotated()
```

Something like this will be returned:
```python
[
    (a,     {'open':True,  'close':[],    'level': 0})
    (ab,    {'open':True,  'close':[],    'level': 1})
    (aba,   {'open':True,  'close':[],    'level': 2})
    (abb,   {'open':False, 'close':[],    'level': 2})
    (abc,   {'open':False, 'close':[0,1], 'level': 2})
    (ac,    {'open':False, 'close':[0],   'level': 1})
]
```
All nodes are ordered by materialized path. 

This can be used with a template like this:
```html
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
```

#### update_tree(cls):
**Rebuld tree** manually:
```python
cls.update_tree()
```

#### delete_tree
**Delete the whole tree** for the current node class.

```python
cls.delete_tree()
```

---

### Logical Methods
These methods provide boolean checks to determine relationships between nodes. They allow verifying whether a node is an ancestor, descendant, sibling, leaf, or root.

#### is_ancestor_of
Return `True` if the current node **is ancestor** of target_obj:
```python
obj.is_ancestor_of(target_obj)
```

#### is_child_of
Return `True` if the current node **is child** of target_obj:
```python
obj.is_child_of(target_obj)
```

#### is_descendant_of
Return `True` if the current node **is descendant** of target_obj:
```python
obj.is_descendant_of(target_obj)
```

#### is_first_child
Return `True` if the current node is the **first child**:
```python
obj.is_first_child()
```

#### is_last_child
Return `True` if the current node is the **last child**:
```python
obj.is_last_child()
```

#### is_leaf
Return `True` if the current node is **leaf** (it has not children):
```python
obj.is_leaf()
```

#### is_parent_of
Return `True` if the current node **is parent** of target_obj:
```python
obj.is_parent_of(target_obj)
```

#### is_root
Return `True` if the current node **is root**:
```python
obj.is_root()
```

#### is_root_of
Return `True` if the current node **is root** of target_obj:
```python
obj.is_root_of(target_obj)
```

#### is_sibling_of
Return `True` if the current node **is sibling** of target_obj:
```python
obj.is_sibling_of(target_obj)
```

---

### Property Accessors
These properties provide direct access to frequently used node attributes such as `parent`, `children`, `siblings`,`depth`, `level`, `priority`, `descendants`, `ancestors`, `family`.

They simplify access to node data without requiring explicit method calls.

#### obj.ancestors
Returns a list with all ancestors (itself included). See [`get_ancestors()`](#get_ancestors) method.

#### obj.ancestors_count
Returns the ancestors count. See [`get_ancestors_count()`](#get_ancestors_count) method.

#### obj.ancestors_pks
Returns the ancestors pks list (itself included). See [`get_ancestors_pks()`](#get_ancestors_pks) method.

#### obj.breadcrumbs
Returns the breadcrumbs to current node (itself included). See [`get_breadcrumbs()`](#get_breadcrumbs) method.

#### obj.children
Returns a list containing all children (itself included). See [`get_children()`](#get_children) method.

#### obj.children_count
Returns the children count. See [`get_children_count()`](#get_children_count) method.

#### obj.children_pks
Returns the children pks list. See [`get_children_pks()`](#get_children_pks) method.

#### obj.depth
Returns the node depth. See [`get_depth()`](#get_depth) method.

### obj.descendants:
Returns a list containing all descendants (itself is not included). See [`get_descendants()`](#get_descendants) method.

#### obj.descendants_count
Returns the descendants count (itself is not included). See [`get_descendants_count()`](#get_descendants_count) method.

#### obj.descendants_pks
Returns the descendants pks list (itself is not included). See [`get_descendants_pks()`](#get_descendants_pks) method.

#### obj.first_child
Returns the first child node. See [`get_first_child()`](#get_first_child) method.

#### obj.index
Returns the node index. See [`get_index()`](#get_index) method.

#### obj.last_child
Returns the last child node. See [`get_last_child()`](#get_last_child) method.

#### obj.level
Returns the node level. See [`get_level()`](#get_level) method.

#### obj.parent
Returns node parent. See [`get_patent()`](#get_patent) method.

#### obj.parent_pk
Returns node parent pk. See [`get_parent_pk()`](#get_parent_pk) method.

#### obj.priority
Returns node oder position (priority). See [`get_priority()`](#get_priority) method.

### cls.roots
Returns a list with all root nodes. See [`get_roots()`](#get_roots) method.

#### obj.root
Returns the root node for the current node. See [`get_root()`](#get_root) method.

#### obj.root_pk
Returns the root node pk for the current node. See [`get_root_pk()`](#get_root_pk) method.

#### obj.siblings
Get a list with all the siblings. See [`get_siblings()`](#get_siblings) method.

#### obj.siblings_count
Returns the siblings count. See [`get_siblings_count()`](#get_siblings_count) method.

#### obj.siblings_pks
Returns  the siblings pks list. See [`get_siblings_pks()`](#get_siblings_pks) method.

#### cls.tree
Returns an n-dimensional dict representing the model tree. See [`get_tree()`](#get_tree) method.

#### cls.tree_display
Returns a multiline string representing the model tree. See [`get_tree_display()`](#get_tree_display) method.

#### obj.tn_order
Return the materialized path. See [`get_order()`](#get_order) method.
**Warning**: Use with caution! Will be changed in future versions.

---

### Obsolete methods
Some previously available methods have been replaced by new methods.

| Obsolete method  | Desctiption | New implementation |
| ------------ | ------------ | ------------ |
| `get_descendants_tree()`  | Returns a **n-dimensional** `dict` representing the **model tree**  |  [`cls.get_tree(cls, instance=None)`](#get_tree) |
| `get_descendants_tree_display()`  | Returns a a **multiline** `string` representing the **model tree** |  [`cls.get_tree_display(instance=None, symbol="&mdash;")`](#get_tree_display) |

---

The `django-fast-treenode` API provides a **robust, well-optimized**, and **extensible** interface for hierarchical data management in Django. Whether you're working with **large datasets** or **migrating from another tree-based package**, the methods are designed to be flexible and efficient.
