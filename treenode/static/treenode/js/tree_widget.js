(function ($) {
    "use strict";

    /**
     * Инициализация Select2 для элементов с классом "tree-widget".
     * Теперь в AJAX-запросе передаются параметры:
     * - q: поисковый запрос
     * - model: имя модели (из data-forward)
     * - selected_id: текущий выбранный или reference‑узел (если selected_id не установлен)
     * - direction: направление загрузки ("center" или "down")
     * - limit: количество узлов для загрузки
     *
     * Если сервер возвращает reference_id и selected_id ещё не задан,
     * то widget обновляет свой data("selected") – это служит опорой для следующих запросов.
     */
    function initializeSelect2() {
        $(".tree-widget").each(function () {
            var $widget = $(this);
            var url = $widget.data("url");
            // Берем начальное значение выбранного узла из data-selected, если оно установлено
            var selectedId = $widget.data("selected") || null;
            var limit = 10;  // Количество узлов для загрузки

            if (!url) {
                console.error("Error: Missing data-url for", $widget.attr("id"));
                return;
            }

            $widget.select2({
                ajax: {
                    url: url,
                    dataType: "json",
                    delay: 250,
                    data: function (params) {
                        var forwardData = $widget.data("forward") || {};
                        // При каждом запросе используем текущее значение выбранного узла (если оно обновилось)
                        var currentSelectedId = $widget.data("selected") || selectedId;
                        // Используем параметр params.page для определения направления
                        // Если params.page существует, то это "down", иначе "center".
                        var direction = params.page ? "down" : "center";
                        return {
                            q: params.term,                // Поисковый запрос
                            model: forwardData.model || null,
                            selected_id: currentSelectedId, // Отправляем текущий (или reference) узел
                            direction: direction,
                            limit: limit
                        };
                    },
                    processResults: function (data) {
                        // Если узел не выбран, обновляем data("selected") из reference_id сервера.
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

            // Обработка прокрутки для ленивой загрузки:
            // При приближении к концу списка триггерим дополнительный запрос.
            $widget.on("select2:open", function () {
                $(".select2-results__options").on("scroll", function () {
                    var $results = $(this);
                    var scrollBottom = $results.prop("scrollHeight") - $results.scrollTop() - $results.innerHeight();

                    if (scrollBottom < 50) {
                        // Триггерим запрос с параметром page:true для загрузки "down"
                        $widget.select2("trigger", "query", { term: "", page: true });
                    }
                });
            });
        });
    }

    /**
     * Форматирование результата для отображения дерева.
     * Добавляет отступ в зависимости от уровня и иконку.
     */
    function formatTreeResult(result) {
        if (!result.id) {
            return result.text;
        }
        var level = result.level || 0;
        var isLeaf = result.is_leaf || false;
        var indent = "&nbsp;&nbsp;".repeat(level);
        var icon = isLeaf ? "📄 " : "📂 ";
        return $("<span>" + indent + icon + result.text + "</span>");
    }

    /**
     * Форматирование выбранного элемента.
     */
    function formatTreeSelection(result) {
        return result.text || "";
    }

    $(document).ready(function () {
        initializeSelect2();
    });

})(django.jQuery || window.jQuery);
