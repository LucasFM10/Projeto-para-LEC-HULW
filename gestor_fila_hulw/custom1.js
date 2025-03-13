function getCSRFToken() {
  let tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
  return tokenElement ? tokenElement.value : "";
}

document.addEventListener('DOMContentLoaded', function () {
  django.jQuery(function ($) {
      console.log("Script carregado e jQuery disponível!");

      $('#id_procedimento').on('change', function () {
          var procedimentoId = $(this).val();
          console.log("Procedimento alterado! ID:", procedimentoId);

          if (procedimentoId) {
              var baseUrl = window.location.origin;
              var url = `${baseUrl}/fila_cirurgica/get_especialidade/${procedimentoId}/`;

              console.log("Fazendo requisição para:", url);

              $.ajax({
                  url: url,
                  method: "POST",
                  headers: {
                      "X-CSRFToken": getCSRFToken()  
                  },
                  success: function (data) {
                      console.log("Resposta recebida:", data);

                      var especialidadeField = $('#id_especialidade');
                      var especialidadeId = data.especialidade_id || "";
                      var especialidadeNome = data.especialidade_nome || "Especialidade Desconhecida"; 

                      // 🔥 Remove qualquer opção existente antes de adicionar a nova
                      especialidadeField.find('option').remove();

                      // 🔥 Adiciona a nova opção dinamicamente ao `select2`
                      especialidadeField.append(new Option(especialidadeNome, especialidadeId, true, true));

                      // 🔥 Atualiza o `select2` para refletir a mudança
                      especialidadeField.trigger("change.select2");
                  },
                  error: function (jqXHR, textStatus, errorThrown) {
                      console.error("Erro ao buscar especialidade:", textStatus, errorThrown);
                      console.error("Código de status HTTP:", jqXHR.status);
                      console.error("Resposta completa do servidor:", jqXHR.responseText);
                  }
              });
          }
      });
  });
});
