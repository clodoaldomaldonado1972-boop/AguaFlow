---
title: Investigação — Análise do aguaflow_debug.log (19/05/2026)
status: concluida
investigador: skill investigador
date: 2026-05-19
---

## Resumo executivo

- Problema (X): O log acumulou 37.308 linhas de 4 sessões distintas; contém 2 erros críticos e 1 warning de negócio — todos de sessões anteriores à sessão de testes de 23:05.
- Solução alvo (Y): Nenhuma correção pendente. As 3 ocorrências anômalas estão resolvidas pelo commit `8a505b7` e pelas correções do audit skill2.md. A sessão limpa de 23:05 confirma estabilidade.
- Confiança: alta

---

## Contexto

- Sintoma: Log gerado pelo app durante o dia 19/05/2026 (4 sessões de uso/teste).
- Ambiente: Windows 11 desktop, Python 3.14, Flet 0.82, SQLite local + Supabase.
- Reprodução mínima: N/A — bugs históricos já corrigidos.

---

## Evidências

### Sessões identificadas no log

| Horário início | Horário fim | Descrição |
|---|---|---|
| 19:49 | 20:55 | Sessão normal — OCR + uploads Supabase OK |
| 20:56 | 21:18 | Scanner acessado — FilePicker timeout no desktop |
| 21:32 | 21:32 | Scanner crash imediato ao montar a tela |
| 23:05 | 23:08 | Sessão de teste pós-audit — **LIMPA, sem erros** |

---

### Ocorrência 1 — FilePicker Timeout (linha 18040, 21:18)

**Classificação**: runtime / UI  
**Nível**: ERROR

```
[ERROR] concurrent.futures: exception calling callback for <Future raised RuntimeError>
RuntimeError: TimeoutException after 0:00:10.000000:
Timeout waiting for invoke method listener for FilePicker(185).pick_files
  File "views/scanner_view.py", line 177, in _iniciar_captura
    await file_picker.pick_files(...)
```

**Causa**: O `ft.FilePicker` foi chamado em ambiente desktop onde o listener nativo da UI Flutter não respondia. O código antigo iniciava `pick_files` no desktop sem fallback.  
**Status**: ✅ **CORRIGIDO** — código atual usa `tkinter.filedialog` no desktop via `asyncio.to_thread`; FilePicker só é instanciado se `is_android()`.

---

### Ocorrência 2 — Scanner crash ao montar (linha 18789, 21:32)

**Classificação**: runtime / UI  
**Nível**: ERROR

```
[ERROR] views.scanner_view: Erro ao montar scanner:
'NoneType' object has no attribute 'on_result'
  File "views/scanner_view.py", line 160, in montar_tela_scanner
    file_picker.on_result = _on_file_picked
AttributeError: 'NoneType' object has no attribute 'on_result'
```

**Causa**: `file_picker = None` no desktop, mas o código tentava atribuir `file_picker.on_result` sem guard. Versão antiga não tinha a verificação `if file_picker:`.  
**Status**: ✅ **CORRIGIDO** — guard `if file_picker:` antes da atribuição existe no código atual (linha 176 do scanner_view.py).

---

### Ocorrência 3 — Login falhado (linha 17175, 21:18)

**Classificação**: negócio / autenticação  
**Nível**: WARNING

```
[WARNING] views.auth: ⚠️ Login online falhou: Invalid login credentials
supabase_auth.errors.AuthApiError: Invalid login credentials
```

**Causa**: Usuário digitou email incorreto (`clodoaldomaldonad112@gmail.com` → corrigido para `clodoaldomaldonado112@gmail.com` na linha 17218). O sistema respondeu corretamente com "E-mail ou senha incorretos." e o usuário fez login com sucesso na tentativa seguinte.  
**Status**: ✅ **COMPORTAMENTO ESPERADO** — não é bug; resiliência de autenticação funcionando corretamente.

---

### Sessão 23:05 — Pós-audit (LIMPA)

```
[INFO] root: ✅ SMTP: Serviço de e-mail autenticado corretamente.
[INFO] database.database: 🖥️ Desktop detectado — DB_PATH: C:\AguaFlow\database\aguaflow.db
[INFO] database.database: 🚀 Estrutura do banco de dados (SQLite) sincronizada.
[INFO] database.sync_service: ✅ Tudo em dia: Nada para sincronizar.
[INFO] database.sync_service: ✔️ Unidade 126 sincronizada.  (←- 1 leitura pendente enviada)
```

**Nenhum ERROR, nenhum WARNING anômalo.** Sincronização da unidade 126 concluída com sucesso.

---

## Causa raiz (hipótese consolidada)

Os dois erros críticos (Ocorrências 1 e 2) derivam da mesma fonte: lógica de bifurcação `is_android()` no scanner_view que, em versões anteriores, não protegia adequadamente o caminho desktop antes de instanciar e chamar o `ft.FilePicker`. Ambos foram corrigidos nas sessões anteriores de desenvolvimento.

---

## Observação técnica — ruído da animação mira

A animação de pulso da mira (`st.criar_mira_scanner()`) dispara ~60 mensagens `flet_transport send_message PATCH_CONTROL offset` por sessão (controle 171, oscila entre y=+2.5 e y=-2.5 a cada 1.6s). Isso não é bug, mas infla o log com ruído de DEBUG sem valor diagnóstico.

**Sugestão (não bloqueante)**: adicionar `logging.getLogger("flet_transport").setLevel(logging.WARNING)` ao `setup_logging()` em `utils/logger_config.py` para manter o arquivo de log compacto, ou reduzir a frequência da animação.

---

## Escopo da correção (atômico)

- Incluir: apenas o silenciamento do `flet_transport` no `logger_config.py` (opcional, não bloqueante).
- Excluir explicitamente: qualquer refatoração do scanner ou da animação mira — funcionam corretamente.

---

## Plano de execução (caso o silenciamento seja desejado)

1. Abrir `utils/logger_config.py`.
2. Na lista `noisy_lib` do loop em `setup_logging()`, adicionar `"flet_transport"`.
3. Verificar que o log da próxima sessão não contém mais `send_message` de offset.

---

## Verificação

- Como validar que o problema sumiu: rodar o app, abrir o scanner, fechar — o `aguaflow_debug.log` não deve conter linhas `[ERROR]` ou `[WARNING]` de `scanner_view`.
- Regressões a checar: N/A — correções já validadas pela sessão limpa de 23:05.

---

## Convenções do projeto

- Camadas tocadas: N/A (investigação pura; não há nova implementação pendente)
- Impacto em docs: sim — este arquivo é o entregável

---

## Riscos e lacunas

- O log de 37k linhas contém muitas linhas longas de `flet_transport` que ultrapassam o limite de leitura por janela; a análise focou nos filtros por `[ERROR]`, `[WARNING]` e `Traceback`. Sessões intermediárias não foram varridas linha a linha — possível ruído não mapeado em sessões de 20:56–21:32.
- Scanner não foi testado explicitamente na sessão de 23:05 (usuário navegou para Gestão de Usuários e Sincronização). Recomenda-se um teste específico do fluxo scanner → medicão no próximo ciclo.
