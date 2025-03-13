   
(function() {
    function waitForJQuery(callback) {
        if (typeof django !== "undefined" && django.jQuery) {
            callback(django.jQuery);
        } else {
            setTimeout(() => waitForJQuery(callback), 50);
        }
    }

    waitForJQuery(($) => {
        $(document).ready(function() {
            var especialidadeField = $('#id_especialidade');
            var procedimentoField = $('#id_procedimento');

            function configurarSelect2() {
                var especialidadeId = especialidadeField.val();
                
                if (!especialidadeId) return; // Se não houver especialidade, não faz nada

                console.log("📢 Filtrando procedimentos para especialidade:", especialidadeId);

                var baseUrl = "/admin/autocomplete/?app_label=fila_cirurgica&model_name=procedimentoaghu&field_name=procedimento";

                procedimentoField.select2({
                    ajax: {
                        url: baseUrl,  // 🔥 URL agora contém os parâmetros obrigatórios
                        data: function (params) {
                            return {
                                q: params.term,  // 🔥 O termo de busca digitado pelo usuário
                                especialidade_id: especialidadeId,  // 🔥 Passamos o ID da especialidade
                                page: params.page || 1  // 🔥 Paginação
                            };
                        },
                        processResults: function (data) {
                            return {
                                results: data.results.map(proc => ({id: proc.id, text: proc.nome}))
                            };
                        }
                    }
                });
            }

            especialidadeField.change(configurarSelect2);
        });
    });
})();
