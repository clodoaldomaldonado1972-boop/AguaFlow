# AguaFlow — Checklist MVP
**Data:** 2026-05-14 | **Versão:** 1.2.0 | **Condomínio:** Vivere Prudente

---

## ROTAS / NAVEGAÇÃO

| Rota | View | No Roteador | Botão no Menu | Status |
|---|---|---|---|---|
| `/` | auth.py | ✅ | — | ✅ Funcional |
| `/registro` | autenticacao.py | ✅ | link no login | ✅ Funcional |
| `/esqueci_senha` | auth.py | ✅ | link no login | ✅ Funcional |
| `/recuperar-email` | recuperar_senha_email.py | ✅ | via esqueci_senha | ⚠️ redirect_to aponta para localhost |
| `/menu` | menu_principal.py | ✅ | — | ✅ Funcional |
| `/medicao` | medicao.py | ✅ | ✅ Medir Agora | ✅ Funcional |
| `/scanner` | scanner_view.py | ✅ | ✅ Scanner | ✅ Funcional |
| `/sincronizar` | sincronizacao.py | ✅ | ✅ Sincronizar Dados | ✅ Funcional |
| `/dashboard_saude` | dashboard_saude.py | ✅ | ✅ (admin) | ✅ Funcional |
| `/usuarios` | gerenciamento_usuarios.py | ✅ | ✅ (admin) | ✅ Funcional |
| `/relatorios` | relatorio_view.py | ✅ | ✅ (admin) | ✅ Funcional |
| `/configuracoes` | configuracoes.py | ✅ | ✅ Configurações | ✅ Funcional |
| `/sobre` | sobre_view.py | ✅ | ❌ sem botão | ⚠️ Inacessível pelo menu |
| `/ajuda` | ajuda_view.py | ❌ | ❌ | ❌ View existe mas não registrada |
| `/historico` | historico.py | ❌ | ❌ | ❌ View existe mas não registrada |
| `/dashboard` | dashboard.py | ❌ | ❌ | ❌ View existe mas não registrada |
| `/qrcodes` | qrcodes_view.py | ❌ | ❌ | ❌ View existe mas não registrada |

---

## FUNCIONALIDADES CORE

### Autenticação
- [x] Login online (Supabase Auth)
- [x] Login offline (fallback SQLite)
- [x] Logout com confirmação
- [x] Registro de novo usuário
- [x] Esqueci minha senha (e-mail de reset)
- [ ] Redirect pós-reset aponta para `localhost:8550` — deve usar URL de produção

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
- [x] OCR validado em 3 fotos reais: `32.89→328.936`, `2673`, `23087`

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
- [ ] **Registrar rotas ausentes** no roteador (`main.py`): `/ajuda`, `/historico`, `/dashboard`, `/qrcodes`
- [ ] **Adicionar botão "Sobre"** no menu principal (rota `/sobre` existe mas inacessível)
- [ ] **Corrigir `redirect_to`** em `recuperar_senha_email.py`: substituir `localhost:8550` pela URL de produção do app

### Importante
- [ ] **Botões de acesso** para `/ajuda` e `/historico` no menu (usuários comuns não têm como chegar lá)
- [ ] **Testar `/usuarios` e `/relatorios`** logado como admin para confirmar carregamento sem erro
- [ ] **Testar `/sincronizar`** manual via UI após as correções do sync_service

### Melhorias
- [ ] Deprecation warning: `ft.app()` → `ft.run()` (main.py:154)
- [ ] `DeprecationWarning` no Flet 0.84 — considerar atualização para 0.90+
- [ ] QR codes nas fotos do scanner: atualmente apenas leitura do display; considerar compor QR+hidrômetro em uma única captura

---

## TESTES REALIZADOS HOJE (2026-05-14)

| Teste | Resultado |
|---|---|
| Login online (Supabase) | ✅ OK |
| Login offline (fallback) | ✅ OK |
| Scanner: captura webcam | ✅ OK |
| Scanner: upload Storage | ✅ OK |
| OCR 156-gas.jpg | ✅ 328.936 (corrigido de 32.89) |
| OCR 161-agua.jpg | ✅ 2673 |
| OCR 162-agua.jpg | ✅ 23087 |
| Sync automático no boot | ✅ OK (sem erros) |
| Sync: unidade 101 → Supabase | ✅ HTTP 201 |
| Edge Function deploy | ✅ OK |
| Secrets ANTHROPIC_API_KEY | ✅ Configurado |

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
