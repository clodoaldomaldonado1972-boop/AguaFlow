"""
AguaFlow Mobile — Motor de Visão Otimizado para APK.
Processamento local leve via Pillow + OCR Inteligente via Claude Vision na Nuvem.
"""
import base64
import os
import time
import logging
import io

logger = logging.getLogger(__name__)

# ── IMPORTS HOMOLOGADOS PARA MOBILE ──────────────────────────────────────────
# OpenCV, NumPy e Tesseract foram totalmente removidos para evitar falhas de análise estática no Buildozer.
try:
    from PIL import Image as _PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.error("⚠️ Biblioteca Pillow (PIL) não está disponível no ambiente móvel.")

# Flags de compatibilidade mantidas estritamente como False para não quebrar referências externas nas Views
CV2_AVAILABLE = False
TESSERACT_AVAILABLE = False

# Mude para True em ambiente de desenvolvimento para simular respostas sem consumir a API real
MODO_SIMULADOR = False


def processar_foto_hidrometro(caminho_foto: str, tipo: str = "água"):
    """
    Extrai a leitura de um hidrômetro/medidor de gás a partir de uma foto.

    Estratégia Mobile Otimizada:
      1. Compressão local assíncrona utilizando Pillow (Reduz consumo de banda e RAM).
      2. Envio do payload em Base64 para processamento na nuvem via Claude Vision.
    
    Retorna: (unidade_qr: None, valor_leitura: str | None, status: str)
    """
    if MODO_SIMULADOR:
        logger.info("🤖 [SIMULADOR] Retornando dados fixos de teste mobile.")
        time.sleep(0.8)
        return None, "00542.30", "ok"

    if not os.path.exists(caminho_foto):
        logger.error(f"❌ Arquivo de mídia não encontrado no cache: {caminho_foto}")
        return None, None, "sem_leitura"

    # OCR primário e único: Claude Vision na Nuvem
    valor, foi_offline = _ocr_claude(caminho_foto, tipo)

    if valor is None:
        status = "offline" if foi_offline else "sem_leitura"
    else:
        status = "ok"

    # Retorna sempre None para o QR Code local no ambiente mobile, delegando o vínculo 
    # de unidades para a lógica de metadados da View ou digitação assistida.
    return None, valor, status


# ── Pré-processamento de Imagem Leve (Pillow) ─────────────────────────────────

def _preparar_imagem_bytes(caminho_foto: str, tipo: str = "água") -> bytes:
    """
    Recorta e redimensiona a imagem antes de enviar ao Claude utilizando apenas o Pillow.
    Evita estouro de memória no Android e otimiza o upload.

    Crop adaptativo por tipo:
      GÁS  — mostrador centralizado no medidor → corta 30-75% da altura em retrato
      ÁGUA — mostrador na metade inferior       → corta 45-90% da altura em retrato
    """
    if PIL_AVAILABLE:
        try:
            img = _PILImage.open(caminho_foto)
            w, h = img.size

            if h > w:  # retrato (foto de celular na vertical)
                is_gas = "gás" in tipo.lower() or "gas" in tipo.lower()
                if is_gas:
                    # Medidores de gás: mostrador no terço central — janela mais ampla
                    img = img.crop((0, int(h * 0.25), w, int(h * 0.80)))
                else:
                    # Hidrômetros de água: mostrador na metade inferior
                    img = img.crop((0, int(h * 0.45), w, int(h * 0.90)))

            img.thumbnail((1024, 1024))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)
            return buf.getvalue()
        except Exception as ex:
            logger.warning(f"Falha ao processar imagem com Pillow: {ex}")

    with open(caminho_foto, "rb") as f:
        return f.read()


def _portrait_detect(caminho_foto: str) -> bool:
    """Retorna True se a imagem capturada estiver em orientação Retrato (Portrait)."""
    if PIL_AVAILABLE:
        try:
            img = _PILImage.open(caminho_foto)
            w, h = img.size
            return h > w
        except Exception:
            pass
    return False


# ── Prompt OCR Otimizado por Tipo de Medidor ─────────────────────────────────

