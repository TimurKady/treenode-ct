## TreeNode Cache Management

### First Generation

The initial caching mechanism was inherited from the `django-treenode` package and was based on the simple use of Django's built-in cache. Each query result was stored in the cache, preventing repeated database queries and thereby improving performance.

The advantage of this approach was its simplicity: it was easy to integrate and provided a speed boost without complex configurations. However, it also had significant drawbacks. Since the mechanism did not control the total memory usage, it quickly filled the cache with a vast number of small queries. This led to cache system overload, reduced efficiency, and slowed down other parts of the application that relied on the same cache. As a result, intensive operations with tree structures could cause memory management issues and impact cache system performance.

---

### Second Generation

In the current version, the caching mechanism has been enhanced with **memory usage limitation** for all models inheriting from `TreeNodeModel`. This was implemented as a **FIFO queue (First In, First Out)**, which automatically removes the oldest entries when the limit is exceeded.

The choice of FIFO was driven by the package's universality. `django-fast-treenode` is designed to work in various scenarios, so it needed a strategy that efficiently handles evenly distributed queries. Even if queries are not evenly distributed in a particular project (e.g., some nodes are accessed more frequently than others), FIFO does not significantly reduce cache performance compared to the first-generation approach. However, it prevents uncontrolled memory growth, ensuring stable cache operation even under high request loads.


#### Key Features

**Global Cache Limit**: The setting `TREENODE_CACHE_LIMIT` defines the maximum cache size (in MB) for **all models** inheriting from `TreeNodeModel`. Default is **100MB** if not explicitly set in `settings.py`.

**settings.py**
``` python
TREENODE_CACHE_LIMIT = 100
```

**Automatic Management**. In most cases, users don’t need to manually manage cache operations.All methods that somehow change the state of models reset the tree cache automatically.

**Manual Cache Clearing**. If for some reason you need to reset the cache, you can do it in two ways:
- **Clear cache for a single model**: Use `clear_cache()` at the model level:
    ```python
    MyTreeNodeModel.clear_cache()
    ```
- **Clear cache for all models**: Use the global `treenode_cache.clear()` method:
    ```python
    from treenode.cache import treenode_cache
    treenode_cache.clear()
    ```

---

### Ceche API

#### `@cached_method` Decorator

The `@cached_method` decorator is available for caching method results in **class and instance methods** of models inheriting from `TreeNodeModel`. This decorator helps optimize performance by reducing redundant computations.

```python
from treenode.cache import cached_method
from treenode.models import TreeNodeModel

class Category(TreeNodeModel):
    name = models.CharField(max_length=50)

    @cached_method
    def my_tree_method(self):
        # Your code is here
```

In this example, `my_tree_method()` is cached.

**Important:** The decorator should **only** be used with `TreeNodeModel` subclasses. Applying it to other classes will cause unexpected behavior.


#### Accessing Cache via `treenode_cache`

A global cache instance `treenode_cache` provides direct cache manipulation methods, allowing you to generate cache keys, store, retrieve, and invalidate cached values.

Methods available in `treenode_cache`:

#### generate_cache_key()
Generates a unique cache key for caching method results. The key is based on model name, method name, object identifier, and method parameters.

```python
cache_key = treenode_cache.generate_cache_key(
    label=Category._meta.label,  # Model label
    func_name=self.<The method you are in>.__name__,
    unique_id=42,   # This can be the object.pk. In a desperate situation, use id(self)
    attr="some string value"
)
```
This ensures that the cache key follows Django's conventions and remains unique.

#### set()
Stores a value in the cache.

```python
treenode_cache.set(cache_key, {'name': 'Root', 'id': 1})
```
This caches a dictionary object under the generated key.

#### get()
Retrieves a cached value by its cache key.

```python
cached_value = treenode_cache.get(cache_key)
if cached_value is None:
    cached_value = compute_expensive_query()
    treenode_cache.set(cache_key, cached_value)
```

#### invalidate()
Removes all cached entries for a **specific model**.

```python
treenode_cache.invalidate(Category._meta.label)
```
This clears all cache entries related to `Category` instances.

#### clear()
Clears **all** cached entries in the system.

```python
treenode_cache.clear()
```
This completely resets the cache, removing **all stored values**.

Best Practices:
- **Always use `generate_cache_key()`** instead of hardcoding cache keys to ensure consistency.
- **Use `invalidate()` instead of `clear()`** when targeting a specific model’s cache.
- **Apply `@cached_method` wisely**, ensuring it is used **only for** `TreeNodeModel`-based methods to avoid conflicts.
- **Be mindful of cache size**, as excessive caching can lead to memory bloat.

By leveraging these caching utilities, `django-fast-treenode` ensures efficient handling of hierarchical data while maintaining high performance.

---

### Third Generation (Currently in Development)

The next version of the caching mechanism introduces adaptability, a **split between "cold" and "hot" caches**, and enhanced eviction strategies. Key improvements include:

#### 1. Two-Tier Caching System

The cache is now divided into two queues:

- **FIFO (70%-80%)** – for new and infrequently accessed data.
- **LRU (20%-30%)** – for frequently accessed objects (Least Recently Used).

How it works:
- If tree queries are evenly distributed, the cache behaves like a standard FIFO.
- If certain nodes receive frequent queries, those records automatically move to LRU, reducing database load.

#### 2. Moving Data Between FIFO and LRU

Each new entry initially goes into **FIFO**. If accessed **more than N times**, it moves to **LRU**, where it remains longer.

**How N is determined:**
- A threshold is set based on **mathematical statistics**: N = 1 / sqrt(2).
- An absolute threshold limit is added.

**LRU Behavior:**
- When accessed, a record moves to the top of the list.
- New records are also placed at the top.
- If LRU reaches capacity, **the evicted record returns to FIFO** instead of being deleted.

#### 3. Cache Invalidation

When data is modified or deleted, the cache **automatically resets** to prevent outdated information. This ensures that modified tree structures do not retain stale data in the cache.

#### 4. Dynamic Time Threshold (DTT)

To automatically clear outdated records, an **adaptive mechanism** is used. Instead of a static TTL, the **DTT parameter** is dynamically calculated based on **Poisson distribution**.

How DTT is calculated:
1. Compute the **average interval between queries (T)**: ``` T = (1/N) * Σ (t_i - t_(i-1)), i=1...N```
2. Store **averaged value** `ΣΔt / N`
3. Set **DTT = 3T**, which removes **95% of infrequent queries**.

**Why this is better than a fixed TTL:**
- If queries are rare → DTT **increases**, preventing premature deletions.
- If queries are frequent → DTT **decreases**, accelerating cache clearing.

All calculations happen **automatically**, without manual configuration.

Additionally, this mechanism will support synchronization in multiprocess environments (WSGI, Gunicorn, Uvicorn).

---

### Fourth Generation (Planned)

The next generation of caching will include:

- **Middleware for caching nodes**, considering nested objects.
- **"Smart" prediction** of peak and dynamics of loads.
- **Asynchronous operations** support, ensuring efficient caching and retrieval in non-blocking environments.

Future versions will continue improving this mechanism, making it **even more efficient and predictable** when working with large tree structures.
