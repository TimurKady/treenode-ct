
# <span style="color:red">⚠️ Branch 2.1 is in development. Do not use it!</span>


# Django-fast-treenode 
__Combination of Adjacency List and Closure Table__

## Functions
Application for supporting tree (hierarchical) data structure in Django projects
* **fast**: the fastest of the two methods is used to process requests, combining the advantages of an **Adjacency List** and a **Closure Table**,
* **even faster**: the main resource-intensive operations are **cached**; **bulk operations** are used for inserts and changes,
* **scale**: optimized for working with large models with a high level of nesting,
* **easy setup**: just extend the abstract model/model-admin,
* **synchronized**: model instances in memory are automatically updated,
* **compatibility**: you can easily add a tree node to existing projects using `TreeNode` without changing the code,
* **admin** integration: visualization options (accordion, breadcrumbs or padding),
* **widget**: built-in Select2 to support arbitrary nesting levels.

This is currently the most productive solution for working with hierarchical data in Django.

## Quick start
1. Run ```pip install django-fast-treenode```
2. Add ```treenode``` to ```settings.INSTALLED_APPS```
3. Make your model inherit from ```treenode.models.TreeNodeModel``` (described below)
4. Make your model-admin inherit from ```treenode.admin.TreeNodeModelAdmin``` (described below)
5. Run python manage.py makemigrations and ```python manage.py migrate```

For more information on migrating from the **django-treenode** package and upgrading to version 2.0, see [below](#migration-guide).

## Usage

Full documentation:

Import and export:

Migration and upgrade guide:

## License
Released under [MIT License](https://github.com/TimurKady/django-fast-treenode/blob/main/LICENSE).

## Credits
Special thanks to [Mathieu Leplatre](https://blog.mathieu-leplatre.info/pages/about.html) for the advice used in writing this application.
