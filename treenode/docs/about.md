## About the project
### The Debut Idea
The idea of ​​this package belongs to **[Fabio Caccamo](https://github.com/fabiocaccamo)**. His idea was to use the **Adjacency List** method to store the data tree. The most probable and time-consuming requests are calculated in advance and stored in the database. Also, most requests are cached. As a result, query processing is carried out in one call to the database or without it at all.

The original application **[django-treenode](https://github.com/fabiocaccamo/django-treenode)** has significant advantages over other analogues, and indeed, is one of the best implementations of support for hierarchical structures for Django.

However, this application has a number of undeniable shortcomings:
* the selected pre-calculations scheme entails high costs for adding a new element;
* inserting new elements uses signals, which leads to failures when using bulk-operations;
* the problem of ordering elements by priority inside the parent node has not been resolved.

That is, an excellent debut idea, in my humble opinion, should have been improved.

---

### The Development of the Idea
My idea was to solve these problems by combining the adjacency list with the Closure Table. Main advantages:
* the Closure Model is generated automatically;
* maintained compatibility with the original package at the level of documented functions;
* most requests are satisfied in one call to the database;
* inserting a new element takes two calls to the database without signals usage;
* bulk-operations are supported;
* the cost of creating a new dependency is reduced many times;
* useful functionality added for some methods (e.g.  the `include_self=False` and `depth` parameters has been added to functions that return lists/querysets);
* additionally, the package includes a tree view widget for the `tn_parent` field in the change form.

Of course, at large levels of nesting, the use of the Closure Table leads to an increase in resource costs. However, the combined approach still outperforms both the original application and other available Django solutions in terms of performance, especially in large trees with over 100k nodes.

---

### The Theory
You can get a basic understanding of what is a **Closure Table** from:
* [presentation](https://www.slideshare.net/billkarwin/models-for-hierarchical-data) by **Bill Karwin**;
* [article](https://dirtsimple.org/2010/11/simplest-way-to-do-tree-based-queries.html) by blogger **Dirt Simple**;
* [article](https://towardsdatascience.com/closure-table-pattern-to-model-hierarchies-in-nosql-c1be6a87e05b) by **Andriy Zabavskyy**.

You can easily find additional information on your own on the Internet.

---

### The First Implementation
The first version of the package was released in January 2023 and underwent continuous improvements over the following year and a half. It demonstrated that leveraging two models—one implementing the **Adjacency List** and the other implementing the **Closure Table**—offers several key advantages:

- Reduced overhead for object creation.  
- Efficient data retrieval with only one or two database queries.  
- Minimal database load.  

However, this version also had some limitations. First, queries could have been further optimized through the use of **JOIN operations**, which were not fully utilized. Second, the caching system required enhancements, as numerous small queries quickly filled the cache, leading to excessive load.

---

### The Second Version

The next version of the package, released in early 2025, is a complete redesign focused primarily on performance optimization. Key improvements include:

1. **Optimized database queries.**  
   All core operations now execute in a single database query, significantly improving data retrieval efficiency.

2. **Custom caching system.**  
   A dedicated cache manager has been introduced to regulate cache load and prevent excessive memory consumption due to frequent small queries.

3. **Data import and export functionality.**  
   The package now supports seamless data import/export for tree models, simplifying data migration and backups.

4. **Enhanced admin panel integration.**  
   The Django admin class has been optimized to reduce query overhead.

Additionally, the package includes a **built-in Select2 widget**, enabling seamless integration of hierarchical structures within the Django admin interface while supporting arbitrary levels of nesting.

---

### The Development Plan

The latest version provides optimized database operations, an improved caching mechanism, and improved integration capabilities, making it a **robust and efficient choice** for handling tree structures. But the **django-fast-treenode** package will continue to evolve from its original concept — combining the benefits of the **Adjacency List** and **Closure Table** models — into a high-performance solution for managing and visualizing hierarchical data in Django projects.

The focus is on **speed, usability, and flexibility**. In future versions, I plan to implement:  

**Version 2.1 – Compatibility and Optimization**  
Reducing dependencies and simplifying migration from other libraries.  
- Removing `numpy` in favor of lighter alternatives.  
- Expanding functionality to simplify migration from other tree packages.  

**Version 2.2 – Performance and Caching**  
Speeding up tree operations and reducing database load.  
- Improving caching: implementing more efficient caching algorithms.  
- Optimizing query performance.  

**Version 2.3 – Ease of use in API-first projects**  
- Developing lightweight tree serialization.  
- Adding initial integration with **Django REST Framework (DRF)**.  

**Version 3.0 – Drag-and-Drop and Admin UI Improvements**  
Making tree management more intuitive.  
- Adding **Drag-and-Drop** support for node sorting in **Django admin**.  
- Enhancing node filtering and search with **AJAX**.
- Refusing to cache calculation results in favor of **caching tree nodes**.

**Version 4.0 – Moving Beyond Django ORM**  
Enabling tree structures to function without a strict dependency on Django.  
- Introducing support for **various storage backends**.  
- Adding compatibility with **Redis** and **JSON-based** tree storage.  
- Expanding usage in **API-first** projects.  

Stay tuned for updates!
Your wishes, objections, comments are welcome.
