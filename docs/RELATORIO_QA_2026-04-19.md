# Relatório de Análise QA - AguaFlow MVP

**Data:** 2026-04-19  
**Analista:** Engenheiro de QA (Ollama)  
**Revisão:** Claude Code  
**Arquivos Analisados:** `main.py`, `database/database.py`, `views/medicao.py`, `utils/scanner.py`

---

## 🔴 ERROS CRÍTICOS (BLOQUEANTES PARA MVP)

### 1. MÉTODOS DO BANCO DE DADOS NÃO EXISTEM

**Problema:** A tela de medição (`views/medicao.py`) chama métodos que **não estão implementados** em `database/database.py`.

| Método Chamado | Localização | Status |
|----------------|-------------|--------|
| `Database._gerar_lista_unidades()` | `medicao.py:16` | ❌ **NÃO EXISTE** |
| `Database.buscar_ultima_unidade_lida()` | `medicao.py:20` | ❌ **NÃO EXISTE** |

**Impacto:** A tela de medição **não carrega** e lança exceção ao tentar acessar essas funções.

**Solução Necessária:** Implementar os métodos em `database/database.py`:

```python
@classmethod
def _gerar_lista_unidades(cls):
    """Retorna lista ordenada de unidades (166→101)."""
    # Edifício Vivere: 66 unidades (101-166)
    unidades = []
    for andar in range(6, 0, -1):  # 6º ao 1º andar
        for num in range(1, 7):    # 4 unidades por andar + 2 duplex
            unidade = f"{andar}{num}"
            unidades.append(unidade)
    # Adiciona unidades duplex
    unidades.extend(["163", "164", "23", "24"])
    return unidades

@classmethod
def buscar_ultima_unidade_lida(cls):
    """Retorna a última unidade gravada no banco."""
    with cls.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT unidade FROM leituras ORDER BY id DESC LIMIT 1")
        resultado = cursor.fetchone()
        return resultado["unidade"] if resultado else None
```

---

### 2. LÓGICA DUPLEX DESSINCRONIZADA

**Problema:** A lógica de unidades duplex (163/164 e 23/24) está implementada de forma **inconsistente**:

| Local | Implementação | Problema |
|-------|---------------|----------|
| `database/database.py:66-70` | Mapeia 163→163/164, 164→163/164, 23→23/24, 24→23/24 | ✅ Correto |
| `views/medicao.py:101` | Salta 2 unidades se for "163" ou "23" | ⚠️ **Parcial** |

**Risco:** Se a unidade "164" ou "24" for lida primeiro (manualmente), o salto de 2 unidades **não funciona** corretamente.

**Solução:** Unificar a lógica em um método central:

```python
@classmethod
def buscar_ultima_unidade_lida(cls, unidade_atual, db_lista):
    """Calcula próxima unidade considerando duplex."""
    duplex_map = {"163": "163/164", "164": "163/164", "23": "23/24", "24": "23/24"}
    
    # Se é parte de duplex, pula para o próximo após o par
    if unidade_atual in ["163", "23"]:
        idx = db_lista.index(unidade_atual)
        return db_lista[idx + 2] if idx + 2 < len(db_lista) else db_lista[0]
    elif unidade_atual in ["164", "24"]:
        # Se chegou aqui por erro, volta ao início
        return db_lista[0]
    else:
        idx = db_lista.index(unidade_atual)
        return db_lista[idx + 1] if idx + 1 < len(db_lista) else db_lista[0]
```

---

### 3. GRAVAÇÃO NO SQLITE PODE FALHAR POR BLOQUEIO

**Problema:** O timeout de 30s no `sqlite3.connect()` ajuda, mas não resolve cenários de:

1. **Conexões não fechadas** - Se `conn.close()` não for chamado em exceção
2. **Transações pendentes** - `conn.commit()` pode não ser atingido em erro
3. **Acesso concorrente** - Múltiplas threads sem lock adequado

**Evidência no Código:**

```python
# database/database.py:12-21
@contextmanager
def get_db(cls):
    conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False, timeout=30)
    try:
        yield conn
    finally:
        conn.close()  # ✅ Isso é bom, mas...
```

**Problema Real:** O método `salvar_leitura_local` não trata exceções de forma granular:

```python
# database/database.py:56-82
def salvar_leitura_local(cls, unidade, agua, gas, tipo):
    try:
        with cls.get_db() as conn:
            cursor = conn.cursor()
            # ... INSERT ...
            conn.commit()
            return True
    except Exception as e:  # ❌ Captura TUDO, inclusive KeyboardInterrupt
        print(f"❌ Falha ao gravar: {e}")
        return False
```

**Solução:**

