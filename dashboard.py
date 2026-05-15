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

# Inicialização IA (Modelo estável da sua lista)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model_ai = genai.GenerativeModel('gemini-flash-latest')

# --- 2. ESTILIZAÇÃO CSS ---
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

# --- 3. FUNÇÕES DE PERSISTÊNCIA (CHAT) ---
def salvar_mensagem_no_banco(role, content):
    try:
        supabase.table("chat_history").insert({"role": role, "content": content}).execute()
    except Exception as e:
        pass # Silencioso para não travar a UI se a tabela não existir ainda

def carregar_historico_do_banco():
    try:
        res = supabase.table("chat_history").select("*").order("created_at", desc=False).execute()
        return [{"role": m["role"], "content": m["content"]} for m in res.data]
    except Exception:
        return []

if "messages" not in st.session_state:
    st.session_state.messages = carregar_historico_do_banco()

# --- 4. PROCESSAMENTO DE DADOS ---
@st.cache_data(ttl=600)
def carregar_dados():
    try:
        res = supabase.table("parlamentares").select("*").execute()
        df = pd.DataFrame(res.data)
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Garantir colunas numéricas para o Quadrante
        for col in ["projetos_propostos", "projetos_aprovados"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        
        # Cálculo de Eficiência
        df['taxa_aprovacao'] = (df['projetos_aprovados'] / df['projetos_propostos'] * 100).fillna(0)
        
        placeholder = "https://www.camara.leg.br/tema/assets/images/foto-deputado-sem-imagem.png"
        if "url_foto" in df.columns:
            df["url_foto"] = df["url_foto"].fillna(placeholder).astype(str)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df_raw = carregar_dados()

# --- 5. INTERFACE DASHBOARD ---
st.markdown('<div class="header-container"><h1>Análise Governamental: Eficiência Legislativa</h1></div>', unsafe_allow_html=True)

if not df_raw.empty:
    with st.expander("🔍 Filtros Avançados", expanded=False):
        c1, c2 = st.columns(2)
        sel_uf = c1.multiselect("UF", sorted(df_raw["uf"].unique().tolist()))
        sel_partido = c2.multiselect("Partido", sorted(df_raw["partido"].unique().tolist()))

    df_view = df_raw.copy()
    if sel_uf: df_view = df_view[df_view["uf"].isin(sel_uf)]
    if sel_partido: df_view = df_view[df_view["partido"].isin(sel_partido)]

    # Métricas Principais
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-box"><h3>Propostas Totais</h3><h2>{int(df_view["projetos_propostos"].sum())}</h2></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-box"><h3>Aprovações</h3><h2>{int(df_view["projetos_aprovados"].sum())}</h2></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-box"><h3>Média Eficiência</h3><h2>{df_view["taxa_aprovacao"].mean():.1f}%</h2></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-box"><h3>Parlamentares</h3><h2>{len(df_view)}</h2></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_dash, col_ia = st.columns([1.8, 1.2], gap="medium")

    with col_dash:
        # Gráfico de Dispersão (Benchmarking)
        st.subheader("🎯 Quadrante de Performance")
        fig_scatter = px.scatter(
            df_view, x="projetos_propostos", y="taxa_aprovacao",
            color="partido", hover_name="nome", size="projetos_propostos",
            labels={"projetos_propostos": "Volume de Projetos", "taxa_aprovacao": "Taxa de Aprovação (%)"},
            template="plotly_white", height=500
        )
        # Linhas de Média para criar o Quadrante
        if len(df_view) > 0:
            fig_scatter.add_hline(y=df_view['taxa_aprovacao'].mean(), line_dash="dot", annotation_text="Média Eficiência")
            fig_scatter.add_vline(x=df_view['projetos_propostos'].mean(), line_dash="dot", annotation_text="Média Volume")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Tabela Detalhada
        st.dataframe(df_view[["url_foto", "nome", "partido", "uf", "projetos_propostos", "taxa_aprovacao"]],
                     column_config={"url_foto": st.column_config.ImageColumn("Foto"),
                                   "taxa_aprovacao": st.column_config.NumberColumn("Eficiência (%)", format="%.1f")}, 
                     hide_index=True, use_container_width=True)

    with col_ia:
        st.markdown('<div class="chat-header">🤖 Analista Legislativo IA</div>', unsafe_allow_html=True)
        chat_container = st.container(height=650, border=True)
        
        for msg in st.session_state.messages:
            with chat_container.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Diga: Quais são os parlamentares acima da média?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            salvar_mensagem_no_banco("user", prompt)
            with chat_container.chat_message("user"): st.write(prompt)

            with chat_container.chat_message("assistant"):
                # Contexto Analítico Otimizado
                stats = df_view.groupby('partido').agg({'projetos_propostos':'sum', 'taxa_aprovacao':'mean'}).to_string()
                top_5 = df_view.nlargest(5, 'taxa_aprovacao')[['nome', 'taxa_aprovacao']].to_string(index=False)
                
                instrucao = f"Baseado nestas métricas:\n\nRESUMO PARTIDOS:\n{stats}\n\nTOP EFICIÊNCIA:\n{top_5}\n\nAnalise: {prompt}"
                
                try:
                    with st.spinner("IA calculando correlações..."):
                        response = model_ai.generate_content(instrucao)
                        res_text = response.text
                        st.write(res_text)
                        st.session_state.messages.append({"role": "assistant", "content": res_text})
                        salvar_mensagem_no_banco("assistant", res_text)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")