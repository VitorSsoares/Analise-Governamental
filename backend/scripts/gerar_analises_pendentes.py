import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Configuração de caminhos
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")
sys.path.append(str(ROOT_DIR / "backend"))

from app.ai.analisador import AnalisadorIA

# Inicialização
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
analisador = AnalisadorIA(api_key=os.getenv("GROQ_API_KEY"))

def processar_analises_faltantes():
    print("🔍 Buscando parlamentares sem análise de IA...")
    
    # Busca apenas quem tem projetos mas o campo analise_ia está nulo ou vazio
    res = supabase.table("parlamentares")\
        .select("*")\
        .is_("analise_ia", "null")\
        .execute()
    
    pendentes = res.data
    total = len(pendentes)
    
    if total == 0:
        print("✅ Todos os parlamentares já possuem análises. Nada a fazer.")
        return

    print(f"📦 Encontrados {total} registros para processar.")

    for idx, p in enumerate(pendentes):
        p_id = p['id']
        nome = p['nome']
        
        print(f"[{idx+1}/{total}] Gerando inteligência para: {nome}...")

        # Prepara o contexto para a Groq ser precisa
        dados_contexto = {
            "nome": nome,
            "partido": p.get('partido'),
            "uf": p.get('uf'),
            "atuacao": f"Possui {p.get('projetos_propostos', 0)} projetos registrados na Câmara."
        }

        try:
            # Gera a análise
            analise = analisador.analisar_perfil(dados_contexto)

            # Salva no banco
            supabase.table("parlamentares").update({
                "analise_ia": analise
            }).eq("id", p_id).execute()
            
            print(f"✅ Análise salva para {nome}.")
            
            # Rate limit preventivo para o Free Tier da Groq
            time.sleep(2) 
            
        except Exception as e:
            print(f"❌ Erro ao processar {nome}: {e}")
            continue

    print("🏁 Processamento concluído!")

if __name__ == "__main__":
    processar_analises_faltantes()