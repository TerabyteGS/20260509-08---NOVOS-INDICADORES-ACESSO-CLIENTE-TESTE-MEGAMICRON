import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Símic - ROC Analítico", layout="wide", initial_sidebar_state="collapsed")

COR_AZUL = "#1C3548"

st.markdown("""
    <style>
    .main {background-color: #F4F6F7;}
    div.stButton > button {width: 100%; border-radius: 8px; font-weight: bold; height: 75px; font-size: 18px; transition: 0.3s; border: 1px solid #BDC3C7; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
    div.stButton > button:hover {transform: scale(1.02); border-color: #1C3548; box-shadow: 0 8px 16px rgba(0,0,0,0.15);}
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {height: 60px; font-size: 18px; font-weight: bold; padding: 0 20px;}
    .css-1v0mbdj.etr89bj1 {margin-top: -30px;}
    hr {margin: 1em 0;}
    </style>
    """, unsafe_allow_html=True)

# --- GERADOR BIG DATA ---
@st.cache_data
def gerar_dados_totem():
    prefixos = [
        ("Moinho L 300", "Moagem", 0.7, 1750, True, "Microlube", 5),
        ("Moinho L 800", "Moagem", 2.2, 1180, True, "Sintético", 3),
        ("Injetora", "Polímeros", 1.1, 3600, True, "Molykote", 15),
        ("Prensa", "Conformação", 1.5, 900, False, "N/A", 12),
        ("Bomba Centrif", "Fluidos", 1.2, 1750, False, "N/A", 14),
        ("Exaustor", "Fluidos", 3.1, 900, True, "Lítio", 4),
        ("Compressor", "Utilidades", 1.8, 3500, True, "Sintético", 2)
    ]
    
    maquinas = []
    for pref, setor, vib, rpm, usa_lub, tipo, qtd in prefixos:
        for i in range(1, qtd + 1):
            maquinas.append({"nome": f"{pref} {i:02d}", "setor": setor, "vib_base": vib, "usa_lub": usa_lub, "tipo_lub": tipo})

    datas = pd.date_range(start=datetime.now() - timedelta(days=5), end=datetime.now(), freq='1h')
    dados = []

    for maq in maquinas:
        destino = random.choices(["Normal", "Suspeito", "Alerta", "Grave"], weights=[65, 15, 12, 8])[0]
        nivel_lub = random.randint(5, 100) if destino != "Grave" else random.randint(0, 8)
        bat_base = random.randint(20, 100) if destino != "Suspeito" else random.randint(0, 14)
        
        for data in datas:
            carga = random.uniform(60, 100)
            vib = maq["vib_base"] * random.uniform(0.8, 1.2) * (carga / 80)
            if destino in ["Alerta", "Grave"]: vib *= random.uniform(1.4, 2.2)
            
            temp = random.uniform(45, 65) + (vib * 3)
            ultrassom_db = random.uniform(30, 50) + (vib * 4)
            corrente = random.uniform(0.5, 2.0)
            sinal_dbm = random.randint(-90, -40)
            bateria = bat_base + random.uniform(-1, 1)
            
            if maq["usa_lub"]:
                nivel_lub -= random.uniform(0.1, 0.5)
                if nivel_lub < 0: nivel_lub = 0
            
            status, causa, icone, risco_usd = "Normal", "Operação Regular", "✅", 0
            health_score = 100
            
            if sinal_dbm < -82 or bateria < 15:
                status, causa, icone = "Suspeito", "Perda de Telemetria", "📡"
                health_score -= 30
            
            if vib > (maq["vib_base"] * 1.5):
                status, causa, icone, risco_usd = "Alerta", "Desbalanceamento Dinâmico", "⚙️", random.randint(8000, 15000)
                health_score -= 40; corrente *= 2.5
                
            if "Bomba" in maq["nome"] and ultrassom_db > 75:
                status, causa, icone, risco_usd = "Alerta", "Cavitação Detectada", "🌊", 6000
                health_score -= 45
                
            if maq["usa_lub"] and nivel_lub <= 5:
                status, causa, icone, risco_usd = "Grave", "Falta de Lubrificação Crítica", "🛢️", random.randint(20000, 45000)
                health_score -= 70; temp += 20
                
            if maq["usa_lub"] and destino == "Alerta" and random.randint(1, 100) > 85:
                status, causa, icone = "Alerta", "Obstrução na Linha de Graxa", "🚫"
                health_score -= 35

            if health_score < 0: health_score = random.randint(0, 5)

            dados.append({
                "Data": data, "Máquina": maq["nome"], "Setor": maq["setor"], 
                "Status": status, "Ícone": icone, "Notificação": causa, "Saúde (%)": round(health_score, 1),
                "Vibração (mm/s)": round(vib, 2), "Temperatura (°C)": round(temp, 1),
                "Ultrassom (dB)": round(ultrassom_db, 1), "Desbalanço (%)": round(corrente, 2), 
                "Carga (%)": round(carga, 1), "Nível Graxa (%)": round(nivel_lub, 1) if maq["usa_lub"] else None,
                "Bateria (%)": round(bateria, 1), "Sinal (dBm)": sinal_dbm,
                "Risco (USD)": risco_usd, "Tipo Lubrificante": maq["tipo_lub"]
            })
    return pd.DataFrame(dados).sort_values("Data", ascending=False)

