## Working with Admin Classes

### Using `TreeNodeModelAdmin`
The easiest way to integrate tree structures into Django’s admin panel is by inheriting from `TreeNodeModelAdmin`. This base class provides all the necessary functionality for managing hierarchical data.

##### admin.py:
```python
from django.contrib import admin
from treenode.admin import TreeNodeModelAdmin

from .models import Category

@admin.register(Category)
class CategoryAdmin(TreeNodeModelAdmin):

    # Set the display mode: 'accordion', 'breadcrumbs', or 'indentation'
    treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_ACCORDION
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_BREADCRUMBS
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_INDENTATION

    list_display = ("name",)
    search_fields = ("name",)
```

The tree structure in the admin panel **loads dynamically as nodes are expanded**. This allows handling **large datasets** efficiently, preventing performance issues.

You can choose from three display modes:
- **`TREENODE_DISPLAY_MODE_ACCORDION` (default)**  
  Expands/collapses nodes dynamically.
- **`TREENODE_DISPLAY_MODE_BREADCRUMBS`**  
  Displays the tree as a sequence of **breadcrumbs**, making it easy to navigate.
- **`TREENODE_DISPLAY_MODE_INDENTATION`**  
  Uses a **long dash** (`———`) to indicate nesting levels, providing a simple visual structure.

The accordion mode is **always active**, and the setting only affects how nodes are displayed.

**Why Dynamic Loading**:  Traditional pagination does not work well for **deep hierarchical trees**, as collapsed trees may contain a **huge number of nodes**, which is in the hundreds of thousands. The dynamic approach allows efficient loading, reducing database load while keeping large trees manageable.

#### Search Functionality
The search bar helps quickly locate nodes within large trees. As you type, **an AJAX request retrieves up to 20 results** based on relevance. If you don’t find the desired node, keep typing to refine the search until fewer than 20 results remain.

### Working with Forms

#### Using TreeNodeForm
If you need to customize forms for tree-based models, inherit from `TreeNodeForm`. It provides:
- A **custom tree widget** for selecting parent nodes.
- Automatic **exclusion of self and descendants** from the parent selection to prevent circular references.

##### `forms.py`:
```python
from treenode.forms import TreeNodeForm
from .models import Category

class CategoryForm(TreeNodeForm):
    """Form for Category model with hierarchical selection."""

    class Meta(TreeNodeForm.Meta):
        model = Category
```

Key Considerations:
- This form automatically ensures that **a node cannot be its own parent**.
- It uses **`TreeWidget`**, a custom hierarchical dropdown for selecting parent nodes.
- If you need a form for another tree-based model, use the **dynamic factory method**:
  
  ```python
  CategoryForm = TreeNodeForm.factory(Category)
  ```

This method ensures that the form correctly associates with different tree models dynamically.


### Using TreeWidget Widget

#### The TreeWidget Class
The `TreeWidget` class is a **custom Select2-based widget** that enables hierarchical selection in forms. While it is used inside the Django admin panel by default, it can **also be used in regular forms** outside the admin panel.

##### `widgets.py`

```python
from django import forms
from treenode.widgets import TreeWidget
from .models import Category

class CategorySelectionForm(forms.Form):
    parent = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=TreeWidget(),
        required=False
    )
```

Important Notes:
- **Requires jQuery**: The widget relies on Select2 and AJAX requests, so ensure jQuery is available when using it outside Django’s admin.
- **Dynamically Fetches Data**: It loads the tree structure asynchronously, preventing performance issues with large datasets.
- **Customizable Data Source**: The `data-url` attribute can be adjusted to fetch tree data from a custom endpoint.

If you plan to use this widget in non-admin templates, make sure the necessary **JavaScript and CSS files** are included:
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js"></script>
<script src="/static/treenode/js/tree_widget.js"></script>
```

By following these guidelines, you can seamlessly integrate `TreeNodeModelAdmin`, `TreeNodeForm`, and `TreeWidget` into your Django project, ensuring efficient management of hierarchical data.
