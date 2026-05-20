---
title: Investigação — Botões QR Água/Gás invisíveis em Relatórios
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-19
---

## Resumo executivo

- Problema (X): Os botões "QR ÁGUA" e "QR GÁS" na tela `/relatorios` nunca aparecem no desktop porque `EXPORT_AVAILABLE = False` em tempo de importação — `reportlab` não está instalado no ambiente.
- Solução alvo (Y): Instalar `reportlab` no `.venv` e documentar no `requirements.txt` com instrução clara de que deve ser instalado apenas no desktop (não compilar no APK).
- Confiança: alta

## Contexto

- Sintoma: Menu Relatórios não exibe os botões "QR ÁGUA" e "QR GÁS".
- Ambiente: Windows 11 desktop, plataforma `windows` confirmada no log (`platform: 'windows'`, linha 8 do log). Python com `.venv` em `C:\AguaFlow\.venv`.
- Reprodução mínima: Abrir o app → navegar para `/relatorios` → seção "IMPRESSÃO DE ETIQUETAS (50/FOLHA)" não mostra os dois botões.

## Evidências

- Trechos de log relevantes:
  - `2026-05-19 19:49:12,511 [INFO] database.database: 🖥️ Desktop detectado` — confirma ambiente desktop.
  - `2026-05-19 19:52:33,202 [DEBUG] __main__: 🛣️ Rota acessada: /relatorios` — rota acessada com sucesso.
  - Nenhum log de erro de importação (silencioso: bloco `try/except ImportError` sem logging).
- Resultado de `pip show reportlab`: `WARNING: Package(s) not found: reportlab`.
- Resultado de `pip show qrcode`: instalado (v8.2). Resultado de `pip show pillow`: instalado (v12.2.0).
- Arquivos inspecionados:
  - `views/relatorio_view.py` — linha 206: `visible=EXPORT_AVAILABLE`
  - `utils/export_manager.py` — linhas 6–14: flag definida por `try/except ImportError`
  - `requirements.txt` — linha 14: `# reportlab` (comentado intencionalmente para evitar falha no build do APK)

## Causa raiz (hipótese consolidada)

`requirements.txt` tem `reportlab` comentado (`# reportlab`) para não quebrar o build do APK com `buildozer`. Quando o desenvolvedor executa `pip install -r requirements.txt` no desktop, `reportlab` não é instalado. Consequentemente `EXPORT_AVAILABLE = False` em `export_manager.py` e o `ft.Row` com os dois botões fica `visible=False` permanentemente — os botões somem sem nenhuma mensagem explicativa ao usuário.

## Escopo da correção (atômico)

- Incluir:
  1. Instalar `reportlab` no `.venv` local (comando único).
  2. Atualizar `requirements.txt` para documentar claramente que `reportlab` é desktop-only e deve ser instalado manualmente.
  3. (Opcional, desejável) Melhorar UX: mostrar os botões sempre, mas exibir `SnackBar` com instrução de instalação se `EXPORT_AVAILABLE = False` ao clicar — em vez de esconder os botões silenciosamente.
- Excluir explicitamente:
  - Alterações no `buildozer.spec`.
  - Alterações nas funções de geração de PDF/QR (o código já está correto).
  - Qualquer refatoração da view além do visível/UX dos botões.

## Plano de execução (ordem fixa)

1. **Instalar `reportlab` no ambiente atual:**
   ```
   pip install reportlab
   ```
2. **Atualizar `requirements.txt`** — substituir a linha comentada por um bloco explicativo:
   ```
   # reportlab — SOMENTE DESKTOP; instalar manualmente: pip install reportlab
   # NÃO incluir no APK (buildozer não suporta compilação desta lib)
   # reportlab
   ```
3. **(Opcional — melhorar UX)** Em `views/relatorio_view.py`, trocar o `visible=EXPORT_AVAILABLE` no `ft.Row` por `visible=True` e adicionar guard dentro de `acao_gerar_qrs` para exibir `SnackBar` informativa se `not EXPORT_AVAILABLE`. Remover o `ft.Text` de aviso desktop que aparece separado.

## Verificação

- Como validar que o problema sumiu: Reiniciar o app após `pip install reportlab` → navegar para `/relatorios` → os dois botões "QR ÁGUA" e "QR GÁS" devem aparecer visíveis abaixo do divisor "IMPRESSÃO DE ETIQUETAS (50/FOLHA)".
- Regressões a checar: Clicar em "QR ÁGUA" deve gerar o PDF em `etiquetas/Etiquetas_50_Agua.pdf` sem erros. Clicar em "EXECUTAR VIRADA DE CICLO" e "GERAR RELATÓRIO" não devem ser afetados.

## Convenções do projeto

- Camadas tocadas: `views/relatorio_view.py`, `requirements.txt`
- Impacto em docs: não — nenhum AGENTS.md precisa ser alterado

## Riscos e lacunas

- Se o step 3 (melhoria de UX) for implementado, testar no ambiente Android (APK) para garantir que o `SnackBar` aparece corretamente quando `EXPORT_AVAILABLE = False` em vez dos botões ocultos.
- `qrcode` v8.2 instalado via `flet-cli` como dependência indireta — se o `flet-cli` for removido no futuro, verificar se `qrcode` precisa ser declarado explicitamente no `requirements.txt`.
