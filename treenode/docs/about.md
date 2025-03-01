# About the project
## The Debut Idea
The idea of ​​this package belongs to **[Fabio Caccamo](https://github.com/fabiocaccamo)**. His idea was to use the **Adjacency List** method to store the data tree. The most probable and time-consuming requests are calculated in advance and stored in the database. Also, most requests are cached. As a result, query processing is carried out in one call to the database or without it at all.

The original application **[django-treenode](https://github.com/fabiocaccamo/django-treenode)** has significant advantages over other analogues, and indeed, is one of the best implementations of support for hierarchical structures for Django.

However, this application has a number of undeniable shortcomings:
* the selected pre-calculations scheme entails high costs for adding a new element;
* inserting new elements uses signals, which leads to failures when using bulk-operations;
* the problem of ordering elements by priority inside the parent node has not been resolved.

That is, an excellent debut idea, in my humble opinion, should have been improved.

## The Development of the Idea
My idea was to solve these problems by combining the **Adjacency List** with the **Closure Table**. Main advantages:
* the Closure Model is generated automatically;
* maintained compatibility with the original package at the level of documented functions;
* most requests are satisfied in one call to the database;
* inserting a new element takes two calls to the database without signals usage;
* bulk-operations are supported;
* the cost of creating a new dependency is reduced many times;
* useful functionality added for some methods (e.g.  the `include_self=False` and `depth` parameters has been added to functions that return lists/querysets);
* additionally, the package includes a tree view widget for the `tn_parent` field in the change form.

Of course, at large levels of nesting, the use of the Closure Table leads to an increase in resource costs. However, the combined approach still outperforms both the original application and other available Django solutions in terms of performance, especially in large trees with over 100k nodes.

## The Theory
You can get a basic understanding of what is a **Closure Table** from:
* [presentation](https://www.slideshare.net/billkarwin/models-for-hierarchical-data) by **Bill Karwin**;
* [article](https://dirtsimple.org/2010/11/simplest-way-to-do-tree-based-queries.html) by blogger **Dirt Simple**;
* [article](https://towardsdatascience.com/closure-table-pattern-to-model-hierarchies-in-nosql-c1be6a87e05b) by **Andriy Zabavskyy**.

You can easily find additional information on your own on the Internet.

## Our days
Over the course of development, the package has undergone significant improvements, with a strong emphasis on performance optimization, database efficiency, and seamless integration with Django’s admin interface. The introduction of a hybrid model combining **Adjacency List** and **Closure Table** has substantially reduced query overhead, improved scalability, and enhanced flexibility when managing hierarchical data. These advancements have made the package not only a powerful but also a practical solution for working with large tree structures. Moving forward, the project will continue to evolve, focusing on refining caching mechanisms, expanding compatibility with Django’s ecosystem, and introducing further optimizations to ensure maximum efficiency and ease of use.
