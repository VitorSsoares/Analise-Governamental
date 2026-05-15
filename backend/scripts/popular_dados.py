import os
import sys
from pathlib import Path
import random
from dotenv import load_dotenv
from supabase import create_client

# Ajuste de caminhos para encontrar o ambiente
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Adiciona o backend ao path para usar o AnalisadorIA
sys.path.append(str(ROOT_DIR / "backend"))
from app.ai.analisador import AnalisadorIA

# Inicialização
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
analisador = AnalisadorIA(api_key=os.getenv("GROQ_API_KEY"))

def popular_metricas_e_ia():
    print("🚀 Iniciando processamento de parlamentares...")
    
    # 1. Busca todos os parlamentares do banco
    res = supabase.table("parlamentares").select("*").execute()
    parlamentares = res.data

    for p in parlamentares:
        p_id = p['id']
        nome = p['nome']
        
        print(f"📦 Processando: {nome} (ID: {p_id})")

        # 2. Simulação de métricas (Simulando os dados da image_7755f5.jpg)
        propostos = random.randint(50, 200)
        aprovados = random.randint(5, int(propostos * 0.4)) # No máx 40% de aprovação
        tramitacao = propostos - aprovados
        
        # 3. Geração da Análise via IA (Groq)
        # Passamos os dados reais para a IA não alucinar
        dados_para_ia = {
            "nome": nome,
            "partido": p.get('partido'),
            "uf": p.get('uf'),
            "atuacao": f"Possui {propostos} projetos propostos e {aprovados} aprovados."
        }
        analise = analisador.analisar_perfil(dados_para_ia)

        # 4. Update no Supabase
        supabase.table("parlamentares").update({
            "projetos_propostos": propostos,
            "projetos_aprovados": aprovados,
            "em_tramitacao": tramitacao,
            "analise_ia": analise
        }).eq("id", p_id).execute()

        # 5. Criando histórico anual (para o gráfico de linhas da imagem)
        for ano in [2023, 2024, 2025]:
            supabase.table("producao_anual").insert({
                "parlamentar_id": p_id,
                "ano": ano,
                "propostos": random.randint(10, 50),
                "aprovados": random.randint(0, 10)
            }).execute()

        print(f"✅ {nome} atualizado com sucesso!")

if __name__ == "__main__":
    popular_metricas_e_ia()