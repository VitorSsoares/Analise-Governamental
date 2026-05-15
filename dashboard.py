import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime

# --- 1. CONFIGURAÇÕES E AMBIENTE ---
st.set_page_config(layout="wide", page_title="Dashboard Legislativo Pro", page_icon="🏛️")
load_dotenv()

# Inicialização Supabase
@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_supabase()

# Inicialização IA (Usando o identificador estável da sua lista)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model_ai = genai.GenerativeModel('gemini-flash-latest')

# --- 2. ESTILIZAÇÃO (Layout Teal Preservado) ---
st.markdown("""
    <style>
    .header-container { background-color: #002B5B; padding: 20px; border-radius: 5px; color: white; margin-bottom: 25px; }
    .metric-box { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; border-top: 4px solid #E2E8F0; height: 100%; }
    .metric-box h3 { color: #64748B; font-size: 13px; margin-bottom: 5px; font-weight: bold; }
    .metric-box h2 { color: #1E3A8A; font-size: 26px; margin: 0; }
    .filter-header { background-color: #1ABC9C; color: white; padding: 10px 15px; border-radius: 8px 8px 0 0; font-weight: bold; }
    .chat-header { background-color: #1E3A8A; color: white; padding: 12px; border-radius: 10px 10px 0 0; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PROCESSAMENTO DE DADOS ---
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        res = supabase.table("parlamentares").select("*").execute()
        df = pd.DataFrame(res.data)
        df.columns = [c.lower().strip() for c in df.columns]
        
        if 'ano' not in df.columns:
            df['ano'] = datetime.now().year
        
        placeholder = "https://www.camara.leg.br/tema/assets/images/foto-deputado-sem-imagem.png"
        df["url_foto"] = df["url_foto"].fillna(placeholder).astype(str)
        
        for c in ["projetos_propostos", "projetos_aprovados", "taxa_aprovacao"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df_raw = carregar_dados()

# --- 4. INTERFACE ---
st.markdown('<div class="header-container"><h1>Dashboard de Projetos Legislativos</h1></div>', unsafe_allow_html=True)

if not df_raw.empty:
    with st.expander("🔍 Painel de Filtros", expanded=False):
        st.markdown('<div class="filter-header">Filtros</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        sel_ano = c1.multiselect("Ano", sorted(df_raw["ano"].unique().tolist(), reverse=True))
        sel_uf = c2.multiselect("UF", sorted(df_raw["uf"].unique().tolist()))
        sel_partido = c3.multiselect("Partido", sorted(df_raw["partido"].unique().tolist()))

    # Filtro Dinâmico
    df_view = df_raw.copy()
    if sel_ano: df_view = df_view[df_view["ano"].isin(sel_ano)]
    if sel_uf: df_view = df_view[df_view["uf"].isin(sel_uf)]
    if sel_partido: df_view = df_view[df_view["partido"].isin(sel_partido)]

    # Métricas
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-box"><h3>Total Projetos</h3><h2>{int(df_view["projetos_propostos"].sum())}</h2></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-box"><h3>Aprovados</h3><h2>{int(df_view["projetos_aprovados"].sum())}</h2></div>', unsafe_allow_html=True)
    with m3:
        taxa = df_view["taxa_aprovacao"].mean() if not df_view.empty else 0
        st.markdown(f'<div class="metric-box"><h3>Média Eficiência</h3><h2 style="color:#1ABC9C;">{taxa:.1f}%</h2></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-box"><h3>Parlamentares</h3><h2>{len(df_view)}</h2></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Conteúdo (Layout [1.8, 1.2])
    col_dash, col_ia = st.columns([1.8, 1.2], gap="medium")

    with col_dash:
        st.subheader("Produção Legislativa")
        fig = px.bar(df_view.groupby("partido")["projetos_propostos"].sum().reset_index(), 
                     x='partido', y='projetos_propostos', color_discrete_sequence=['#1ABC9C'], template="simple_white")
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_view[["url_foto", "nome", "partido", "uf", "projetos_propostos"]],
                     column_config={"url_foto": st.column_config.ImageColumn("Foto")}, hide_index=True, use_container_width=True)

    with col_ia:
        st.markdown('<div class="chat-header">🤖 Analista IA (Otimizado)</div>', unsafe_allow_html=True)
        chat_container = st.container(height=550, border=True)
        
        for msg in st.session_state.messages:
            with chat_container.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Ex: Qual partido é mais produtivo?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user"): st.write(prompt)

            with chat_container.chat_message("assistant"):
                # --- OTIMIZAÇÃO DE PERFORMANCE: Agregação via Pandas ---
                resumo_partidos = df_view.groupby('partido').agg({
                    'projetos_propostos': 'sum',
                    'projetos_aprovados': 'sum',
                    'nome': 'count'
                }).to_string()
                
                top_5 = df_view.nlargest(5, 'projetos_propostos')[['nome', 'partido', 'projetos_propostos']].to_string(index=False)
                
                instrucao = f"""
                Analise os dados legislativos abaixo e responda de forma concisa.
                Use bullet points para destacar informações.
                
                RESUMO POR PARTIDO:
                {resumo_partidos}
                
                TOP 5 DESTAQUES:
                {top_5}
                
                PERGUNTA: {prompt}
                """
                
                try:
                    with st.spinner("IA Processando Dados..."):
                        response = model_ai.generate_content(instrucao)
                        st.write(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
else:
    st.info("Conectando ao banco de dados...")