from database.supabase_client import insert_leitura_supabase
import os
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao path para importar o database e supabase_client
sys.path.append(str(Path(__file__).parent.parent))


def processar_lote_temp():
    # Caminho absoluto para a pasta de fotos temporárias
    # O script está em /storage, então fotos estão em /storage/temp
    pasta_fotos = Path(__file__).parent / "temp"

    if not pasta_fotos.exists():
        print(f"❌ Pasta não encontrada: {pasta_fotos}")
        return

    # Extensões de imagem permitidas
    extensoes = ('.jpg', '.jpeg', '.png')
    arquivos = [f for f in os.listdir(
        pasta_fotos) if f.lower().endswith(extensoes)]

    print(f"🔍 Encontradas {len(arquivos)} fotos em {pasta_fotos}")

    for arquivo in arquivos:
        # 1. Identifica a unidade pelo nome do arquivo (ex: 51.jpg -> 51)
        unidade_base = Path(arquivo).stem

        # 2. Garante o prefixo QR- (necessário para a chave estrangeira no Supabase)
        id_final = f"QR-{unidade_base}" if not unidade_base.startswith(
            "QR-") else unidade_base[cite: 2]

        print(f"📸 Processando: {arquivo} -> Unidade: {id_final}")

        # 3. Envia os dados iniciais para o Supabase
        # Como o Supabase fará o OCR, enviamos valor 0.0 para ser processado lá
        resultado = insert_leitura_supabase(
            id_unidade=id_final,
            valor=0.0,
            tipo_leitura="Água",
            leiturista="Carga_Lote_Real"
        )[cite: 3]

        if resultado.get("sucesso"):
            print(f"   ✅ {resultado['mensagem']}")
        else:
            print(f"   ❌ Erro: {resultado['mensagem']}")


if __name__ == "__main__":
    processar_lote_temp()
