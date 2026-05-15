import requests
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

# Carrega variáveis locais (no GitHub ele usará os Secrets)
load_dotenv()

def sync():
    url_sb = os.getenv("SUPABASE_URL")
    key_sb = os.getenv("SUPABASE_KEY")
    
    if not url_sb or not key_sb:
        print("Erro: Variáveis de ambiente não configuradas.")
        return

    supabase = create_client(url_sb, key_sb)

    print("Buscando parlamentares na API da Câmara...")
    try:
        # Puxando a lista de deputados atuais
        url_api = "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"
        response = requests.get(url_api).json()
        df = pd.DataFrame(response['dados'])

        # Preparando e subindo para o Supabase
        for _, row in df.iterrows():
            dados_parlamentar = {
                "id": row['id'],
                "nome": row['nome'],
                "partido": row['siglaPartido'],
                "uf": row['siglaUf'],
                "url_foto": row['urlFoto']
            }
            supabase.table("parlamentares").upsert(dados_parlamentar).execute()
        
        print("Sincronização concluída com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    sync()