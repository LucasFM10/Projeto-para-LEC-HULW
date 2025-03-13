document.addEventListener("DOMContentLoaded", function() {
    // Aguarda o Django carregar o jQuery
    function loadJQuery(callback) {
        if (typeof django !== "undefined" && django.jQuery) {
            callback(django.jQuery);
        } else {
            setTimeout(function() { loadJQuery(callback); }, 50);
        }
    }

    loadJQuery(function($) {
        console.log("jQuery carregado!");

        $(document).ready(function() {
            $(document).on("change", "#id_especialidade", function() {

                let especialidadeId = $(this).val();
                let procedimentoField = $('#id_procedimento');

                $.get(`admin/filtrar_procedimentos/?especialidade_id=${especialidadeId}`, function(data) {
                    procedimentoField.empty(); // Limpa as opções anteriores
                    console.log("111")
                    console.log(data)
                    console.log("222")
                    $.each(data.procedimentos, function(index, proc) {
                        procedimentoField.append(new Option(proc.nome, proc.id));
                    });
                });
            });
        });
    });
});
