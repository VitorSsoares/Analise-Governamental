import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from supabase import create_client

# --- AJUSTE DE AMBIENTE ---
# Define a raiz do projeto (analise Governo) e a pasta backend
CURRENT_DIR = Path(__file__).resolve().parent # pasta 'app'
BACKEND_DIR = CURRENT_DIR.parent             # pasta 'backend'
ROOT_DIR = BACKEND_DIR.parent                # pasta 'analise Governo'

# Adiciona ao sys.path para o Python encontrar o pacote 'app'
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

# Carrega o .env da raiz do projeto
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# --- IMPORTS DO PROJETO ---
try:
    from app.ai.analisador import AnalisadorIA
except ImportError:
    from ai.analisador import AnalisadorIA

# --- INICIALIZAÇÃO ---
app = FastAPI(title="Portal de Análise Governamental")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
groq_key = os.getenv("GROQ_API_KEY")

supabase = create_client(supabase_url, supabase_key)
analisador = AnalisadorIA(api_key=groq_key)

@app.get("/")
def home():
    return {"status": "Online", "database": "Conectado", "ia": "Groq Llama-3"}

@app.get("/deputados/{id}/analise")
def obter_analise(id: int):
    try:
        # Busca parlamentar no Supabase
        res = supabase.table("parlamentares").select("*").eq("id", id).single().execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Parlamentar não encontrado.")
        
        # Gera análise com a IA
        texto_analise = analisador.analisar_perfil(res.data)
        
        return {
            "id": res.data.get("id"),
            "nome": res.data.get("nome"),
            "partido": res.data.get("partido"),
            "analise": texto_analise
        }
    except Exception as e:
        print(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))