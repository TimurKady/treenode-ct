# Import&Export Functionality
## Overview

TreeNode v2.0 includes **built-in export and import features** for easier data migration. Supported Formats: `csv`, `json`, `xlsx`, `yaml`, `tsv`. The system supports importing and exporting data for any models, allowing users to efficiently manage and update data while preserving its structure and relationships.

## Installation for Import/Export Features
By default, import/export functionality is **not included** to keep the package lightweight. If you need these features, install the package with:
```bash
pip install django-fast-treenode[import_export]
```

Once installed, **import/export buttons will appear** in the Django admin interface.

## Data Processing Logic
When importing data into the system, **three key fields** must be present:
- **`id`** – the unique identifier of the record.
- **`tn_parent`** – the identifier of the parent node.
- **`tn_priority`** – the ordinal number of the node among its parent's children.

These fields ensure the correct construction of the hierarchical data structure.

Important:
- If a record with the same `id` **already exists** in the database, its data **will be updated** with the imported values.
- If no record with the given `id` **is found**, a **new record will be created** with the specified parameters.

This import mechanism is designed to allow users to:
- **Export data**, edit it (e.g., in a CSV, Excel, or JSON file).
- **Upload the modified file** without disrupting the model structure.
- **Update only the changed data**, keeping relationships with other models intact (e.g., without altering primary and foreign key values).

This approach provides **flexible data management**, enabling users to safely apply modifications without manually updating each record in the system.

## Important Considerations

Exporting objects with M2M fields may lead to serialization issues. Some formats (e.g., CSV) do not natively support many-to-many relationships. If you encounter errors, consider exporting data in `json` or `yaml` format, which better handle nested structures.