def _prompt_ocr(tipo: str, is_portrait: bool = False) -> str:
    is_gas = "gás" in tipo.lower() or "gas" in tipo.lower()

    if is_gas:
        return (
            "Esta é uma foto de um medidor de GÁS residencial marca LAO (contador mecânico de roletes).\n\n"
            "ESTRUTURA DO PAINEL FRONTAL (de cima para baixo, dentro da tampa transparente):\n"
            "  1. Etiqueta branca no TOPO com código de barras e NÚMERO DE SÉRIE "
            "(ex: 'A16L0128519D', 'A10190151501A') — IGNORE totalmente esta etiqueta.\n"
            "  2. JANELAS DE ROLETES no CENTRO — este é o único alvo de leitura.\n"
            "  3. Texto de especificações abaixo (Vn., Qmax, Qmin, Pmax, G0.6, IND.BRAS.) — IGNORE.\n\n"
            "PASSO 1 — Localize as JANELAS DE ROLETES no centro do painel:\n"
            "São retângulos enfileirados horizontalmente. "
            "Cada janela mostra UM dígito (0-9) em rolete mecânico. "
            "As 5 janelas da esquerda têm fundo PRETO (parte inteira, m³). "
            "As 3 janelas da direita têm fundo VERMELHO (decimais, hm³).\n\n"
            "PASSO 2 — IGNORE absolutamente tudo que não são os roletes:\n"
            "NÃO leia o número de série impresso na etiqueta ACIMA dos roletes "
            "(ex: 'A16L0128519D', 'A10190151501A' — são alfanuméricos, não a leitura). "
            "NÃO leia código de barras. "
            "NÃO leia especificações técnicas (G0.6, G4, Vn, Qmax, Pmax, IND.BRAS.). "
            "NÃO leia número de unidade na parede, QR code ou qualquer texto fora dos roletes.\n\n"
            "PASSO 3 — Leia os 8 dígitos nos roletes, da esquerda para a direita.\n"
            "Use ponto como separador após o 5º dígito.\n"
            "Formato obrigatório: 5 dígitos + ponto + 3 dígitos "
            "(ex: '00214.835', '00158.485', '00327.834').\n"
            "Retorne APENAS a string numérica limpa. "
            "Se os roletes estiverem obstruídos ou ilegíveis, retorne: null"
        )
    return (
        "Esta é uma foto de um hidrômetro de ÁGUA circular marca Renova (modelo UR-3.0).\n\n"
        "ESTRUTURA DA FACE DO MEDIDOR (dentro da tampa circular transparente):\n"
        "  1. Logo 'Renova B-H' e texto de especificações (PN 10, T Max: 40°C, 38.57) — IGNORE.\n"
        "  2. FAIXA DE ROLETES — retângulo horizontal com janelas de dígitos — ESTE É O ALVO.\n"
        "  3. Símbolo 'm³' imediatamente à direita da faixa de roletes — use como referência.\n"
        "  4. Mostrador analógico giratório à direita (ponteiro vermelho, escalas circulares 0-9) — IGNORE.\n"
        "  5. Tampa basculante aberta (sticker com QR code e serial ex: 'A23R012062') — IGNORE.\n\n"
        "PASSO 1 — Localize a FAIXA DE ROLETES à esquerda do símbolo 'm³':\n"
        "São janelas enfileiradas horizontalmente, cada uma com UM dígito (0-9) em rolete mecânico. "
        "As 5 janelas da esquerda têm fundo PRETO (parte inteira, m³). "
        "As 2 janelas da direita têm fundo VERMELHO (decimais).\n\n"
        "PASSO 2 — IGNORE absolutamente tudo que não são os roletes:\n"
        "NÃO leia os números do mostrador analógico (ponteiro vermelho e escalas 0-9 circulares). "
        "NÃO leia o número de série ou QR code da tampa aberta (ex: 'A23R012062'). "
        "NÃO leia especificações (PN 10, T Max, 38.57, UR-3.0, Qmax, Qmin, INMETRO). "
        "NÃO leia número de unidade visível na parede.\n\n"
        "PASSO 3 — Leia os 7 dígitos nos roletes, da esquerda para a direita.\n"
        "Use ponto como separador após o 5º dígito.\n"
        "Formato obrigatório: 5 dígitos + ponto + 2 dígitos "
        "(ex: '03285.52', '05683.08', '03943.14').\n"
        "Retorne APENAS a string numérica limpa. "
        "Se os roletes estiverem obstruídos ou ilegíveis, retorne: null"
    )


