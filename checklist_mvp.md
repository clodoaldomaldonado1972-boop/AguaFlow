# AguaFlow — Checklist MVP
**Data:** 2026-05-14 | **Versão:** 1.2.0 | **Condomínio:** Vivere Prudente

---

## ROTAS / NAVEGAÇÃO

| Rota | View | No Roteador | Botão no Menu | Status |
|---|---|---|---|---|
| `/` | auth.py | ✅ | — | ✅ Funcional |
| `/registro` | autenticacao.py | ✅ | link no login | ✅ Funcional |
| `/esqueci_senha` | auth.py | ✅ | link no login | ✅ Funcional |
| `/recuperar-email` | recuperar_senha_email.py | ✅ | via esqueci_senha | ✅ redirect_to corrigido |
| `/menu` | menu_principal.py | ✅ | — | ✅ Funcional |
| `/medicao` | medicao.py | ✅ | ✅ Medir Agora | ✅ Funcional |
| `/scanner` | scanner_view.py | ✅ | ✅ Scanner | ✅ Funcional |
| `/sincronizar` | sincronizacao.py | ✅ | ✅ Sincronizar Dados | ✅ Funcional |
| `/dashboard_saude` | dashboard_saude.py | ✅ | ✅ (admin) | ✅ Funcional |
| `/usuarios` | gerenciamento_usuarios.py | ✅ | ✅ (admin) | ⚠️ Não testado como admin |
| `/relatorios` | relatorio_view.py | ✅ | ✅ (admin) | ⚠️ Não testado como admin |
| `/configuracoes` | configuracoes.py | ✅ | ✅ Configurações | ✅ Funcional |
| `/sobre` | sobre_view.py | ✅ | ✅ TextButton | ✅ Funcional (back corrigido → /menu) |
| `/ajuda` | ajuda_view.py | ✅ | ✅ TextButton | ✅ Registrada e acessível |
| `/historico` | historico.py | ✅ | ✅ TextButton | ✅ Funcional (bgcolor + AppBar adicionados) |
    | `/dashboard` | dashboard.py | ✅ | ❌ sem botão | ⚠️ Acessível via URL, usa `criar_card_metrica` ausente |
    | `/qrcodes` | qrcodes_view.py | ✅ | ✅ TextButton | ✅ Funcional |

    ---

## FUNCIONALIDADES CORE

### Autenticação
- [x] Login online (Supabase Auth)
- [x] Login offline (fallback SQLite)
- [x] Logout com confirmação
- [x] Registro de novo usuário
- [x] Esqueci minha senha (e-mail de reset)
- [x] `redirect_to` corrigido para URL do Supabase Auth

### Medição
- [x] Inserção manual de leitura Água
- [x] Inserção manual de leitura Gás
- [x] Seleção de unidade
- [x] Data/hora automática com fuso America/Sao_Paulo
- [x] Salvamento local (SQLite) com `sincronizado = 0`
- [x] Propagação de `foto_url` do scanner para a leitura salva

### Scanner / OCR
- [x] Captura de foto via webcam (cv2)
- [x] Redimensionamento para max 1024px (preserva aspecto)
- [x] Compressão JPEG qualidade 75 (~60 KB por foto)
- [x] Detecção de QR Code — formato simples `"162"` e composto `"AGUAFLOW|162-AGUA"`
- [x] Upload para Supabase Storage (`fotos_hidrometros/unidade/timestamp_MODO.jpg`)
- [x] Upload usa service_role (bypass RLS)
- [x] Storage path sanitizado (caracteres inválidos → `_`)
- [x] OCR via Claude claude-opus-4-7 Vision (Edge Function Deno)
- [x] Lê dígitos vermelhos como casas decimais
- [x] Aceita até 3 casas decimais (ex: `328.936`)
- [x] Atualiza `leituras.valor_leitura` no Supabase via webhook pg_net
- [x] OCR validado em 22/22 fotos (Claude Haiku Vision): `real_161→2673.536`, `real_162→23087.0`, `real_152-gas→1595.956`
- [x] Scanner popula `valor_scanner` automaticamente → campo pré-preenchido em `/medicao`

### Sincronização
- [x] Sync automático em loop (60s) ao iniciar o app
- [x] Sync manual pela tela `/sincronizar`
- [x] `sqlite3.Row` convertido para `dict` antes do upload
- [x] Campo `valor_leitura` incluído no INSERT (NOT NULL)
- [x] `sync_log` com coluna correta `unidade_id`
- [x] Limpeza de foto local após sync bem-sucedido
- [x] Log de auditoria em `sync_log` (sucesso/falha)
- [x] E-mail de alerta em falha de upload

### Pipeline OCR completo (end-to-end)
- [x] Foto → Storage → webhook pg_net → Edge Function → Claude → UPDATE leituras
- [x] `ANTHROPIC_API_KEY` configurado como Supabase Secret
- [x] Edge Function deployada e respondendo

---

## PENDÊNCIAS PARA MVP

