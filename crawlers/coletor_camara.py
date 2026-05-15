import requests
import os
from dotenv import load_dotenv
from supabase import create_client

# 1. Tenta carregar o .env de dois lugares para garantir
load_dotenv()
load_dotenv("../.env")

url_sb = os.getenv("SUPABASE_URL")
key_sb = os.getenv("SUPABASE_KEY")

print(f"DEBUG: URL encontrada? {'Sim' if url_sb else 'Não'}")

if not url_sb or not key_sb:
    print("❌ ERRO: Chaves não carregadas. Verifique seu arquivo .env")
    exit()

try:
    supabase = create_client(url_sb, key_sb)
    print("✅ Conexão com Supabase configurada.")
except Exception as e:
    print(f"❌ ERRO ao conectar no Supabase: {e}")
    exit()

def rodar_coletor():
    print("🚀 Buscando deputados na API da Câmara...")
    try:
        response = requests.get("https://dadosabertos.camara.leg.br/api/v2/deputados", timeout=15)
        response.raise_for_status()
        deputados = response.json()['dados']
        print(f"📦 Encontrados {len(deputados)} deputados.")
        
        # Vamos enviar os primeiros 10 para testar rápido
        print("enviando dados...")
        for dep in deputados:
            dados_para_enviar = {
                "nome": dep['nome'],
                "partido": dep['siglaPartido'],
                "uf": dep['siglaUf'],
                "foto_url": dep['urlFoto']
            }
            # O .execute() é o que realmente manda o comando
            supabase.table("parlamentares").upsert(dados_para_enviar).execute()
        
        print("✅ PROCESSO CONCLUÍDO! Verifique o Supabase agora.")

    except Exception as e:
        print(f"❌ OCORREU UM ERRO DURANTE A COLETA: {e}")

# ESSA LINHA É ESSENCIAL PARA O SCRIPT RODAR:
if __name__ == "__main__":
    rodar_coletor()