```python
def salvar_leitura_local(cls, unidade, agua, gas, tipo):
    try:
        with cls.get_db() as conn:
            cursor = conn.cursor()
            # Validação prévia dos dados
            if not unidade or agua is None:
                raise ValueError("Unidade e leitura de água são obrigatórias")
            
            # Mapeamento duplex
            mapeamento = {"163": "163/164", "164": "163/164", "23": "23/24", "24": "23/24"}
            unidade_final = mapeamento.get(unidade, unidade)

            cursor.execute("""
                INSERT INTO leituras (unidade, leitura_agua, leitura_gas, data_hora_coleta)
                VALUES (?, ?, ?, ?)
            """, (unidade_final, float(agua), float(gas), datetime.now().isoformat()))
            
            conn.commit()
            print(f"💾 Sucesso: Unidade {unidade_final} gravada.")
            return True
            
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"🔒 Banco bloqueado. Tentando novamente em 1s...")
            time.sleep(1)
            return cls.salvar_leitura_local(unidade, agua, gas, tipo)  # Retry
        raise
    except (ValueError, TypeError) as e:
        print(f"📝 Dados inválidos: {e}")
        return False
```

---

## ⚠️ PROBLEMAS DE MÉDIA PRIORIDADE

### 4. SCANNER OCR NÃO RETORNA UNIDADE

**Problema:** O `utils/scanner.py` recebe o callback `processar_retorno_ocr` mas o OCR **não retorna a unidade** - apenas o valor.

```python
# utils/leitor_ocr.py:64-67
return {
    "unidade": unidade,  # ✅ Vem do QR Code
    "valor": valor,      # ✅ Vem do OCR
    "status": "Sucesso" if unidade and valor else "Parcial"
}
```

**Risco:** Se o QR Code não for legível, a unidade chega como `None` e a medição não pode ser salva.

**Recomendação:** Adicionar fallback para unidade manual quando QR Code falhar.

---

### 5. CONVERSÃO DE TIPOS NÃO TRATADA

**Problema:** Em `views/medicao.py:90-91`:

```python
agua_f = float(txt_agua.value.replace(",", "."))
gas_f = float(txt_gas.value.replace(",", ".")) if txt_gas.value else 0.0
```

Se `txt_agua.value` for vazio ou contiver caracteres inválidos, lança `ValueError`.

**Solução:** Adicionar validação antes da conversão:

```python
try:
    agua_f = float(txt_agua.value.replace(",", ".")) if txt_agua.value else None
    gas_f = float(txt_gas.value.replace(",", ".")) if txt_gas.value else 0.0
except ValueError:
    page.snack_bar = ft.SnackBar(ft.Text("Valores inválidos."), bgcolor="red", open=True)
    return
```

---

## ✅ PONTOS FORTES IDENTIFICADOS

| Item | Status | Observação |
|------|--------|------------|
| Timeout OCR (10s) | ✅ | Implementado corretamente |
| Context manager DB | ✅ | `get_db()` fecha conexão |
| Mapeamento duplex no DB | ✅ | Lógica correta em `salvar_leitura_local` |
| Thread safety (asyncio.to_thread) | ✅ | OCR roda em thread separada |
| Supressão de warnings | ✅ | Console limpo no Android |

---

## 📋 CHECKLIST DE CORREÇÕES

| # | Ação | Arquivo | Prioridade | Status |
|---|------|---------|------------|--------|
| 1 | Implementar `Database._gerar_lista_unidades()` | `database/database.py` | 🔴 Crítica | Pendente |
| 2 | Implementar `Database.buscar_ultima_unidade_lida()` | `database/database.py` | 🔴 Crítica | Pendente |
| 3 | Unificar lógica duplex em método central | `database/database.py` | 🔴 Crítica | Pendente |
| 4 | Adicionar retry para "database is locked" | `database/database.py` | 🔴 Crítica | Pendente |
| 5 | Validação prévia de dados antes de INSERT | `database/database.py` | 🟡 Média | Pendente |
| 6 | Fallback para unidade manual se QR Code falhar | `utils/leitor_ocr.py` | 🟡 Média | Pendente |
| 7 | Try/except na conversão float | `views/medicao.py` | 🟡 Média | Pendente |

---

## 🎯 STATUS DO MVP

| Módulo | Status | Bloqueante? |
|--------|--------|-------------|
| **Banco de Dados** | 🔴 CRÍTICO | **SIM** - Métodos faltantes |
| **Tela de Medição** | 🔴 CRÍTICO | **SIM** - Não carrega sem os métodos |
| **Scanner OCR** | ⚠️ ATENÇÃO | Não - Funciona mas pode falhar sem QR Code |
| **Regra Duplex** | ⚠️ ATENÇÃO | Não - Funciona mas tem edge cases |
| **Gravação SQLite** | ⚠️ ATENÇÃO | Potencial - Pode travar em concorrência |

---

## 📌 RECOMENDAÇÃO FINAL

**NÃO LANÇAR O MVP** sem antes implementar:

1. `Database._gerar_lista_unidades()`
2. `Database.buscar_ultima_unidade_lida()`
3. Tratamento de retry para bloqueio de banco

**Tempo estimado para correções:** 2-3 horas

---

*Relatório gerado automaticamente - Análise QA completa*