df = gerar_dados_totem()
status_atual = df.drop_duplicates(subset=['Máquina'], keep='first')

if 'filtro' not in st.session_state: st.session_state.filtro = 'Todos'
def set_filtro(novo_filtro): st.session_state.filtro = novo_filtro

# --- CABEÇALHO ---
st.markdown(f"<h1 style='text-align: center; color: {COR_AZUL}; font-size: 3em; margin-bottom: 0;'>HUB DE CONFIABILIDADE SÍMIC</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; font-size: 1.2em; color: #7F8C8D;'>Monitorando {len(status_atual)} ativos via IA Preditiva | Atualizado em: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

# --- SEMÁFORO INTERATIVO (KPIs VITAIS) ---
contagem = status_atual["Status"].value_counts()
saude_geral = status_atual['Saúde (%)'].mean()
oee_estimado = 98.5 - (contagem.get('Grave', 0) * 1.2) - (contagem.get('Alerta', 0) * 0.4)

c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
c_kpi1.metric("Índice de Saúde Global", f"{saude_geral:.1f}%", f"{saude_geral - 100:.1f}%")
c_kpi2.metric("OEE Estimado (Planta)", f"{oee_estimado:.1f}%", "-0.8% hoje")
c_kpi3.metric("Risco Financeiro Mitigado", f"R$ {status_atual['Risco (USD)'].sum():,.0f}", "Prevenção Ativa")
c_kpi4.metric("Sensores Transmitindo", f"{len(status_atual)} Un.", "100% Cobertura")

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button(f"🌐 Malha Inteira\n{len(status_atual)} Ativos"): set_filtro('Todos')
with col2:
    if st.button(f"✅ Operação Normal\n{contagem.get('Normal', 0)} Ativos"): set_filtro('Normal')
with col3:
    if st.button(f"🟡 Inspeção Sugerida\n{contagem.get('Suspeito', 0)} Ativos"): set_filtro('Suspeito')
with col4:
    if st.button(f"🟠 Alerta Crítico\n{contagem.get('Alerta', 0)} Ativos"): set_filtro('Alerta')
with col5:
    if st.button(f"🔴 Falha Iminente\n{contagem.get('Grave', 0)} Ativos"): set_filtro('Grave')

df_hist_filt = df if st.session_state.filtro == 'Todos' else df[df["Status"] == st.session_state.filtro]
status_atual_filt = status_atual if st.session_state.filtro == 'Todos' else status_atual[status_atual["Status"] == st.session_state.filtro]

st.markdown("<hr>", unsafe_allow_html=True)

# ==========================================
# AS 6 ABAS TITAN (O SHOWCASE)
# ==========================================
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "⚙️ Cinemática & Vibração", 
    "🗺️ Mapa Sunburst", 
    
    "🛢️ Gestão de Cartuchos", 
    "⚡ Assinatura Multivariável", 
    "📡 Telemetria IoT", 
    "📋 Data Lake"
])

# --- ABA 1: MAPA SUNBURST ---
with aba2:
    st.markdown("### Índice de Saúde por Setor (Clique nas fatias para navegar)")
    c1, c2 = st.columns([2, 1])
    with c1:
        fig_sun = px.sunburst(status_atual, path=['Setor', 'Status', 'Máquina'], values='Saúde (%)', 
                              color='Status', color_discrete_map={"Normal": "#27AE60", "Suspeito": "#F1C40F", "Alerta": "#E67E22", "Grave": "#E74C3C"})
        fig_sun.update_layout(height=500, margin=dict(l=0, r=0, b=0, t=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sun, use_container_width=True, config={'displayModeBar': False})
    with c2:
        st.markdown("#### Top 5 Piores Índices de Saúde")
        top_doentes = status_atual_filt.sort_values('Saúde (%)').head(5)
        st.dataframe(top_doentes[['Máquina', 'Saúde (%)', 'Notificação']].style.background_gradient(cmap='Reds_r', subset=['Saúde (%)']), hide_index=True, use_container_width=True)

# --- ABA 2: CINEMÁTICA E VIBRAÇÃO (A NOVA SOLUÇÃO) ---
with aba1:
    st.markdown("### Distribuição ISO 10816 e Outliers")
    c3, c4 = st.columns([1.5, 1])
    
    with c3:
        st.info("Gráfico de Caixa (Boxplot): Mostra a variação normal da planta. Os pontos isolados acima são as anomalias detectadas (Outliers).")
        # BOXPLOT: Acaba com a poluição, mostra o "ruído" normal vs anomalias
        fig_box = px.box(status_atual_filt, x="Setor", y="Vibração (mm/s)", color="Setor", points="all", hover_data=["Máquina"])
        fig_box.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        fig_box.update_yaxes(gridcolor='#E5E8E8')
        st.plotly_chart(fig_box, use_container_width=True)

    with c4:
        st.markdown("#### Curvas Críticas (Top 5 Piores Máquinas)")
        st.info("Isola apenas as máquinas com maior índice vibratório atual para análise de tendência.")
        # LINE CHART LIMPO: Só pega as 5 piores para não virar macarrão
        top_5_maq = status_atual_filt.nlargest(5, 'Vibração (mm/s)')['Máquina'].tolist()
        df_top5 = df_hist_filt[df_hist_filt['Máquina'].isin(top_5_maq)]
        if not df_top5.empty:
            fig_line = px.line(df_top5, x="Data", y="Vibração (mm/s)", color="Máquina", line_shape="spline", color_discrete_sequence=px.colors.qualitative.Set1)
            fig_line.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=10, b=0))
            fig_line.update_xaxes(showgrid=False); fig_line.update_yaxes(gridcolor='#E5E8E8')
            st.plotly_chart(fig_line, use_container_width=True)

