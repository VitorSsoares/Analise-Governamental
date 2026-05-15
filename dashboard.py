import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime

# --- 1. CONFIGURAÇÕES E AMBIENTE ---
st.set_page_config(layout="wide", page_title="Análise Legislativa Brasil", page_icon="🏛️")
load_dotenv()

# Inicialização da Conexão com Supabase
@st.cache_resource
def init_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

# Inicialização da Inteligência Artificial (Gemini)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model_ai = genai.GenerativeModel('gemini-flash-latest')

# --- 2. TRATAMENTO DE DADOS (COM PROTEÇÃO) ---
@st.cache_data(ttl=600)
def get_data():
    try:
        res = supabase.table("parlamentares").select("*").execute()
        df = pd.DataFrame(res.data)
        
        if df.empty:
            return pd.DataFrame(columns=['nome', 'partido', 'uf', 'projetos_propostos', 'projetos_aprovados', 'ano'])
        
        # Padroniza colunas
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Garante que colunas essenciais existam
        if 'ano' not in df.columns: df['ano'] = 2026
        if 'uf' not in df.columns: df['uf'] = "ND"
        
        for col in ['projetos_propostos', 'projetos_aprovados']:
            if col not in df.columns: df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['ano'] = pd.to_numeric(df['ano'], errors='coerce').fillna(2026).astype(int)
        df['uf'] = df['uf'].astype(str).str.upper()
        
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com o banco: {e}")
        return pd.DataFrame()

df_raw = get_data()

# --- 3. ESTILIZAÇÃO VISUAL ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .header-style { color: #1E3A8A; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. INTERFACE E FILTROS ---
st.title("🏛️ Portal de Transparência Legislativa")

if not df_raw.empty:
    with st.sidebar:
        st.header("⚙️ Filtros de Pesquisa")
        
        # Filtro de Ano
        anos_disponiveis = sorted(df_raw['ano'].unique(), reverse=True)
        sel_ano = st.selectbox("Selecione o Ano", anos_disponiveis)
        
        # Filtro de Partido
        partidos = sorted(df_raw['partido'].unique().tolist())
        sel_partido = st.multiselect("Filtrar por Partido", partidos)
        
        # Filtro de UF (Estado)
        ufs = sorted(df_raw['uf'].unique().tolist())
        sel_uf = st.multiselect("Filtrar por Estado (UF)", ufs)

    # Aplicação da Lógica de Filtros
    df_filtered = df_raw[df_raw['ano'] == sel_ano]
    if sel_partido:
        df_filtered = df_filtered[df_filtered['partido'].isin(sel_partido)]
    if sel_uf:
        df_filtered = df_filtered[df_filtered['uf'].isin(sel_uf)]

    # --- 5. BLOCO DE MÉTRICAS ---
    c1, c2, c3, c4 = st.columns(4)
    total_propostos = int(df_filtered['projetos_propostos'].sum())
    total_aprovados = int(df_filtered['projetos_aprovados'].sum())
    taxa_geral = (total_aprovados / total_propostos * 100) if total_propostos > 0 else 0

    c1.metric("Projetos Criados", total_propostos)
    c2.metric("Projetos Aprovados", total_aprovados)
    c3.metric("Eficiência Média", f"{taxa_geral:.1f}%")
    c4.metric("Parlamentares na Lista", len(df_filtered))

    st.markdown("---")

    # --- 6. GRÁFICOS ---
    col_visual, col_chat = st.columns([1.6, 1], gap="large")

    with col_visual:
        # Gráfico de Funil
        st.subheader("📉 Funil de Conversão Legislativa")
        funnel_data = pd.DataFrame({
            "Fase": ["Criados", "Aprovados"],
            "Quantidade": [total_propostos, total_aprovados]
        })
        fig_funnel = px.funnel(funnel_data, x='Quantidade', y='Fase', color_discrete_sequence=['#1E3A8A'])
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Gráfico de Ranking
        st.subheader("🚩 Produção por Partido")
        rank_partido = df_filtered.groupby('partido')['projetos_propostos'].sum().sort_values(ascending=True).reset_index()
        fig_bar = px.bar(rank_partido, x='projetos_propostos', y='partido', 
                        orientation='h', color_discrete_sequence=['#1ABC9C'],
                        text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chat:
        st.subheader("💬 Analista de Dados IA")
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        chat_box = st.container(height=550, border=True)
        
        for msg in st.session_state.messages:
            with chat_box.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("Ex: Como está a produção do meu estado?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_box.chat_message("user"): st.write(prompt)

            with chat_box.chat_message("assistant"):
                # Prepara contexto para IA baseado no filtro atual
                resumo_uf = df_filtered.groupby('uf')['projetos_propostos'].sum().to_string()
                instrucao = f"Resumo atual (Ano {sel_ano}):\n{resumo_uf}\n\nPergunta: {prompt}"
                
                response = model_ai.generate_content(instrucao)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
else:
    st.info("Carregando dados do Supabase...")