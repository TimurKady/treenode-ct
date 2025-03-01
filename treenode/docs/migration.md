# Migrations Guide
## Migration from _django-treenode_ packege
The migration process from `django-treenode` is fully automated. No manual steps are required. Upon upgrading, the necessary data structures will be checked and updated automatically.
Run the following commands in the terminal:

```bash
pip install django-fast-treenode
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
It's unlikely that you'll need or want this, but in exceptional cases you can call the whole tree update code `cls.update_tree()` manually.

---

## Update _django-fast-treenode_ version 2.1 and less
The sequence of actions when migrating from previous versions of `django-fast-treenode` is similar to upgrading models of the `django-treenode` package.
Run the following commands in the terminal:

```bash
pip install --upgrade django-fast-treenode
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
Now your models are updated and running even faster than before.

---

## Migration from _django-mptt_ or _django-treebeard_ packege
Migration from other packages is not as seamless as with `django-treebeard`, which is probably understandable. However, `django-fast-treenode` has been specially tweaked so that such migration requires minimal effort, including minimal changes to your project code.
Below is a guide on how to migrate to `django-fast-treenode` from other packages using a project using `django-treebeard` as an example. Migration from other packages will involve similar steps.

### Step 1: Export existing data
Launch the Python console:

```bash
python manage.py shell
```

Run the following code to export the tree structure:
```python
from yourapp.models import Category
import json

data = []

def export_tree(node):
    children = node.get_children()
    return {
        "id": node.id,
        "tn_parent": node.get_parent().id if node.get_parent() else None,
        "name": node.name,
        # Continue the list by inserting the required model fields
        # Do not export the `children` field
    }

roots = Category.objects.filter(depth=1)  # treebeard root nodes
for root in roots:
    data.append(export_tree(root))

with open("tree_data.json", "w") as f:
    json.dump(data, f, indent=4)
```

This code exports your structure to `tree_data.json` file. JSON preserves the id → tn_parent relationship, but without children.

Now clear the table:
```python
Category.objects.all().delete()
```
Remove `django-treebeard` if it is installed:
```bash
pip uninstall django-treebeard
```
Install `django-fast-treenode`:
```bash
pip install django-fast-treenode
```

Before you start the migration, it is important to make sure **you have a backup of your database**, as the tree storage structure will change.

### Step 2: Preparing for Migration
If you have a model in your project that uses `treebeard`, it probably looks like this:
```python
from treebeard.mp_tree import MP_Node

class Category(MP_Node):
    name = models.CharField(max_length=255)
```
Now we need to adapt it for `django-fast-treenode`. Change the model to use `TreeNodeModel` instead of `MP_Node`:
```python
from treenode.models import TreeNodeModel

class Category(TreeNodeModel):
    name = models.CharField(max_length=255)

    treenode_display_field = "name"
    treenode_sort_field = "None"
```
Be sure to add `treenode_display_field` as `django-fast-treenode` uses it to display nodes in the admin panel. 

The `treenode_sort_field` attribute specifies the tree sorting order. The default value of this field is `None`. It will sort by the internal field `tn_priority`.

The `tn_priority` value will be generated automatically if not specified during import. It will either be set as nodes are inserted into the tree (in the order in which the nodes will appear in the imported data), or after they are inserted, depending on the results of sorting by the field specified in the `treenode_sort_field` attribute.

> Note: sorting functions are available for `django-tree-node` version 2.3 and higher.

### Step 3: Update the code
The `django-fast-treenode` package contains the full set of methods you are used to. But the methods for working with the tree are slightly different. For example:

|**django-treebeard** | **django-fast-treenode** |**Features of use**|
|---------------------|----------------------|----------------------|
| The `pos` parameter in `add_sibling()` and `move()` methods |  The parameter `pos` has the name `position` | • The `position` parameter in `django-fast-treenode` always consists of two parts separated by `-`: the first part determines the insertion method (_first, left, right, last, sorted_), the second — the placement type (_child, sibling_). <br> • Instead of a string format, you can also pass position as an integer indicating the exact position of the node in the list.|
|`get_siblings()`, `get_ancestors()` end ect. | Similar methods have parameters `include_self` and `depth` |• The `include_self` parameter specifies whether to include the node itself in the selection. <br> • The  `depth` parameter specifies the depth of the search. |
|`move(target, pos)` metiod| The method `move()` has the name `move_to(target, position)` | - |

As you can see, unlike treebeard, django-fast-treenode provides more features, allowing you to use familiar methods more flexibly.

For more details, refer to the `django-fast-treenode` documentation and update your code accordingly


### Step 4: Create Migrations
After changing the model, new migrations need to be created and applied.

```bash
python manage.py makemigrations
python manage.py migrate
```

After a successful migration, you can remove references to `django-treebeard` in `requirements.txt` and `INSTALLED_APPS` if they were there.

### Step 5:  Data Import
Now start the server.
   ```bash
   python manage.py runserver
   ```

Go to Django Admin and import data into your model from the previously saved file. `django-fast-treenode` will do everything automatically. Check if the tree structure is displayed correctly. 

Moreover, the import will preserve the `id` of all nodes, which will ensure that the values of the keys referencing your model are unchanged.

---

Now your project has completely migrated from `django-treebeard` to `django-fast-treenode`. Your tree is more performant and easier to use, and your code is cleaner and more flexible.
