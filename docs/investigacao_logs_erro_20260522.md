---
title: Investigação — logs de erro 22/05 + visibilidade OCR na medição
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-22
---

## Resumo executivo

- Problema (X): Três falhas encontradas nos logs e screenshot do dia 22/05: (1) aviso PGRST205 a cada OCR por tabela `ocr_log` ausente no Supabase; (2) pasta no Storage usando raw barcode — cria subpastas incorretas para unidades duplex ("163/164"); (3) valor preenchido pelo OCR no TextField de leitura tem cor insuficiente contra o fundo escuro.
- Solução alvo (Y): Suprimir WARNING PGRST205 em `utils/vision.py`; normalizar nome de pasta em `views/scanner_view.py` antes de chamar o upload; adicionar `color="white"` em `txt_agua` e `txt_gas` em `views/medicao.py`.
- Confiança: alta

## Contexto

- Sintoma 1: A cada OCR bem-sucedido, o log registra `WARNING Falha ao logar OCR: {'message': "Could not find the table 'public.ocr_log' in the schema cache", 'code': 'PGRST205'}`. Não afeta o funcionamento, mas polui os logs e pode ocultar erros reais.
- Sintoma 2: Fotos enviadas ao bucket `fotos_hidrometros` aparecem sob `AGUAFLOW_163/164-GAS/202605_GAS.jpg` (3 níveis) em vez de `163-164/202605_GAS.jpg`. Para unidades simplex a pasta fica `AGUAFLOW_161-AGUA/202605_AGUA.jpg` em vez de `161/202605_AGUA.jpg`.
- Sintoma 3: Screenshot 20:58:53 do APK 125 mostra valor `144,98` preenchido pelo OCR no campo "Leitura Água (m³)" em tom cinza quase indistinguível do placeholder no tema escuro (#121417). Usuário não consegue confirmar se o valor foi preenchido.
- Ambiente: Android APK 125 / Flet 0.82.2 / Python 3.12
- Reprodução mínima: (1) Escanear QR + tirar foto com internet → ver log. (2) Unidade 163/164 → ver pasta no Supabase Storage. (3) OCR retorna valor → ver campo na tela de medição.

## Evidências

- Log literal bug 1: `22/05 16:20:58 [WARNING] utils.vision: Falha ao logar OCR: {'message': "Could not find the table 'public.ocr_log' in the schema cache", 'code': 'PGRST205', 'hint': None, 'details': None}`
- Log literal bug 2: `📸 Foto enviada ao Supabase Storage: .../fotos_hidrometros/DESCONHECIDA/20260522_162058_AGUA.jpg` (log antigo, APK pré-125) e `AGUAFLOW_163/164-GAS/202605_GAS.jpg` (APK 125 com QR scanneado).
- Screenshot bug 3: `WhatsApp Image 2026-05-22 at 20.58.53.jpeg` — campo "Leitura Água (m³)" com `144,98` em cinza, inseparável do hint text visualmente.
- Arquivos inspecionados: `utils/vision.py` (L174–191), `database/database.py` (L583–620), `views/scanner_view.py` (L157–160), `views/medicao.py` (L193–216).

## Causa raiz (hipótese consolidada)

**Bug 1**: A função `_log_ocr_supabase()` (`utils/vision.py:181`) tenta `INSERT` na tabela `ocr_log` que não existe no projeto Supabase. O `except Exception` captura o erro PostgREST e loga como WARNING. A tabela nunca foi criada via migration.

**Bug 2**: Em `database.py:593`, `re.sub(r'[^a-zA-Z0-9_\-/]', '_', unidade)` mantém a barra `/` no charset permitido. Para `"AGUAFLOW|163/164-GAS"`, o resultado é `"AGUAFLOW_163/164-GAS"`, que vira um caminho com 3 níveis no bucket. O `|` e `-AGUA/-GAS` também ficam na string, gerando nomes longos e inconsistentes.

**Bug 3**: `txt_agua` e `txt_gas` em `medicao.py` não têm `color` definido. No tema escuro do Flet 0.82.2, o texto padrão do TextField pode renderizar em tom médio que se confunde com o hint text contra o fundo `#121417`.

## Escopo da correção (atômico)

- Incluir: `utils/vision.py` (suprimir PGRST205), `views/scanner_view.py` (normalizar unidade antes do upload), `views/medicao.py` (color="white" nos campos).
- Excluir explicitamente: criar tabela `ocr_log` no Supabase (fora do escopo — requer migration SQL separada); alterar lógica de OCR ou upload; mexer em `build_wsl.sh` ou Dart.

## Plano de execução (ordem fixa)

1. **`utils/vision.py` L190–191** — em `_log_ocr_supabase()`, no `except Exception as ex:`, verificar se `'PGRST205'` está em `str(ex)` e, se sim, logar em `DEBUG` em vez de `WARNING`. Elimina o ruído sem silenciar outros erros reais.

2. **`views/scanner_view.py` L157–159** — antes de `asyncio.create_task(_upload_background(...))`, normalizar `unidade_upload`:
   ```python
   unidade_raw = state.get("unidade") or "DESCONHECIDA"
   # Extrai número limpo: "AGUAFLOW|163/164-GAS" → "163-164"
   if '|' in unidade_raw:
       unidade_raw = unidade_raw.split('|', 1)[1]
   if '-' in unidade_raw and unidade_raw.rsplit('-', 1)[1].upper() in ('AGUA', 'GAS'):
       unidade_raw = unidade_raw.rsplit('-', 1)[0]
   unidade_upload = unidade_raw.replace('/', '-')
   ```
   Resultado: `"161"`, `"163-164"`, `"LAZER GAS"`, `"TERREO GERAL AGUA"`.

3. **`views/medicao.py` L193–216** — adicionar `color="white"` em `txt_agua` e `txt_gas`. Garante que valor preenchido pelo OCR seja claramente visível no tema escuro.

## Verificação

- Como validar que o problema sumiu:
  - Bug 1: Tirar foto com internet → log não deve ter `WARNING Falha ao logar OCR` com PGRST205 (pode aparecer `DEBUG`).
  - Bug 2: Escanear QR da unidade 161 → foto deve aparecer em `fotos_hidrometros/161/202605_AGUA.jpg`; unidade 163/164 → `163-164/202605_GAS.jpg`.
  - Bug 3: OCR retorna valor → campo exibe número em branco, claramente legível.
- Regressões a checar: modo GAS (txt_gas color); campo desabilitado (Flet escurece automaticamente); hint_text ainda visível quando campo vazio.

## Convenções do projeto

- Camadas tocadas: views, utils, database (apenas scanner_view e medicao nas views; vision e database)
- Impacto em docs (`docs/`, AGENTS.md): não

## Riscos e lacunas

- A tabela `ocr_log` continua inexistente — o logging de calibragem do OCR permanece desativado. Para reativar, criar a tabela no Supabase (SQL: `CREATE TABLE ocr_log (id uuid DEFAULT gen_random_uuid() PRIMARY KEY, resposta_bruta text, valor_aceito text, status text, foi_offline boolean, modo text, modelo text, created_at timestamptz DEFAULT now())`).
- Unidades com nome que não segue o padrão `AGUAFLOW|<num>-<TIPO>` (ex: `TERREO GERAL AGUA` sem pipe/hífen) passam direto pelo normalize sem alteração — comportamento correto.
- O path normalizado `163-164` é diferente do path antigo `AGUAFLOW_163_164-GAS` — fotos antigas no Storage continuam no caminho antigo (sem impacto funcional, apenas arquivos orphaned).