# --- ABA 3: TRIBOLOGIA (TREEMAP DE CARTUCHOS) ---
with aba3:
    st.markdown("### Automação de Lubrificação (Status dos Injetores)")
    df_lub = status_atual_filt.dropna(subset=["Nível Graxa (%)"])
    
    c5, c6 = st.columns([1.5, 1])
    with c5:
        st.info("Mapa de Árvore (Treemap): O tamanho do bloco reflete o volume de graxa. Blocos grandes verdes estão cheios, blocos pequenos vermelhos estão secando.")
        if not df_lub.empty:
            fig_tree = px.treemap(df_lub, path=[px.Constant("Planta Símic"), 'Setor', 'Máquina'], values='Nível Graxa (%)', color='Nível Graxa (%)', color_continuous_scale='RdYlGn')
            fig_tree.update_traces(root_color="lightgrey")
            fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=450, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_tree, use_container_width=True)
            
    with c6:
        st.markdown("#### Diagnóstico do Fluido")
        fig_pie = px.pie(df_lub, names="Tipo Lubrificante", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=250, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("**Fila de Troca Prioritária:**")
        trocas = df_lub[df_lub['Nível Graxa (%)'] < 20].sort_values('Nível Graxa (%)')
        st.dataframe(trocas[['Máquina', 'Nível Graxa (%)']].style.background_gradient(cmap='Reds_r'), hide_index=True, use_container_width=True)

# --- ABA 4: ASSINATURA MULTIVARIÁVEL ---
with aba4:
    c7, c8 = st.columns([1.5, 1])
    with c7:
        st.markdown("### Assinatura Radar (Falha Estrutural)")
        categorias = ['Vibração', 'Temperatura', 'Ultrassom', 'Desbalanço', 'Carga']
        fig_radar = go.Figure()
        for _, row in status_atual_filt.head(5).iterrows(): 
            valores = [min(row['Vibração (mm/s)']*20, 100), min(row['Temperatura (°C)'], 100), min(row['Ultrassom (dB)']*1.5, 100), min(row['Desbalanço (%)']*20, 100), min(row['Carga (%)'], 100)]
            fig_radar.add_trace(go.Scatterpolar(r=valores, theta=categorias, fill='toself', name=row['Máquina'], opacity=0.4))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor="rgba(0,0,0,0)", height=450)
        st.plotly_chart(fig_radar, use_container_width=True)
        
    with c8:
        st.markdown("### Emissão Acústica (Ultrassom)")
        fig_ultra = px.bar(status_atual_filt.sort_values('Ultrassom (dB)').tail(15), x="Ultrassom (dB)", y="Máquina", orientation='h', color="Ultrassom (dB)", color_continuous_scale="Purples")
        fig_ultra.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=450, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_ultra, use_container_width=True)

# --- ABA 5: TELEMETRIA IOT ---
with aba5:
    st.markdown("### Estabilidade da Rede Mesh")
    c9, c10 = st.columns(2)
    with c9:
        fig_sinal = px.box(status_atual_filt, x="Setor", y="Sinal (dBm)", color="Setor", title="Intensidade do Sinal Wi-Fi/Mesh")
        fig_sinal.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_sinal, use_container_width=True)
    with c10:
        fig_bat_hist = px.histogram(status_atual_filt, x="Bateria (%)", color="Status", color_discrete_map={"Normal": "#27AE60", "Suspeito": "#F1C40F", "Alerta": "#E67E22", "Grave": "#E74C3C"}, title="Distribuição de Carga Energética")
        fig_bat_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bat_hist, use_container_width=True)

# --- ABA 6: DATA LAKE ---
with aba6:
    st.markdown("### Data Lake (Base Consolidada)")
    
    def color_tabela(row):
        s = row['Status']
        if s == 'Grave': return ['background-color: #FADBD8'] * len(row)
        if s == 'Alerta': return ['background-color: #FDEBD0'] * len(row)
        if s == 'Suspeito': return ['background-color: #FCF3CF'] * len(row)
        return [''] * len(row)
        
    st.dataframe(
        df_hist_filt.head(1000).style.apply(color_tabela, axis=1).format({"Risco (USD)": "${:,.0f}"}), 
        height=600, use_container_width=True, hide_index=True
    )