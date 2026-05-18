# AGENTS.md — AguaFlow

Ponto de entrada para agentes e humanos: onde está a documentação, como o código está organizado e quais regras manter ao evoluir o projeto.

## Visão geral

- **Produto:** aplicativo de digitalização / leitura de hidrômetros (fluxo offline-first com SQLite e caminho de nuvem Supabase).
- **Stack principal:** Python 3, **Flet** (`requirements.txt`, alvo ~0.84+), SQLite (`database/`), Supabase (cliente e sync onde aplicável).
- **Princípio arquitetural:** o projeto é **modular por pastas de responsabilidade**; novas funcionalidades devem **reforçar** esse desenho (evitar “god files” na raiz e lógica de domínio dentro de views).

## Documentação (localização)

| Área | Caminho |
|------|---------|
| Checklist MVP / escopo técnico | `docs/CHECKLIST_MVP.md` (espelho histórico em `CHECKLIST_MVP.py` / raiz conforme versão) |
| Status de integridade / estrutura (referência) | `docs/STATUS_INTEGRIDADE.md` |
| Relatório de checkout / decisões recentes | `docs/CHECKOUT.md` |
| Checkout resumido | `CHECKOUT_MVP.md` |
| Checklists operacionais | `docs/CHECKLIST_STATUS.md` |
| QA | `docs/RELATORIO_QA_2026-04-19.md` |
| Gitignore / artefatos | `docs/GITIGNORE_RELATORIO.md` |
| Gerador de checklist (ferramenta auxiliar) | `docs/checklist-generator/README.md`, `docs/checklist-generator/generate_checklist.py` |

Ao atualizar o comportamento do app ou da infraestrutura, **alinhe ou cite** o doc correspondente em `docs/` para não divergir do que o time trata como fonte de verdade.

## Mapa de módulos (pastas)

- **`main.py`** — Orquestração: tema/página, **roteamento** (`page.route` → view), boot em background (DB/sync quando aplicável), tarefas periódicas leves. Imports de views preferencialmente **preguiçosos** dentro do handler de rota para reduzir acoplamento e custo de startup.
- **`views/`** — **UI Flet**: telas, composição de controles, navegação via `page.go`. Subpastas ou arquivos coesos (ex.: `views/components/` para pedaços reutilizáveis de tela). Não coloque regras de negócio pesadas aqui; delegue a `database/` ou `utils/`.
- **`database/`** — Persistência local (SQLite), esquema, operações transacionais, backup/reset/gestão de períodos, cliente Supabase e serviços de sync quando forem da camada de dados.
- **`utils/`** — Serviços transversais: logging, e-mail, OCR/visão, autenticação auxiliar, export, diagnóstico, etc. Funções puras ou classes pequenas com responsabilidade única.
- **`storage/`** — Arquivos gerados ou pipeline de mídia (ex.: fotos, exports) alinhado ao uso em Docker (`./storage` montado em volume).

Scripts pontuais na **raiz** (`testar_*.py`, `setup_*.py`, etc.) são aceitáveis como ferramentas; **não** misture esse código com o fluxo principal sem extrair para `utils/` ou `database/` quando virar permanente.

## Convenções de nomenclatura

- **Arquivos Python:** `snake_case.py`.
- **Views:** preferir nomes que indiquem a tela (`medicao.py`, `menu_principal.py`). Quando for uma tela “nomeada” de produto, o padrão `*_view.py` já aparece no projeto (`sobre_view.py`, `scanner_view.py`, `relatorio_view.py`) — **seja consistente** com o arquivo mais parecido na mesma pasta.
- **Funções de montagem de tela:** prefixo `montar_tela_*` ou `criar_tela_*`, retornando **`ft.View`** (padronização descrita em `docs/CHECKOUT.md`).
- **Classes:** `PascalCase` (ex.: `Database` em `database/database.py`).
- **Strings de interface:** português, alinhado ao domínio do condomínio/usuários finais.
- **Logs:** módulos usam `logging.getLogger(__name__)` com configuração central em `utils/logger_config.py`.

## Como criar um novo módulo (checklist)

1. **Definir a camada:** UI → `views/`; persistência → `database/`; serviço compartilhado → `utils/`; arquivos ou fluxo de mídia → `storage/`.
2. **Evitar dependências circulares:** não importar `main.py` a partir de views/utils/database; o fluxo é **unidirecional** em direção às bibliotecas internas (documentado implicitamente em `docs/CHECKOUT.md`).
3. **Nova rota:** adicionar ramo em `main.py` em `route_change`, import lazy da view, e usar `page.views` / `page.go("/rota")` no mesmo estilo das rotas existentes.
4. **Sessão / auth:** reutilizar padrões de `utils/auth_utils.py` e telas em `views/auth.py` / `views/autenticacao.py` em vez de duplicar checagens.
5. **Estilo visual:** reutilizar `views/styles.py` e padrões já usados no menu e telas correlatas.
6. **Configuração secreta:** variáveis via `.env` (ex.: Supabase), sem commit de credenciais; `load_dotenv()` já é usado na camada adequada (`database/database.py`).

## Boas práticas herdadas da documentação interna

- **Validação em camadas** para dados críticos (ex.: entrada numérica no app + constraints SQL), conforme narrativa em `docs/CHECKLIST_MVP.md`.
- **Backup e integridade:** manter consciência de transações e recuperação onde o checklist MVP ainda aponta lacunas; alterações em `database/` devem preservar caminhos de DB e compatibilidade Docker (`docker-compose.yml` monta `./database`).
- **Navegação Flet:** não reintroduzir padrões obsoletos removidos no checkout (ex.: uso antigo de `page.go` como comando solto fora do modelo atual de rotas/views).
- **Testes rápidos:** scripts `testar_*.py` / `test_*.py` na raiz podem validar fluxos; ao adicionar cobertura formal, preferir nomes claros e dependências mínimas.

## Dependências e execução

- **Python:** `requirements.txt` na raiz.
- **Docker:** `Dockerfile` + `docker-compose.yml`; variável `IS_DOCKER=True` no serviço para ajuste de caminhos quando necessário.

## Manutenção deste arquivo

- Quando criar documentação nova relevante para agentes ou desenvolvedores, **adicione uma linha na tabela “Documentação”** acima e, se couber, **uma regra curta** na seção de módulos ou boas práticas.
- Se uma pasta ganhar nova responsabilidade permanente, atualize o **Mapa de módulos** para refletir o contrato da pasta (o que entra / o que não entra).
