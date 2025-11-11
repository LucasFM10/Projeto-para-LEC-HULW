# Gestor de Fila Cirúrgica (LEC · HULW)

Painel e ferramentas para gestão da lista de espera cirúrgica do HULW (LEC). Este projeto é uma aplicação Django que oferece administração da fila cirúrgica, importadores para dados legados (LEC), APIs internas e páginas públicas de consulta.

---

## Badges

[![Build status](https://img.shields.io/badge/build-unknown-lightgrey.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-See_LICENSE-blue.svg)](LICENSE)

> Observação: substitua o badge de build pelo badge do CI que você usa (GitHub Actions, GitLab CI, etc.).

## O que o projeto faz

- Administra listas de espera cirúrgicas, pacientes, procedimentos e especialidades.
- Fornece dashboards e indicadores (sem expor dados sensíveis publicamente).
- Inclui utilitários para importar e compatibilizar dados legados do LEC (CSV) e scripts para gerar modelos a partir desses dados.

Apps principais:

- `fila_cirurgica/` — regras, modelos e admin da fila.
- `portal/` — formulários e views para operadores e equipe clínica.
- `externo/` — endpoints e páginas públicas para consulta (posições, indicadores).
- `lec_legado/` — ferramentas para importar e mapear dados legados.

## Por que é útil

- Automatiza a gestão operacional da fila cirúrgica.
- Centraliza indicadores e histórico para apoio à decisão.
- Facilita migração de bases legadas por meio de scripts de importação.
- Estrutura Django padrão, fácil de manter e estender.

## Pré-requisitos

- Python 3.10+ (compatibilidade típica com Django 4.x / 3.x — ver `requirements.txt`).
- Node.js + npm (apenas se você for compilar assets frontend com Tailwind/PostCSS).
- Banco de dados: SQLite é usado por padrão para desenvolvimento (`db.sqlite3` presente), mas configure `DATABASES` para produção.

## Como começar (rápido)

Clone o repositório e entre no diretório do projeto:

```bash
git clone <repo>
cd Projeto-para-LEC-HULW
```

Configurar ambiente Python e instalar dependências:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Instalar dependências de frontend (opcional, para compilar CSS/JS):

```bash
npm install
# npm run build  # se definido em package.json
```

Inicializar banco e rodar servidor de desenvolvimento:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver
```

Abra http://127.0.0.1:8000/ e acesse a área administrativa em `/admin/`.

Configuração principal: `gestor_fila_hulw/settings.py`.

> Em produção, ajuste `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, e `DATABASES`.

## Importando dados LEC (CSV legado)

O repositório inclui scripts e comandos de management para gerar modelos e importar arquivos CSV do LEC.

- Script para gerar modelos a partir de um CSV de legado:
  - `scripts/gerar_lec_legado_models.py`
- Command para importação:
  - `lec_legado/management/commands/import_lec_csv.py`

Exemplo de uso do management command:

```bash
python manage.py import_lec_csv path/to/df_lec_final_tratado.csv --replace --max-len 0
```

Consulte o código em `lec_legado/` para detalhes de configuração e opções do comando.

## Estrutura selecionada do repositório

- `manage.py` — entrypoint Django.
- `gestor_fila_hulw/settings.py` — configurações principais.
- `fila_cirurgica/`, `portal/`, `externo/`, `aih/`, `lec_legado/` — apps do domínio.
- `scripts/` — utilitários (ex.: `gerar_lec_legado_models.py`).
- `db.sqlite3` — banco de desenvolvimento (opcionalmente presente).
- `Procfile` — exemplo de entrada para Heroku/Gunicorn.

## Testes

Executar a suíte de testes Django:

```bash
python manage.py test
```

Os testes estão distribuídos por app (ex.: `aih/tests.py`, `externo/tests.py`, `lec_legado/tests.py`).

## Como contribuir (resumo)

1. Abra uma issue para discutir alterações significativas.
2. Crie um branch a partir de `main`/`master`.
3. Adicione testes para novas funcionalidades/bugs.
4. Faça PRs pequenos e atômicos; descreva a motivação e mudanças no título/descritivo.

Para diretrizes formais, adicione um `CONTRIBUTING.md` no repositório e links aqui. Atualmente referencie `CONTRIBUTING.md`:

- `docs/CONTRIBUTING.md` (se criado)
- `CONTRIBUTING.md` (arquivo na raiz)

## Onde obter ajuda

- Abra uma issue neste repositório.
- Consulte o código-fonte e templates nas pastas dos apps.
- Logs de execução: saída de `runserver`/`gunicorn` e logs do CI.

## Mantenedores

- Repositório mantido por: equipe do projeto (NIR / HULW). Para contato interno, procure o responsável técnico listado nos metadados do projeto.

Se quiser adicionar contatos públicos ou e-mails, crie `MAINTAINERS.md` e referencie aqui.

## Notas de segurança e privacidade

- O projeto lida com dados clínicos sensíveis. Em produção, verifique conformidade com LGPD e políticas locais. Evite expor dados pessoais em endpoints públicos.

---

Se quiser, posso também criar um `CONTRIBUTING.md` e um `MAINTAINERS.md` esboço curto para acompanhar este README.
