import os

def criar_projeto():
    # Estrutura de pastas baseada na sua stack (FastAPI + Next.js + Crawlers)
    estrutura = [
        "backend/app/api",
        "backend/app/models",
        "backend/app/database",
        "backend/app/ai",
        "frontend/src/components/charts",
        "frontend/src/components/ui",
        "frontend/src/services",
        "crawlers/logs",
        "data/raw"
    ]

    # Arquivos base com conteúdo inicial
    arquivos = {
        # Backend
        "backend/app/main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'status': 'Radar Legislativo Online'}",
        "backend/app/database/supabase_client.py": "import os\nfrom supabase import create_client\n\nurl = os.getenv('SUPABASE_URL')\nkey = os.getenv('SUPABASE_KEY')\nsupabase = create_client(url, key)",
        "backend/requirements.txt": "fastapi\nuvicorn\nsupabase\nsqlalchemy\npsycopg2-binary\nlangchain\nopenai\npython-dotenv",
        "backend/.env": "SUPABASE_URL=seu_url_aqui\nSUPABASE_KEY=sua_chave_aqui\nOPENAI_API_KEY=sua_chave_ia_aqui",

        # Crawlers
        "crawlers/coletor_camara.py": "import requests\n\ndef fetch_data():\n    pass\n\nif __name__ == '__main__':\n    print('Coletor pronto para iniciar...')",
        "crawlers/requirements.txt": "requests\nsupabase\npython-dotenv",

        # Root
        ".gitignore": "venv/\n__pycache__/\n.env\nnode_modules/\n.next/",
        "README.md": "# Radar Legislativo\nPlataforma de análise automática de projetos legislativos com IA."
    }

    print("🚀 Iniciando criação da estrutura do Radar Legislativo...\n")

    # Criar pastas
    for pasta in estrutura:
        os.makedirs(pasta, exist_ok=True)
        # Criar __init__.py em todas as pastas do backend para evitar ImportError
        if "backend" in pasta:
            with open(os.path.join(pasta, "__init__.py"), "w") as f:
                pass
        print(f"✅ Pasta criada: {pasta}")

    # Criar arquivos
    for caminho, conteudo in arquivos.items():
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print(f"📄 Arquivo criado: {caminho}")

    print("\n✨ Tudo pronto! Agora você pode começar a Fase 2 (Coleta de Dados).")

if __name__ == "__main__":
    criar_projeto()