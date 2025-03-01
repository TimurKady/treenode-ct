## Roadmap
The latest version provides optimized database operations, an improved caching mechanism, and enhanced integration capabilities, making it a **robust and efficient choice** for handling tree structures.

But the **django-fast-treenode** package will continue to evolve from its original concept—combining the benefits of the **Adjacency List** and **Closure Table** models—into a high-performance solution for managing and visualizing hierarchical data in Django projects. The focus is on **speed, usability, and flexibility**.

In future versions, I plan to implement:

### **Version 2.1 – Compatibility and Optimization**
Reducing dependencies and simplifying migration from other libraries.
- **Expanding functionality** to simplify migration from other tree packages.
- Introducing node **filtering and search with AJAX**.
- **Optimizing query performance** by reducing query complexity and improving indexing strategies.
- **Reducing database load** from the `TreeNodeAdmin` when working with large trees.
- Removing `numpy` in favor of lighter alternatives.

### **Version 2.2 – Caching Improvements**
Speeding up tree operations and reducing database load.
- **Implementing a more efficient caching algorithm** to optimize performance and reduce recomputation.
- **Refining cache expiration strategies** for better memory management.

### **Version 2.3 – Performance Enhancements**
- **Reducing query overhead** and optimizing bulk operations for large datasets.
- **Django REST Framework (DRF)**: Adding initial integration for efficient tree-based API handling.
- **Serialization**: Developing lightweight tree serialization for API-first projects.
- **Enhancing node filtering and search** with AJAX-driven interfaces.

### **Version 2.4 – Drag-and-Drop and Admin UI Improvements**
- **Drag-and-Drop**: Adding drag-and-drop support for node sorting in Django admin.
- **Advanced Sorting**: Adding multiple sorting strategies for tree nodes, including manual ordering and hierarchical priority rules.
- **Admin Panel Enhancements**: Expanding the functionality of the Django admin interface for managing hierarchical data more efficiently.

### **Version 3.0 – Fourth-Generation Cache Management System**
- **Reworking Adjacency List and Closure Table managers** for a new caching system.
- **Shifting from caching computed results to directly caching tree nodes**, reducing recomputation overhead and improving cache efficiency.
- **Enhancing cache consistency** across multiple processes (WSGI, Gunicorn, Uvicorn) with a global synchronization mechanism.

### **Version 4.0 – Moving Beyond Django ORM**
Enabling tree structures to function without a strict dependency on Django ORM while maintaining compatibility.
- **Introducing support for various storage backends**, allowing greater flexibility.
- **Adding compatibility with Redis for in-memory tree storage** and JSON-based trees for lightweight embedded storage.
- **Expanding usage in API-first projects**, enabling tree structures to work independently from Django models.

Stay tuned for updates!
Your wishes, objections, and comments are welcome.