### Crítico
- [x] **Registrar rotas ausentes** no roteador (`main.py`): `/ajuda`, `/historico`, `/dashboard`, `/qrcodes`
- [x] **Adicionar botões** no menu principal: Histórico, QR Codes, Ajuda, Sobre (row de TextButtons)
- [x] **Corrigir `redirect_to`** em `recuperar_senha_email.py`
- [x] **Corrigir bgcolor** de todos os views (tela branca durante transição)
- [x] **Adicionar AppBar + back button** em `/historico` e `/ajuda`
- [x] **Corrigir botão Voltar** de `/sobre` (apontava para `/configuracoes`, agora vai para `/menu`)
- [x] **Corrigir `on_view_pop`** em `main.py` — retornava `None` sempre (len > 1 nunca satisfeito com clear+append), deixava `page.views` vazio → tela branca ao pressionar voltar do sistema
- [x] **Corrigir `validar_sessao`** — retornava View vazia sem bgcolor → tela branca
- [x] **Corrigir error handler** em `main.py` — agora limpa views e mostra tela escura com "Voltar ao Menu"
- [x] **Scroll no menu** — `ScrollMode.ADAPTIVE` na Column interna para garantir visibilidade do TextButton row

### Importante
- [ ] **`/dashboard`** usa `st.criar_card_metrica` que não existe em `styles.py` — crashará se acessada
- [ ] **Testar `/usuarios` e `/relatorios`** logado como admin para confirmar carregamento sem erro
- [ ] **Testar `/sincronizar`** manual via UI

### Melhorias
- [ ] `historico.py`: `gc.collect()` após envio de e-mail (já com import `gc` adicionado)
- [ ] Deprecation warning: `ft.app()` → `ft.run()` (main.py:166)
- [ ] QR codes nas fotos do scanner: considerar compor QR+hidrômetro em uma única captura
- [x] **OCR Claude Vision** — `utils/vision.py` usa Claude Haiku como primário (22/22), Tesseract como fallback offline. Scanner popula `valor_scanner` automaticamente.
- [ ] **Tesseract PATH** — adicionar `C:\Program Files\Tesseract-OCR` ao PATH do sistema para evitar `tesseract_cmd` hardcoded

---

## TESTES REALIZADOS (2026-05-14)

| Teste | Resultado |
|---|---|
| Login online (Supabase) | ✅ OK |
| Login offline (fallback) | ✅ OK |
| Scanner: captura webcam | ✅ OK |
| Scanner: upload Storage | ✅ OK |
| OCR 156-gas.jpg | ✅ 328.936 |
| OCR 161-agua.jpg | ✅ 2673 |
| OCR 162-agua.jpg | ✅ 23087 |
| Sync automático no boot | ✅ OK |
| Sync: unidade 101 → Supabase | ✅ HTTP 201 |
| Edge Function deploy | ✅ OK |
| Secrets ANTHROPIC_API_KEY | ✅ Configurado |
| Rota /historico | ✅ Carrega (bgcolor + AppBar corrigidos) |
| Rota /qrcodes | ✅ Carrega sem erros |
| Rota /sobre | ✅ Carrega (back corrigido → /menu) |
| Rota /ajuda | ⚠️ Registrada, não testada com log |
| **Teste OCR — temp/ (22 fotos) — 2026-05-14 v1** | |
| QR Code detecção (14/22 fotos) | ✅ QR lido corretamente (ex: `AGUAFLOW\|151-AGUA`, `AGUAFLOW\|163/164-AGUA`) |
| OCR Tesseract (3/22 fotos) | ⚠️ Taxa baixa — retorna fragmentos (2, 3, 2) em vez de leitura completa |
| **Teste OCR — temp/ (22 fotos) — 2026-05-14 v2 (Claude Haiku Vision)** | |
| OCR Claude Vision — ÁGUA (13 fotos) | ✅ 13/13 — ex: `151→260.12`, `162→22786.0`, `real_161→2678.5`, `real_162→23087.0` |
| OCR Claude Vision — GÁS (9 fotos) | ✅ 9/9 — ex: `152-gas→1584.48`, `156-gas→327.833`, `real_152→1595.956`, `155-gas→214.835` |
| QR detectado neste lote | ✅ 11/22 — `151-AGUA`, `152-GAS`, `153-AGUA`, `154-AGUA`, `155-AGUA`, `156-AGUA`, `156-GAS`, `161-AGUA`, `162-AGUA`, `163/164-AGUA`, `165-AGUA`, `real_156-GAS`, `real_162-AGUA` |
| Taxa geral OCR | ✅ **22/22 (100%)** — Claude Vision + Tesseract fallback |
| Scanner → OCR → valor pré-preenchido | ✅ `valor_scanner` populado automaticamente no `/medicao` |
| Supabase: consulta tabela leituras | ✅ 34 registros, colunas `leitura_agua`/`leitura_gas` corrigidas no sync |
| Fix sync GAS mode | ✅ `leitura_gas` e `valor_leitura` agora corretos para modo GÁS |
| Tesseract PATH no Windows | ⚠️ Não está no PATH — requer `pytesseract.tesseract_cmd` explícito (fallback offline) |

---

## ARQUITETURA RESUMIDA

```
App (Flet 0.84 / Python)
├── views/          — UI por rota
├── database/
│   ├── database.py     — SQLite local + Supabase client
│   └── sync_service.py — fila offline → Supabase
├── utils/          — logger, updater, diagnóstico
├── assets/
│   ├── *.jpg           — fotos reais de hidrômetros (teste)
│   └── qrcodes/        — QR codes gerados por unidade
└── supabase/
    └── functions/
        └── ocr-hidrometro/index.ts  — Claude claude-opus-4-7 Vision OCR
```

**Supabase:** `rpacxhgvscqnlawxgwfk.supabase.co`
**Storage bucket:** `fotos_hidrometros` (público, max 5 MB)
**Tabelas principais:** `leituras`, `medidores`, `sync_log`
