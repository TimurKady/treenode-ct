## Model Inheritance and Extensions

### Model Inheritance

To define a model that supports tree structures, simply inherit from `TreeNodeModel`. Below is an example of a basic category model:

##### models.py

```python
from django.db import models
from treenode.models import TreeNodeModel

class Category(TreeNodeModel):

    treenode_display_field = "name"  # Defines the field used for display in the admin panel

    name = models.CharField(max_length=50)

    class Meta(TreeNodeModel.Meta):  # Ensure TreeNodeModel's indexing settings are preserved
        verbose_name = "Category"
        verbose_name_plural = "Categories"
```

Key Considerations:
- `treenode_display_field`  
This attribute defines which field will be used to display the tree structure in the Django admin panel. If it is not set, nodes will be named generically as `"Node <id>"`, where `<id>` is the primary key of the record.
- Inheriting model Meta class from `TreeNodeModel.Meta`
It is **essential** to inherit the `Meta` class from `TreeNodeModel.Meta`. Failure to do so may impact database performance and query efficiency.

With this setup, your model will seamlessly integrate into Django, supporting hierarchical relationships while maintaining optimized indexing and efficient querying.


### Model Extending

When extending a model based on `TreeNodeModel`, you have full flexibility to add custom fields and methods. However, to ensure compatibility and maintainability, follow these best practices.

#### General Guidelines
You are free to add new fields and methods. The basic model does not impose any restrictions on the expansion of functionality. However, it is strongly recommended to adhere to the principles and standards of the object-oriented approach.
**Avoid direct access to model fields** when modifying tree-related data.  
     Fields with the `tn_` prefix **may be renamed in future versions** (this is already planned). Instead of assigning values directly, use **accessor and mutator methods**:  
```python
# ❌ Avoid direct assignment
node.tn_parent = other_node

# ✅ Use the provided method
node.set_parent(other_node)
```
**Hardcoding field names may lead to compatibility issues in future updates.** Always use methods provided by the package when working with tree structures.

#### Extending Indexing

If your model requires additional indexing, **do not override the indexing settings of `TreeNodeModel.Meta`**. Instead, extend them properly using Django’s index definitions.

If you want to add an index to a new or existing field (e.g., `"name"`), do it as follows:

```python
from django.db import models
from treenode.models import TreeNodeModel

class Category(TreeNodeModel):

    treenode_display_field = "name"

    name = models.CharField(max_length=50, db_index=True)  # Adding an index to "name"

    class Meta(TreeNodeModel.Meta):  # Preserve indexing settings from TreeNodeModel
        indexes = TreeNodeModel.Meta.indexes + [
            models.Index(fields=["name"]),
        ]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
```

By following these principles, your extended models will remain stable, maintainable, and compatible with future versions of `django-fast-treenode`.

### Customize Managers

When defining custom model managers for `TreeNodeModel`, it is **essential** to extend `TreeNodeModelManager` rather than modifying internal components like `ClosureQuerySet`, `ClosureModelManager`, or `TreeNodeQuerySet`. Direct manipulation of these lower-level structures **can lead to data corruption** and is not guaranteed to remain stable in future versions.

#### Always Extend TreeNodeModelManager
To ensure stability and maintain tree integrity, always **extend** `TreeNodeModelManager`. Never directly interact with internal tree structures like the Closure Table or adjacency list.

Example: Safe Custom Manager:
```python
from treenode.managers import TreeNodeModelManager

class CustomTreeNodeManager(TreeNodeModelManager):
    def active(self):
        """Return only active nodes."""
        return self.get_queryset().filter(is_active=True)
```
**Correct**: This approach preserves all core tree operations while adding custom behavior.

#### Avoid Direct Parent-Child Modifications
Modifying relationships improperly can break the tree structure. Use built-in methods instead:

Safe Parent Update:
```python
node.set_parent(new_parent)  # ✅ Safe
node.tn_parent = new_parent  # ❌ Unsafe (bypasses tree updates)
```

#### **3. Use `bulk_create` and `bulk_update` Carefully**
Since tree structures require synchronization between adjacency and closure models, **always use transactions**:

Safe Bulk Create Example:

```python
from django.db import transaction

class CustomTreeNodeManager(TreeNodeModelManager):
    @transaction.atomic
    def bulk_create(self, objs, batch_size=1000):
        """Ensures proper insertion of nodes without breaking the tree."""
        objs = super().bulk_create(objs, batch_size=batch_size)
        return objs
```
**Important**: Do not directly insert nodes without using `bulk_create` from `TreeNodeModelManager`.

#### Custom Queries
Use `get_queryset()` Instead of QuerySet Overrides. If custom queries are needed, **override `get_queryset()`** in your manager instead of modifying internal querysets:
```python
class CustomTreeNodeManager(TreeNodeModelManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
```

By following these principles, you ensure your custom managers remain **future-proof**, **safe**, and **maintainable** without the risk of breaking tree integrity.
