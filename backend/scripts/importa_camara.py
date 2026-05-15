import requests
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Configurações
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def importar_deputados():
    print("📡 Conectando à API da Câmara...")
    # Endpoint para listar todos os deputados em exercício
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"
    
    response = requests.get(url)
    if response.status_code != 200:
        print("❌ Erro ao acessar API da Câmara")
        return

    deputados = response.json()['dados']
    
    for dep in deputados:
        id_camara = dep['id']
        nome = dep['nome']
        partido = dep['siglaPartido']
        uf = dep['siglaUf']
        foto = dep['urlFoto']

        print(f"🔄 Sincronizando: {nome} ({partido})")

        # Upsert: Insere novo ou atualiza se o id_camara já existir
        data = {
            "id_camara": id_camara,
            "nome": nome,
            "partido": partido,
            "uf": uf,
            "url_foto": foto
        }

        # No Supabase, o 'on_conflict' ajuda a não duplicar registros
        try:
            supabase.table("parlamentares").upsert(data, on_conflict="id_camara").execute()
        except Exception as e:
            print(f"⚠️ Erro ao inserir {nome}: {e}")

    print("✅ Sincronização concluída!")

if __name__ == "__main__":
    importar_deputados()