## Configuration Guide

### Installation

#### First-Time Installation
If you are installing `django-fast-treenode` for the first time, the process is straightforward. Simply install the package via `pip`:

```sh
pip install django-fast-treenode
```

Once installed, add `'treenode'` to your `INSTALLED_APPS` in `settings.py`:
##### settings.py
```python
INSTALLED_APPS = [
    ...
    'treenode',
]
```

Then, apply migrations:

```sh
python manage.py migrate
```

#### Upgrading or Migrating from `django-treenode`
If you are upgrading to a new version of `django-fast-treenode` or switching from `django-treenode`, it is essential to run migrations to ensure data consistency:

```sh
pip install --upgrade django-fast-treenode
python manage.py migrate
```

#### Migrating from Other Packages
If you are migrating from other tree management solutions, additional steps may be required. Please refer to the [Migration and Upgrade Guide](migration.md) for detailed instructions.

### Configuration

#### Cache Setup
To optimize performance, `django-fast-treenode` uses caching for tree structure operations. You can define a **dedicated cache backend** for the package by adding a `"treenode"` entry to `settings.CACHES`. If no dedicated cache is provided, the default Django cache will be used.

##### settings.py
```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "...",
    },
    "treenode": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "KEY_PREFIX": "",   # This is important!
        "VERSION":  None,    # This is important!
    },
}
```
**Important Notes:**
- You can use **any cache backend**, including Django’s built-in options or external solutions like **Redis** or **Memcached** .
- **`KEY_PREFIX` must be an empty string (`""`)**, and **`VERSION` must be `None`**, otherwise cache inconsistencies may occur.

#### Cache Size Allocation
By default, the cache stores all tree-related data for models inheriting from `TreeNodeModel`. You can control the cache size using `TREENODE_CACHE_LIMIT` in **megabytes**.

##### settings.py
```python
TREENODE_CACHE_LIMIT = 100
```
This setting determines the memory allocation for caching **all instances** of tree models.

For more details on how caching works and how to fine-tune its behavior, refer to the [Caching and Cache Management](cache.md)  Guide.
