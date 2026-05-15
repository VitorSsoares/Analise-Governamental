import requests
import pandas as pd
from supabase import create_client
import os
# Configurações via Variáveis de Ambiente (Segurança)
url_sb = os.getenv("SUPABASE_URL")
key_sb = os.getenv("SUPABASE_KEY")
supabase = create_client(url_sb, key_sb)
def sync_api_to_supabase():
# 1. Extração
endpoint = "https://dadosabertos.camara.leg.br/api/v2/deputados"
res = requests.get(endpoint).json()
df = pd.DataFrame(res['dados'])
# 2. Carga (Upsert evita duplicados)
for _, row in df.iterrows():
data = {
"id": row['id'],
"nome": row['nome'],
"partido": row['siglaPartido'],
"uf": row['siglaUf']
}
supabase.table("parlamentares").upsert(data).execute()
print("Dados Sincronizados!")
if __name__ == "__main__":
sync_api_to_supabase()