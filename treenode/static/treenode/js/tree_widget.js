(function ($) {
    "use strict";

/**

Initialize Select2 for elements with class "tree-widget".
Now the parameters passed in the AJAX request are:
- q: search query
- model: model name (from data-forward)
- selected_id: currently selected or reference node
  (if selected_id is not set)
- direction: load direction ("center" or "down")
- limit: number of nodes to load

If the server returns a reference_id and selected_id is not set yet,
then widget updates its data("selected") - this serves as a reference for
the following requests.

Version 2.0.0

*/

    function initializeSelect2() {
        $(".tree-widget").each(function () {
            var $widget = $(this);
            var url = $widget.data("url");
            // Take the initial value of the selected node from data-selected if it is set
            var selectedId = $widget.data("selected") || null;
            var limit = 10;  // Number of nodes to load

            if (!url) {
                console.error("Error: Missing data-url for", $widget.attr("id"));
                return;
            }

            $widget.select2({
                ajax: {
                    url: url,
                    dataType: "json",
                    delay: 500,
                    data: function (params) {
                        var forwardData = $widget.data("forward") || {};
                        // For each request, use the current value of the selected node (if it has been updated)
                        var currentSelectedId = $widget.data("selected") || selectedId;
                        // Use params.page to determine direction
                        // If params.page exists, it is "down", otherwise "center".
                        var direction = params.page ? "down" : "center";
                        return {
                            q: params.term,   // Search query
                            model: forwardData.model || null,
                            selected_id: currentSelectedId, // Send the current (or reference) node
                            direction: direction,
                            limit: limit
                        };
                    },
                    processResults: function (data) {
                        // If the node is not selected, update data("selected") from the server's reference_id.
                        if (!$widget.data("selected") && data.reference_id) {
                            $widget.data("selected", data.reference_id);
                        }
                        return { results: data.results };
                    }
                },
                minimumInputLength: 0,
                allowClear: true,
                width: "100%",
                templateResult: formatTreeResult,
                templateSelection: formatTreeSelection,
                escapeMarkup: function (markup) {
                    return markup;
                }
            });

            // Handle scrolling for lazy loading:
            // When approaching the end of the list, trigger an additional request.
            $widget.on("select2:open", function () {
                $(".select2-results__options").on("scroll", function () {
                    var $results = $(this);
                    var scrollBottom = $results.prop("scrollHeight") - $results.scrollTop() - $results.innerHeight();

                    if (scrollBottom < 50) {
                        // Trigger a request with the page:true parameter to load "down"
                        $widget.select2("trigger", "query", { term: "", page: true });
                    }
                });
            });
        });
    }

    /**
    * Formatting the result to display the tree.
    * Adds indentation depending on the level and an icon.
    */
    function formatTreeResult(result) {
        if (!result.id) {
            return result.text;
        }
        var level = result.level || 0;
        var isLeaf = result.is_leaf || false;
        var indent = "&nbsp;&nbsp;".repeat(level);
        var icon = isLeaf ? "📄 " : "📁 ";
        return $("<span>" + indent + icon + result.text + "</span>");
    }

    /**
    * Format the selected element.
    */
    function formatTreeSelection(result) {
        return result.text || "";
    }

    $(document).ready(function () {
        initializeSelect2();
    });

})(django.jQuery || window.jQuery);
