import requests
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def atualizar_dados():
    # 1. Puxa dados da API da Câmara (Exemplo de deputados)
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"
    response = requests.get(url).json()
    df = pd.DataFrame(response['dados'])
    
    # 2. Sincroniza com seu Supabase
    for _, row in df.iterrows():
        # O upsert garante que não haverá duplicatas
        supabase.table("parlamentares").upsert({
            "id": row['id'],
            "nome": row['nome'],
            "partido": row['siglaPartido'],
            "uf": row['siglaUf'],
            "url_foto": row['urlFoto']
        }).execute()
    print("Dados sincronizados com sucesso!")

if __name__ == "__main__":
    atualizar_dados()