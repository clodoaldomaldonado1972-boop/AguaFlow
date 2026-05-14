"""
Teste end-to-end do OCR com fotos reais da pasta assets.
Fluxo: upload foto → inserir leitura → invocar OCR → verificar resultado.
"""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(__file__))

from database.database import Database, get_supabase_client

FOTOS = [
    ("assets/156-gas.jpg",  "QR-156-GAS",  "Gás"),
    ("assets/161-agua.jpg", "101",          "Água"),   # usa 101 (FK válida) para 161
    ("assets/162-agua.jpg", "101",          "Água"),
]

def invocar_ocr(file_path: str) -> dict:
    import httpx
    svc_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    payload = {"record": {"bucket_id": "fotos_hidrometros", "name": file_path}}
    r = httpx.post(
        "https://rpacxhgvscqnlawxgwfk.supabase.co/functions/v1/ocr-hidrometro",
        json=payload,
        headers={"Authorization": f"Bearer {svc_key}"},
        timeout=30,
    )
    return r.json() if r.status_code == 200 else {"erro": r.text}

def main():
    from dotenv import load_dotenv
    load_dotenv()
    Database.inicializar_tabelas()
    supabase = Database.supabase_admin or Database.supabase
    svc_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    for foto_local, unidade, tipo in FOTOS:
        foto_path = os.path.join(os.path.dirname(__file__), foto_local)
        if not os.path.exists(foto_path):
            print(f"⚠️  Foto não encontrada: {foto_local}")
            continue

        nome = os.path.basename(foto_local)
        modo = "GAS" if "gas" in nome.lower() else "AGUA"
        storage_path = f"{unidade}/20260514_ocr_{nome}"

        print(f"\n{'='*55}")
        print(f"Foto   : {foto_local}")
        print(f"Unidade: {unidade} | Tipo: {tipo}")

        # 1. Upload para Supabase Storage
        with open(foto_path, "rb") as f:
            dados_foto = f.read()
        resp = supabase.storage.from_("fotos_hidrometros").upload(
            storage_path, dados_foto,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        public_url = supabase.storage.from_("fotos_hidrometros").get_public_url(storage_path)
        print(f"Upload : {public_url}")

        # 2. Inserir leitura com foto_url
        insert = supabase.table("leituras").insert({
            "unidade_id": unidade,
            "tipo_registro": tipo,
            "leitura_agua": 0 if "Água" in tipo else None,
            "leitura_gas":  0 if "Gás"  in tipo else None,
            "valor_leitura": 0,
            "leiturista": "Teste-OCR",
            "data_hora_coleta": "2026-05-14T15:00:00+00:00",
            "foto_url": public_url,
        }).execute()
        leitura_id = insert.data[0]["id"] if insert.data else "?"
        print(f"Leitura: id={leitura_id} inserida com valor_leitura=0")

        # 3. Invocar OCR
        print(f"OCR    : invocando Edge Function...")
        resultado = invocar_ocr(storage_path)
        print(f"OCR    : resultado = {resultado}")

        # 4. Verificar atualização
        if "valorOcr" in resultado:
            time.sleep(1)
            row = supabase.table("leituras").select("id,valor_leitura").eq("id", leitura_id).execute()
            valor_atual = row.data[0]["valor_leitura"] if row.data else "?"
            status = "OK" if str(valor_atual) == str(resultado["valorOcr"]) else "DIVERGENCIA"
            print(f"DB     : valor_leitura = {valor_atual}  {status}")

if __name__ == "__main__":
    main()