# ── OCR via Claude Vision API ─────────────────────────────────────────────────

def _log_ocr_supabase(resposta_bruta: str, valor_aceito, status: str, foi_offline: bool, tipo: str):
    """Registra tentativa OCR na tabela ocr_log do Supabase para calibragem."""
    try:
        from database.database import Database
        client = Database.supabase_admin or Database.supabase
        if not client:
            return
        client.table("ocr_log").insert({
            "resposta_bruta": resposta_bruta,
            "valor_aceito": valor_aceito,
            "status": status,
            "foi_offline": foi_offline,
            "modo": "GAS" if ("gás" in tipo.lower() or "gas" in tipo.lower()) else "AGUA",
            "modelo": "claude-haiku-4-5-20251001",
        }).execute()
        logger.debug("📊 OCR logado no Supabase")
    except Exception as ex:
        logger.warning(f"Falha ao logar OCR: {ex}")


def _ocr_claude(caminho_foto: str, tipo: str = "água") -> tuple:
    """
    Envia a imagem otimizada para o Claude Haiku e extrai os valores do mostrador.
    Retorna uma tupla: (valor, foi_offline)
    """
    try:
        from anthropic import Anthropic
        from dotenv import load_dotenv

        # Carrega as variáveis de ambiente locais do arquivo .env corporativo
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("⚠️ ANTHROPIC_API_KEY não localizada nas variáveis de ambiente — pulando Claude Vision.")
            return None, True

        is_portrait = _portrait_detect(caminho_foto)
        raw_bytes = _preparar_imagem_bytes(caminho_foto, tipo)
        img_b64 = base64.b64encode(raw_bytes).decode("utf-8")

        is_gas = "gás" in tipo.lower() or "gas" in tipo.lower()
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            system=(
                "Você é um especialista em leitura de medidores de gás e água. "
                "Sua única função é extrair o valor exibido no mostrador retangular principal do medidor. "
                "Responda SOMENTE com a string numérica no formato solicitado ou 'null'. "
                "Nunca explique, nunca adicione texto extra."
            ),
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        }
                    },
                    {
                        "type": "text",
                        "text": _prompt_ocr(tipo, is_portrait)
                    },
                ],
            }],
        )

        texto = msg.content[0].text.strip()
        logger.info(f"📡 Resposta bruta do Claude Vision: '{texto}'")

        if not texto or texto.lower() == "null":
            _log_ocr_supabase(texto, None, "sem_leitura", False, tipo)
            return None, False

        # Sanitização básica da resposta da IA
        texto = texto.replace(",", ".")
        try:
            float(texto)
            _log_ocr_supabase(texto, texto, "ok", False, tipo)
            return texto, False
        except ValueError:
            logger.warning(f"⚠️ Resposta da IA não seguiu o padrão estritamente numérico: '{texto}'")
            _log_ocr_supabase(texto, None, "formato_invalido", False, tipo)
            return None, False

    except Exception as e:
        try:
            from anthropic import APIConnectionError, APITimeoutError
            if isinstance(e, (APIConnectionError, APITimeoutError)):
                logger.warning(f"📶 Falha de comunicação de rede com os servidores Anthropic: {e}")
                _log_ocr_supabase("", None, "offline", True, tipo)
                return None, True
        except ImportError:
            pass

        logger.warning(f"⚠️ Erro operacional no módulo Claude Vision: {e}")
        msg_lower = str(e).lower()
        is_offline = any(keyword in msg_lower for keyword in ("connect", "timeout", "network", "unreachable", "dns"))
        _log_ocr_supabase(str(e)[:200], None, "offline" if is_offline else "erro", is_offline, tipo)
        return None, is_offline