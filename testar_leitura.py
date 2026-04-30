from database.database import Database
import os
import sys

# Garante que o Python encontre as pastas database e utils
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


def teste_fluxo_leitura():
    print("🚀 INICIANDO TESTE AUTOMÁTICO DE LEITURA\n")

    # 1. Inicializa o banco (Garante que as tabelas existam)
    Database.init_db()

    # 2. Busca a próxima unidade pendente
    pendente = Database.buscar_proximo_pendente(tipo_filtro="Água")

    if not pendente:
        print("❌ Nenhuma unidade pendente encontrada. Rode o forcar_reset.py primeiro.")
        return

    unidade_id, _, tipo = pendente
    print(f"📍 Unidade selecionada para teste: {unidade_id}")

    # 3. Simula o processamento da visão computacional
    from utils.vision import processar_foto_hidrometro  # Lazy loading
    # Passamos um caminho fictício pois o MODO_SIMULADOR no vision.py ignora a imagem
    print("📸 Simulando leitura do hidrômetro...")
    unidade_ocr, valor_ocr = processar_foto_hidrometro("caminho/fake/foto.jpg")

    if valor_ocr:
        print(f"✅ Visão capturou o valor: {valor_ocr}")

        # 4. Grava no banco de dados
        resultado = Database.registrar_leitura(
            unidade=unidade_id,
            valor=valor_ocr,
            tipo_leitura=tipo
        )

        if resultado['sucesso']:
            print(
                f"💾 SUCESSO: Leitura gravada no banco (ID: {resultado['id']})")

            # 5. Verificação final: Consultar se o dado está lá
            with Database.get_db() as conn:
                res = conn.execute(
                    "SELECT * FROM leituras WHERE id = ?", (resultado['id'],)).fetchone()
                print(f"\n🔍 CONFERÊNCIA NO BANCO:")
                print(
                    f"   Unidade: {res['unidade']} | Valor: {res['valor']} | Sinc: {res['sincronizado']}")
        else:
            print(f"❌ ERRO ao gravar: {resultado['mensagem']}")


if __name__ == "__main__":
    teste_fluxo_leitura()
