from groq import Groq

class AnalisadorIA:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key da Groq não encontrada. Verifique seu .env")
        self.client = Groq(api_key=api_key)
        # O modelo llama3-8b-8192 saiu de linha. Vamos usar o sucessor:
        self.model = "llama-3.1-8b-instant" 

    def analisar_perfil(self, dados: dict):
        try:
            # Extraímos o máximo de info que você tiver no seu SELECT * do Supabase
            nome = dados.get('nome', 'Parlamentar')
            partido = dados.get('partido', 'MDB')
            uf = dados.get('uf', 'AP')
            # Exemplo: se você tiver uma coluna 'atuacao' no banco, use-a aqui!
            detalhes = dados.get('atuacao', 'Deputado Federal atuante') 

            # Criamos um prompt que "alimenta" a IA com fatos
            prompt = (
                f"Analise o seguinte perfil político:\n"
                f"Nome: {nome}\n"
                f"Partido/UF: {partido}/{uf}\n"
                f"Contexto: {detalhes}\n\n"
                f"Com base nesses dados e no seu conhecimento sobre a política do {partido} "
                f"na região Norte, descreva a importância estratégica deste parlamentar."
            )

            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Você é um analista político brasileiro especializado em análise de dados legislativos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5, # Menos temperatura = análise mais factual
                max_tokens=500,
                stream=False
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Erro na API Groq: {e}")
            return "Não foi possível gerar a análise técnica no momento."