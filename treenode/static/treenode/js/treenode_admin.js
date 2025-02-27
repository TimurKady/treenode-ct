/* 
TreeNode Admin JavaScript

This script enhances the Django admin interface with interactive 
tree structure visualization. It provides expand/collapse functionality 
for hierarchical data representation.

Features:
- Dynamically generates node displays, preventing an increase in the load
  on the database.
- Allows you to expand and collapse nodes.
- Manage node searches.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
*/

(function($) {
  // Function for debounce call (execution delay)
  function debounce(func, wait) {
    var timeout;
    return function() {
      var context = this, args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(function() {
        func.apply(context, args);
      }, wait);
    };
  }

  // Save the original contents of the change_list table (root nodes only)
  var $tableBody = $('table#result_list tbody');
  var originalTableHtml = $tableBody.html();

  // Handler for clicking on the toggle button (expand/collapse)
  $tableBody.on('click', '.treenode-toggle', function(e) {
    e.preventDefault();
    var $btn = $(this);
    var nodeId = $btn.data('node-id');

    // If this node is already expanded, collapse it
    if ($btn.data('expanded')) {
      // Remove all rows marked as children of this node
      $tableBody.find('tr[data-parent-of="' + nodeId + '"]').remove();
      // Change the icon back to ▶ and reset the flag
      $btn.html('▶').data('expanded', false);
    } else {
      // Node not expanded, make AJAX request to get children
      $.getJSON('change_list/', { parent_id: nodeId }, function(response) {
        // Если ответ содержит дочерние узлы
        if (response.results && response.results.length > 0) {
          var rowsHtml = '';
          // For each received node we form a table row
          $.each(response.results, function(index, node) {
            // First column: drag handle (icon)
            var dragCell = '<td class="drag-cell"><span class="treenode-drag-handle">↕</span></td>';
            // Second column: toggle button if node has children, otherwise empty block
            var toggleCell = '';
            if (!node.is_leaf) {
              toggleCell = '<td class="toggle-cell"><button class="treenode-toggle" data-node-id="' + node.id + '">▶</button></td>';
            } else {
              toggleCell = '<td class="toggle-cell"><div class="treenode-space">&nbsp;</div></td>';
            }
            // Third column: node display (HTML, already with accordion wrapper)
            var displayCell = '<td class="display-cell">' + node.text + '</td>';
            // Collect the entire row; add a data attribute so that we can later collapse all children of this node
            rowsHtml += '<tr data-parent-of="' + nodeId + '">' + dragCell + toggleCell + displayCell + '</tr>';
          });
          // Insert new lines immediately after the line of the parent node
          var $parentRow = $btn.closest('tr');
          $parentRow.after(rowsHtml);
          // Update the expand icon and set the "expanded" flag
          $btn.html('▼').data('expanded', true);
        }
      });
    }
  });

  // Handler for searching nodes with delay
  $('input[name="q"]').on('keyup', debounce(function(e) {
    var query = $.trim($(this).val());
    // If the search string is empty, return the initial state of change_list (root nodes only)
    if (query === '') {
      $tableBody.html(originalTableHtml);
      return;
    }
    // If there is a search query, we make an AJAX request to the endpoint "search/"
    $.getJSON('search/', { q: query }, function(response) {
      var rowsHtml = '';
      if (response.results && response.results.length > 0) {
        $.each(response.results, function(index, node) {
          var dragCell = '<td class="drag-cell"><span class="treenode-drag-handle">↕</span></td>';
          var toggleCell = '';
          if (!node.is_leaf) {
            toggleCell = '<td class="toggle-cell"><button class="treenode-toggle" data-node-id="' + node.id + '">▶</button></td>';
          } else {
            toggleCell = '<td class="toggle-cell"><div class="treenode-space">&nbsp;</div></td>';
          }
          var displayCell = '<td class="display-cell">' + node.text + '</td>';
          // In the search we consider that all nodes are root (closed)
          rowsHtml += '<tr>' + dragCell + toggleCell + displayCell + '</tr>';
        });
      } else {
        rowsHtml = '<tr><td colspan="3">Ничего не найдено</td></tr>';
      }
      // Update the table contents with the search results
      $tableBody.html(rowsHtml);
    });
  }, 500)); // delay 500ms

})(django.jQuery || window.jQuery);
