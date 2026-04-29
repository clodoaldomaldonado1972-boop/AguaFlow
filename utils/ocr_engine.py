import pytesseract
import re

def extrair_leitura_hidrometro(imagem_processada, modo="AGUA"):
    """
    Transforma a imagem binarizada em texto numérico.
    """
    try:
        # psm 7: Linha única. Whitelist permite dígitos e ponto.
        config_custom = '--psm 7 -c tessedit_char_whitelist=0123456789.'
        
        texto = pytesseract.image_to_string(imagem_processada, config=config_custom)
        
        # Mantém apenas dígitos e ponto
        numeros = re.sub(r'[^\d.]', '', texto)
        
        # Validação de comprimento para evitar lixo do OCR
        # Água (5.2) -> ~7-8 chars | Gás (5.3) -> ~8-9 chars
        if modo == "AGUA" and 4 <= len(numeros.replace('.', '')) <= 7:
            return numeros
        elif modo == "GAS" and 4 <= len(numeros.replace('.', '')) <= 8:
            return numeros
            
        return None
    except Exception as e:
        print(f"Erro no motor OCR: {e}")
        return None