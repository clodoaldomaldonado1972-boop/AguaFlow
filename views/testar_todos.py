import leitor_ocr
import os


def executar_testes():
    print(f"\n{'ARQUIVO':<15} | {'UNIDADE':<15} | {'CONSUMO (m³)':<15}")
    print("-" * 50)

    for i in range(1, 11):
        nome_arquivo = f"teste{i}.jpg"

        if not os.path.exists(nome_arquivo):
            print(f"{nome_arquivo:<15} | Arquivo não encontrado")
            continue

        try:
            unidade, consumo = leitor_ocr.extrair_dados_fluxo(nome_arquivo)
            # Formata para exibir '---' se o consumo for None
            valor_display = f"{consumo} m³" if consumo else "FALHA NA LEITURA"
            print(f"{nome_arquivo:<15} | {unidade:<15} | {valor_display:<15}")
        except Exception as e:
            print(f"{nome_arquivo:<15} | ERRO: {e}")

    print("-" * 50)
    print("DICA: Verifique 'visao_do_visor.png' para entender o último erro.")


if __name__ == "__main__":
    executar_testes()
