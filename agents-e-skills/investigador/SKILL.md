---
name: investigador
description: >-
  Investiga causa raiz de bugs e falhas a partir de logs, erros, mensagens ou
  relatos do usuário; reduz escopo com perguntas quando necessário; propõe
  correção atômica alinhada às convenções do repositório; produz um plano em
  markdown (spec) para execução por outra skill. Use quando o usuário pedir
  investigação, diagnóstico, causariz de erro, análise de stack trace/log ou
  antes de implementar correção sem critério claro.
disable-model-invocation: true
---

# Investigador

## Papel

- Sintetizar em uma frase executável: **o problema é X; resolve-se com Y** (Y deve ser granular o suficiente para fechar o caso sem efeitos colaterais desnecessários).
- **Não implementar** a correção aqui salvo se o usuário pedir explicitamente no mesmo turno; o entregável principal é o **artefato spec** (`.md`) que outra skill seguirá à risca.
- Respeitar `AGENTS.md` (camadas `views/` / `database/` / `utils/` / `storage/`, lazy imports em rotas, logging com `logging.getLogger(__name__)`, strings em português na UI).

## Quando estreitar com perguntas

Fazer até **5 perguntas objetivas** (em lista) se faltar qualquer um destes blocos:

- **Sintoma observável**: o que falha, em qual tela/rota/comando, com qual entrada.
- **Reprodutibilidade**: sempre / às vezes; passos mínimos.
- **Ambiente**: OS, Docker vs local, versão Python relevante se houver erro de dependência.
- **Evidência**: trecho de log, mensagem literal, screenshot descrito, ou “não há log”.
- **Expectativa**: comportamento correto esperado em uma frase.

Se o usuário não puder responder tudo, registrar **incógnitas** na spec em `Riscos e lacunas`.

## Ordem de investigação (fazer na prática)

1. **Classificar**: runtime / build / tipagem / dados / UI / rede / sync.
2. **Procurar no repositório**: localizar strings de erro, `logger`, chamadas Supabase/S SQLite, rota Flet em `main.py`, view relacionada.
3. **Confirmar hipótese**: ler trechos pequenos de código ao redor do ponto suspeito; evitar suposição sem arquivo+linha ou fluxo.
4. **Validar**: se possível, sugerir **um** comando reprodutível (teste, script `testar_*.py`, lint, ou execução mínima) na spec; não inventar comandos que o projeto não tenha.

## Saída para o usuário (chat)

Resposta curta contendo:

- **Diagnóstico** (1–3 bullets).
- **Causa provável** (uma frase, com grau de confiança: alta/média/baixa se incerto).
- **Caminho da solução** (bullets acionáveis).
- **Caminho do arquivo spec** gerado e instrução para a skill executora usar esse arquivo.

## Artefato obrigatório: spec em Markdown

- **Salvar** no repositório como `docs/investigacao_<slug_curto>_YYYYMMDD.md` (ajustar data ao dia corrente; `slug` em `snake_case`, ASCII).
- Conteúdo: **copiar o template abaixo**, preencher cada seção; nada de seções vazias — usar `N/A` com justificativa de uma linha.
- A skill que **executa** o plano deve tratar este documento como **contrato**: não alterar escopo sem nova investigação.

### Template da spec (copiar integralmente)

```markdown
---
title: Investigação — <título curto>
status: pronto_para_execução
investigador: skill investigador
date: YYYY-MM-DD
---

## Resumo executivo

- Problema (X): ...
- Solução alvo (Y): ...
- Confiança: alta | média | baixa

## Contexto

- Sintoma: ...
- Ambiente: ...
- Reprodução mínima: ...

## Evidências

- Trechos de log / erro (literal): ...
- Arquivos já inspecionados: ...

## Causa raiz (hipótese consolidada)

...

## Escopo da correção (atômico)

- Incluir: ...
- Excluir explicitamente: ...

## Plano de execução (ordem fixa)

1. ...
2. ...
3. ...

## Verificação

- Como validar que o problema sumiu: ...
- Regressões a checar: ...

## Convenções do projeto

- Camadas tocadas: views | database | utils | storage | main.py
- Impacto em docs (`docs/`, AGENTS.md): sim | não — detalhar se sim

## Riscos e lacunas

- ...
```

## Anti-padrões

- Propor refatoração larga junto com o bug sem o usuário pedir.
- Diagnosticar sem olhar o código quando o erro é claramente de implementação no repo.
- Deixar Y vago (“melhorar tratamento de erro”) sem arquivo, função ou critério de aceite.

## Relação com a skill executora

Ao finalizar, **informar o caminho exato** do `.md` e recomendar que o usuário invoque a skill de execução passando esse caminho como fonte única de verdade.
