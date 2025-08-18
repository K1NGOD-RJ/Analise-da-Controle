import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# --- Configuração da Página ---
st.set_page_config(
    page_title="🏭 Dashboard Científico de Produção",
    page_icon="📊",
    layout="wide",
)

# --- Modo Escuro/Light Mode Toggle ---
st.sidebar.markdown("### 🎨 Aparência")
use_dark_mode = st.sidebar.checkbox("🌙 Modo Escuro", value=True)

# Define cores com base no tema
if use_dark_mode:
    bg_color = "#0E1117"
    text_color = "#FAFAFA"
    sec_bg = "#1E293B"
    primary_color = "#1f77b4"
else:
    bg_color = "#FFFFFF"
    text_color = "#000000"
    sec_bg = "#F0F2F6"
    primary_color = "#1f77b4"

# --- Estilo CSS Dinâmico com Sidebar e Todos os Elementos ---
st.markdown(f"""
<style>
    /* Fundo e texto principal */
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {bg_color};
        color: {text_color};
        border-right: 1px solid #333;
    }}

    /* Títulos no sidebar */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {{
        color: {text_color} !important;
    }}

    /* Texto no sidebar */
    [data-testid="stSidebar"] .css-1v3fvcr, 
    [data-testid="stSidebar"] .css-1v02yyg,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {{
        color: {text_color} !important;
    }}

    /* Inputs, checkboxes, selects no sidebar */
    [data-testid="stSidebar"] .stCheckbox > label,
    [data-testid="stSidebar"] .stRadio > label,
    [data-testid="stSidebar"] .stSelectbox > label,
    [data-testid="stSidebar"] .stTextInput > label,
    [data-testid="stSidebar"] .stNumberInput > label {{
        color: {text_color} !important;
    }}

    /* Inputs themselves */
    [data-testid="stSidebar"] .stTextInput > div > div > input,
    [data-testid="stSidebar"] .stNumberInput > div > div > input,
    [data-testid="stSidebar"] .stSelectbox > div > div > div {{
        background-color: {'#1E293B' if use_dark_mode else 'white'} !important;
        color: {text_color} !important;
        border: 1px solid #444;
    }}

    /* Hover effect nos botões */
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: #1a6ec0;
        color: white;
    }}

    /* Expander (info tooltips) */
    .st-expander {{
        background-color: {sec_bg};
        border: 1px solid #444;
    }}
    .st-expander > div > p {{
        color: {text_color};
    }}

    /* Títulos e textos gerais */
    h1, h2, h3, h4, h5, h6, p, div, span, label {{
        color: {text_color} !important;
    }}

    /* Botões principais */
    .stButton>button {{
        background-color: {primary_color};
        color: white;
        border: none;
        border-radius: 5px;
    }}
    .stButton>button:hover {{
        background-color: #1a6ec0;
        color: white;
    }}

    /* Métricas (KPIs) */
    .stMetricLabel, .stMetricValue {{
        color: {text_color} !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- URLs dos CSVs ---
url_data = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_dataframe.csv"
url_log = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_dataframe_log.csv"

# --- Carregamento dos dados principais ---
try:
    df = pd.read_csv(url_data.strip(), sep=',', on_bad_lines='warn', encoding='utf-8', low_memory=False)
    # Renomear colunas
    df = df.rename(columns={
        'DATA DE ENTREGA': 'DATA_DE_ENTREGA',
        'ANO-MES entrega': 'MES_ANO',
        'MES ENTREGA': 'MES_ENTREGA',
        'ANO ENTREGA': 'ANO_ENTREGA',
        'CATEGORIA CONVERSOR': 'CATEGORIA_CONVERSOR',
        'FAMILIA1': 'FAMILIA',
        'QUANTIDADE PONDERADA': 'QTD_PONDERADA',
        'OS UNICA': 'OS_UNICA',
        'CODIGO/CLIENTE': 'CODIGO_CLIENTE',
        'PRODUTO': 'PRODUTO',
        'CANAL': 'CANAL',
        'STATUS': 'STATUS'
    })

    # Conversão de tipos
    df['QTD'] = pd.to_numeric(df['QTD'], errors='coerce')
    df['QTD_PONDERADA'] = pd.to_numeric(df['QTD_PONDERADA'], errors='coerce')
    df['MES_ENTREGA'] = pd.to_numeric(df['MES_ENTREGA'], errors='coerce')
    df['ANO_ENTREGA'] = pd.to_numeric(df['ANO_ENTREGA'], errors='coerce')
    df['DATA_DE_ENTREGA'] = pd.to_datetime(df['DATA_DE_ENTREGA'], format='%d/%m/%Y', errors='coerce', dayfirst=True)

    # Limpeza
    df = df.dropna(subset=['QTD', 'ANO_ENTREGA', 'RESPONSAVEL', 'EQUIPE', 'DATA_DE_ENTREGA'])
    df = df[df['QTD'] > 0]

    # ✅ CORREÇÃO: Reconstruir MES_ANO a partir da data real
    df['MES_ANO'] = df['DATA_DE_ENTREGA'].dt.to_period('M').astype(str)

    # Padronização de texto
    df['FAMILIA'] = df['FAMILIA'].str.upper()

except Exception as e:
    st.error(f"❌ Erro ao carregar o arquivo de dados: {e}")
    st.stop()

# --- Carregar dados de capacidade (log) ---
try:
    log = pd.read_csv(url_log.strip(), sep=',', encoding='utf-8')
    log['MES_ANO'] = log['MES_ANO'].astype(str)
    # Garantir que PPDT esteja calculado
    log['PPDT'] = log['producao_real'] / (log['numero_funcionarios'] * log['dias_trabalhados'])
    log['ShiftFactor'] = log['ShiftFactor'].fillna(1.0)
except Exception as e:
    st.warning("⚠️ Dados de capacidade não carregados. Digital Twin será baseado em projeção simples.")
    log = None

# --- Métrica: QTD vs QTD_PONDERADA ---
st.sidebar.markdown("### 📊 Métrica de Produção")
use_ponderada = st.sidebar.checkbox("Usar Quantidade Ponderada", value=False)
valor_coluna = 'QTD_PONDERADA' if use_ponderada else 'QTD'
label_metrica = 'Quantidade Ponderada' if use_ponderada else 'Quantidade Bruta (QTD)'

# --- Barra Lateral: Filtros ---
st.sidebar.header("🔍 Filtros")

if st.sidebar.button("🔄 Resetar Filtros"):
    st.session_state.clear()
    st.rerun()

# Filtro de Ano
anos_disponiveis = sorted(df['ANO_ENTREGA'].dropna().unique().astype(int))
ano_filtro_ativo = st.sidebar.checkbox("Filtrar por Ano", value=False)
anos_selecionados = anos_disponiveis if not ano_filtro_ativo else st.sidebar.multiselect(
    "Ano", anos_disponiveis, default=anos_disponiveis, key="anos")

# Filtro de Mês
meses_disponiveis = sorted(df['MES_ENTREGA'].dropna().unique())
mes_filtro_ativo = st.sidebar.checkbox("Filtrar por Mês", value=False)
meses_selecionados = meses_disponiveis if not mes_filtro_ativo else st.sidebar.multiselect(
    "Mês", meses_disponiveis, default=meses_disponiveis, key="mes")

# Filtro por Responsável
responsavel_disponiveis = sorted(df['RESPONSAVEL'].dropna().unique())
responsavel_filtro_ativo = st.sidebar.checkbox("Filtrar por Responsável", value=False)
responsavel_selecionados = responsavel_disponiveis if not responsavel_filtro_ativo else st.sidebar.multiselect(
    "Responsável", responsavel_disponiveis, default=responsavel_disponiveis, key="responsavel")

# Filtro por Equipe
equipes_disponiveis = sorted(df['EQUIPE'].dropna().unique())
equipe_filtro_ativo = st.sidebar.checkbox("Filtrar por Equipe", value=False)
equipes_selecionados = equipes_disponiveis if not equipe_filtro_ativo else st.sidebar.multiselect(
    "Equipe", equipes_disponiveis, default=equipes_disponiveis, key="equipe")

# --- Filtragem do DataFrame ---
mask = (
    (df['ANO_ENTREGA'].isin(anos_selecionados)) &
    (df['MES_ENTREGA'].isin(meses_selecionados)) &
    (df['RESPONSAVEL'].isin(responsavel_selecionados)) &
    (df['EQUIPE'].isin(equipes_selecionados))
)
df_filtrado = df[mask].copy()

# --- Função auxiliar: Botão de Info (i) com explicação ---
def info_tooltip(label, text):
    with st.container():
        col_i, col_c = st.columns([1, 20])
        with col_i:
            st.markdown(f"<h4 style='text-align: center; margin: 0;'>ℹ️</h4>", unsafe_allow_html=True)
        with col_c:
            st.markdown(label)
        with st.expander("📘 Como ler este gráfico"):
            st.markdown(text)

# --- Exportar Relatório PDF ---
if st.sidebar.button("🖨️ Gerar Relatório Completo (PDF)"):
    if df_filtrado.empty:
        st.sidebar.warning("Nenhum dado para gerar relatório.")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Relatório de Produção", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(0, 10, f"Métrica: {label_metrica}", ln=True)
        pdf.ln(10)

        # Adicionar métricas
        total = df_filtrado[valor_coluna].sum()
        media = df_filtrado[valor_coluna].mean()
        num_os = len(df_filtrado)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Métricas Gerais", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Produção Total: {total:,.0f}", ln=True)
        pdf.cell(0, 10, f"Média por OS: {media:,.0f}", ln=True)
        pdf.cell(0, 10, f"Total de OS: {num_os:,}", ln=True)
        pdf.ln(10)

        # Função para adicionar gráfico ao PDF
        def add_fig_to_pdf(fig, title):
            buf = BytesIO()
            fig.write_image(buf, format="png", width=1000, height=600, scale=2)
            buf.seek(0)
            image = Image.open(buf)
            temp_file = "/tmp/temp_plot.png"
            image.save(temp_file)
            pdf.image(temp_file, x=10, w=180)
            pdf.ln(5)

        # 1. Produção Diária
        if not df_filtrado.empty:
            daily = df_filtrado.groupby('DATA_DE_ENTREGA')[valor_coluna].sum().reset_index()
            daily['Média Móvel'] = daily[valor_coluna].rolling(window=7).mean()
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=daily['DATA_DE_ENTREGA'], y=daily[valor_coluna], mode='lines+markers', name=label_metrica))
            fig1.add_trace(go.Scatter(x=daily['DATA_DE_ENTREGA'], y=daily['Média Móvel'], mode='lines', name='Média Móvel'))
            fig1.update_layout(title="Produção Diária")
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "1. Produção Diária com Média Móvel", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, "Mostra a produção diária com tendência de 7 dias.", ln=True)
            add_fig_to_pdf(fig1, "Produção Diária")

        # 2. Heatmap Equipe x Categoria
        if not df_filtrado.empty:
            heat = df_filtrado.groupby(['EQUIPE', 'CATEGORIA_CONVERSOR'])[valor_coluna].sum().unstack(fill_value=0)
            fig2 = px.imshow(heat, color_continuous_scale="Blues", title="Produção por Equipe e Categoria")
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "2. Produção por Equipe e Categoria", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, "Mapa de calor que mostra especialização por equipe e categoria.", ln=True)
            add_fig_to_pdf(fig2, "Heatmap")

        # Salvar PDF
        pdf_output = "relatorio_producao.pdf"
        pdf.output(pdf_output)

        with open(pdf_output, "rb") as f:
            st.sidebar.download_button(
                label="📥 Baixar Relatório (PDF)",
                data=f,
                file_name="relatorio_producao.pdf",
                mime="application/pdf"
            )

# --- Mostrar Métrica Ativa ---
st.markdown(f"### 📌 Métrica Ativa: **{label_metrica}**")
st.markdown("---")

# --- Título ---
st.title("🏭 Dashboard Científico de Produção")
st.markdown("Análise avançada da linha de produção com métricas de desempenho, tendências e eficiência.")

# --- Métricas Gerais ---
st.subheader("📈 Métricas Gerais")

if not df_filtrado.empty:
    total = df_filtrado[valor_coluna].sum()
    media = df_filtrado[valor_coluna].mean()
    num_os = len(df_filtrado)
    categoria_top = df_filtrado['CATEGORIA_CONVERSOR'].mode().iloc[0] if not df_filtrado['CATEGORIA_CONVERSOR'].mode().empty else "N/A"
else:
    total = media = num_os = 0
    categoria_top = "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Produção Total", f"{total:,.0f}")
col2.metric("Média por OS", f"{media:,.0f}")
col3.metric("Total de OS", f"{num_os:,}")
col4.metric("Categoria Dominante", categoria_top)

st.markdown("---")

# --- NOVO GRÁFICO: Representatividade por Família ---
info_tooltip(
    f"### 🔥 Representatividade por Família ({label_metrica})",
    "Mostra a participação de cada família de produtos na produção total. "
    "Ajuda a identificar quais famílias são mais relevantes e merecem foco."
)
if not df_filtrado.empty:
    fam = df_filtrado.groupby('FAMILIA')[valor_coluna].sum().reset_index().sort_values(valor_coluna, ascending=False)
    fig_fam_pie = px.pie(fam, names='FAMILIA', values=valor_coluna, title="Distribuição por Família", hole=0.4)
    fig_fam_pie.update_traces(textinfo='percent+label', textposition='inside')
    fig_fam_pie.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig_fam_pie, use_container_width=True)
else:
    st.info("Nenhum dado para exibir por família.")

# --- Gráfico 1: Produção Diária ---
info_tooltip(
    f"### 1. Produção Diária com Média Móvel (7 dias) - {label_metrica}",
    "Mostra a produção diária com uma linha de tendência (média móvel de 7 dias). "
    "Ajuda a identificar picos e quedas reais, filtrando ruídos diários."
)
if not df_filtrado.empty:
    daily = df_filtrado.groupby('DATA_DE_ENTREGA')[valor_coluna].sum().reset_index()
    daily = daily.sort_values('DATA_DE_ENTREGA')
    daily['Média Móvel'] = daily[valor_coluna].rolling(window=7).mean()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=daily['DATA_DE_ENTREGA'], y=daily[valor_coluna], mode='lines+markers', name=label_metrica, line=dict(color='blue')))
    fig1.add_trace(go.Scatter(x=daily['DATA_DE_ENTREGA'], y=daily['Média Móvel'], mode='lines', name='Média Móvel (7 dias)', line=dict(color='red', width=3)))
    fig1.update_layout(
        title="Produção Diária",
        xaxis_title="Data",
        yaxis_title="Quantidade",
        title_x=0.1,
        hovermode='x unified',
        template="plotly_dark" if use_dark_mode else "plotly_white"
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a produção diária.")

# --- Gráfico 2: Heatmap Equipe x Categoria ---
info_tooltip(
    f"### 2. Produção por Equipe e Categoria - {label_metrica}",
    "Mapa de calor que mostra quanto cada equipe produz em cada categoria. "
    "Ajuda a identificar especialização e oportunidades de realinhamento."
)
if not df_filtrado.empty:
    heat = df_filtrado.groupby(['EQUIPE', 'CATEGORIA_CONVERSOR'])[valor_coluna].sum().unstack(fill_value=0)
    fig2 = px.imshow(heat, labels=dict(x="Categoria", y="Equipe"), color_continuous_scale="Blues")
    fig2.update_layout(title="Matriz de Especialização por Equipe", template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a matriz de especialização.")

# --- Gráfico 3: Top 5 Líderes ---
info_tooltip(
    f"### 3. Top 5 Líderes por Volume - {label_metrica}",
    "Os 5 líderes com maior volume de produção. "
    "Use para reconhecimento e análise de desempenho."
)
if not df_filtrado.empty:
    top_resp = df_filtrado.groupby('RESPONSAVEL')[valor_coluna].sum().nlargest(5).reset_index()
    top_resp = top_resp.sort_values(valor_coluna, ascending=True)
    fig3 = px.bar(top_resp, x=valor_coluna, y='RESPONSAVEL', orientation='h', title="Top 5 Líderes por Volume", text=valor_coluna)
    fig3.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig3.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Nenhum dado para exibir os líderes.")

# --- Gráfico 4: Distribuição do Tamanho dos Lotes ---
info_tooltip(
    f"### 4. Distribuição do Tamanho dos Lotes ({label_metrica})",
    "Histograma que mostra como os tamanhos dos lotes estão distribuídos. "
    "Boxplot acima mostra outliers (valores extremos)."
)
if not df_filtrado.empty:
    fig4 = px.histogram(df_filtrado, x=valor_coluna, nbins=30, marginal="box", title=f"Distribuição do Tamanho dos Lotes de Produção ({label_metrica})")
    fig4.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a distribuição de lotes.")

# --- Gráfico 5: Evolução Mensal por Líder ---
info_tooltip(
    f"### 5. Evolução da Produção por Líder ao Longo do Tempo ({label_metrica})",
    "Linha por líder mostrando evolução mensal contínua (com ano). "
    "Ajuda a ver tendências de crescimento ou queda."
)
if not df_filtrado.empty:
    df_filtrado['ANO_MES_DT'] = pd.to_datetime(df_filtrado['MES_ANO'] + "-01", format='%Y-%m-%d', errors='coerce')
    evolucao = df_filtrado.groupby(['ANO_MES_DT', 'RESPONSAVEL'])[valor_coluna].sum().reset_index()
    evolucao = evolucao.sort_values('ANO_MES_DT')
    fig5 = px.line(evolucao, x='ANO_MES_DT', y=valor_coluna, color='RESPONSAVEL', markers=True, title="Evolução da Produção por Líder")
    fig5.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white", hovermode='x unified')
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a evolução por líder.")

# --- Gráfico 6: Produção por Canal de Venda ---
info_tooltip(
    f"### 6. Produção por Canal de Venda ({label_metrica})",
    "Gráfico de pizza mostrando a participação de cada canal (Site, Atacado, etc). "
    "Ajuda a entender de onde vem a demanda."
)
if not df_filtrado.empty:
    canal = df_filtrado.groupby('CANAL')[valor_coluna].sum().reset_index()
    fig6 = px.pie(canal, names='CANAL', values=valor_coluna, title="Distribuição da Produção por Canal de Venda", hole=0.4)
    fig6.update_traces(textinfo='percent+label')
    fig6.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig6, use_container_width=True)
else:
    st.info("Nenhum dado para exibir por canal.")

# --- Gráfico 7: Heatmap de Produção por Mês e Equipe ---
info_tooltip(
    f"### 7. Produção por Mês e Equipe (Heatmap) - {label_metrica}",
    "Mapa de calor com produção por mês e equipe. "
    "Identifica sazonalidade e desempenho relativo."
)
if not df_filtrado.empty:
    heat_month = df_filtrado.groupby(['MES_ENTREGA', 'EQUIPE'])[valor_coluna].sum().unstack(fill_value=0)
    fig7 = px.imshow(heat_month, labels=dict(x="Equipe", y="Mês"), color_continuous_scale="Greens")
    fig7.update_layout(title="Desempenho Mensal por Equipe", template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig7, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o heatmap mensal.")

# --- Gráfico 8: Tamanho Médio do Lote por Categoria ---
info_tooltip(
    f"### 8. Tamanho Médio do Lote por Categoria ({label_metrica})",
    "Mostra o tamanho médio dos lotes por categoria. "
    "Ajuda a entender complexidade e planejamento."
)
if not df_filtrado.empty:
    avg_qtd = df_filtrado.groupby('CATEGORIA_CONVERSOR')[valor_coluna].mean().reset_index()
    avg_qtd = avg_qtd.sort_values(valor_coluna, ascending=True)
    fig8 = px.bar(avg_qtd, x=valor_coluna, y='CATEGORIA_CONVERSOR', orientation='h', title="Tamanho Médio do Lote por Categoria", text=valor_coluna)
    fig8.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig8.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig8, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o tamanho médio por categoria.")

# --- Gráfico 9: Frequência de OS por Líder ---
info_tooltip(
    f"### 9. Frequência de OS por Líder ({label_metrica})",
    "Número total de OS por líder (não volume). "
    "Mostra engajamento e distribuição de carga."
)
if not df_filtrado.empty:
    os_count = df_filtrado.groupby('RESPONSAVEL').size().reset_index(name='OS Count')
    os_count = os_count.sort_values('OS Count', ascending=True)
    fig9 = px.bar(os_count, x='OS Count', y='RESPONSAVEL', orientation='h', title="Número de OS por Líder (Frequência)", text='OS Count')
    fig9.update_traces(texttemplate='%{text}', textposition='outside')
    fig9.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig9, use_container_width=True)
else:
    st.info("Nenhum dado para exibir frequência por líder.")

# --- Gráfico 10: Scatter - Frequência vs. Tamanho do Lote ---
info_tooltip(
    f"### 10. Frequência vs. Tamanho do Lote por Equipe ({label_metrica})",
    "Gráfico de dispersão: quanto maior o ponto, mais OS a equipe fez. "
    "Equipes no canto superior direito são altamente produtivas."
)
if not df_filtrado.empty:
    scatter_data = df_filtrado.groupby('EQUIPE').agg(OS_Count=('OS', 'size'), Avg_QTD=(valor_coluna, 'mean')).reset_index()
    fig10 = px.scatter(scatter_data, x='OS_Count', y='Avg_QTD', size='OS_Count', color='EQUIPE', title="Frequência de OS vs. Tamanho Médio do Lote por Equipe")
    fig10.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig10, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o gráfico de dispersão.")

# --- Gráfico 11: Produção Acumulada por Equipe ---
info_tooltip(
    f"### 11. Produção Acumulada por Equipe ao Longo do Tempo ({label_metrica})",
    "Mostra como cada equipe acumula produção ao longo dos meses. "
    "Pendências indicam ritmo de trabalho."
)
if not df_filtrado.empty:
    cumulativo = df_filtrado.groupby(['MES_ENTREGA', 'EQUIPE'])[valor_coluna].sum().reset_index()
    cumulativo['QTD Acumulada'] = cumulativo.groupby('EQUIPE')[valor_coluna].cumsum()
    fig11 = px.line(cumulativo, x='MES_ENTREGA', y='QTD Acumulada', color='EQUIPE', markers=True, title="Produção Acumulada por Equipe")
    fig11.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white", hovermode='x unified')
    st.plotly_chart(fig11, use_container_width=True)
else:
    st.info("Nenhum dado para exibir produção acumulada.")

# --- Gráfico 12: Boxplot da QTD por Categoria ---
info_tooltip(
    f"### 12. Distribuição da {label_metrica} por Categoria (Boxplot)",
    "Boxplot mostra mediana, quartis e outliers por categoria. "
    "Ajuda a comparar variabilidade entre categorias."
)
if not df_filtrado.empty:
    fig12 = px.box(df_filtrado, x='CATEGORIA_CONVERSOR', y=valor_coluna, color='CATEGORIA_CONVERSOR', title="Distribuição da Quantidade por Categoria")
    fig12.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white", showlegend=False)
    st.plotly_chart(fig12, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o boxplot.")

# --- Pareto por Família ---
info_tooltip(
    f"### 🎯 Pareto por Família ({label_metrica})",
    "Mostra quais famílias de produtos representam 80% da produção. "
    "Ajuda a focar recursos nas famílias mais relevantes."
)
if not df_filtrado.empty:
    pareto_fam = df_filtrado.groupby('FAMILIA')[valor_coluna].sum().sort_values(ascending=False).reset_index()
    pareto_fam['cumsum'] = pareto_fam[valor_coluna].cumsum() / pareto_fam[valor_coluna].sum() * 100
    fig_pareto_fam = px.line(pareto_fam, x='FAMILIA', y='cumsum', markers=True, title="Acumulado de Produção por Família (80/20)")
    fig_pareto_fam.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80%")
    fig_pareto_fam.update_layout(template="plotly_dark" if use_dark_mode else "plotly_white")
    st.plotly_chart(fig_pareto_fam, use_container_width=True)
else:
    st.info("Nenhum dado para Pareto por família.")

# --- 8. Digital Twin: Projeção por Mês (com SDOR corrigido) ---
info_tooltip(
    "### 💡 8. Digital Twin: Projeção por Mês",
    "Simula a produção futura com base no SDOR (Produtividade Padrão por Funcionário por Dia), "
    "ajustado pelo turno. Use para planejar contratações, dias úteis e mudanças de turno."
)

if log is not None and not df_filtrado.empty:
    # ✅ Usar SDOR médio dos últimos meses (base ajustada)
    if len(log) >= 3:
        sdor_base = log['SDOR'].tail(3).mean()
    else:
        sdor_base = log['SDOR'].iloc[-1] if len(log) > 0 else 70  # fallback

    st.markdown(f"**📊 Produtividade Base (SDOR):** {sdor_base:.1f} unidades por funcionário por dia")
    st.markdown("*Valor ajustado para remover o efeito do turno. Serve como base para projeções.*")

    # Próximos 3 meses
    last_date = df_filtrado['DATA_DE_ENTREGA'].max()
    next_months = pd.date_range(last_date, periods=4, freq='MS')[1:4]
    month_names = [date.strftime('%b/%Y') for date in next_months]

    # Inputs por mês
    proj_data = []
    col1, col2, col3 = st.columns(3)
    months_cols = [col1, col2, col3]

    shift_map = {"1 Turno": 1.0, "2 Turno": 1.15, "1 Turno Com Extra": 1.2}

    for i, col in enumerate(months_cols):
        with col:
            st.markdown(f"**📅 {month_names[i]}**")
            func = st.number_input(f"Funcionários", min_value=1, value=int(log['numero_funcionarios'].iloc[-1]), key=f"func_{i}")
            dias = st.number_input(f"Dias úteis", min_value=1, value=int(log['dias_trabalhados'].iloc[-1]), key=f"dias_{i}")
            turno = st.selectbox(f"Turno", ["1 Turno", "2 Turno", "1 Turno Com Extra"], index=0, key=f"turno_{i}")
            shift_factor = shift_map[turno]

            # ✅ Projeção: SDOR × shift_factor × func × dias
            proj_qtd = sdor_base * shift_factor * func * dias
            proj_data.append({
                "MES_ANO": next_months[i].strftime('%Y-%m'),
                "Produção": round(proj_qtd),
                "Tipo": "Projeção",
                "Turno": turno
            })

    # Histórico (últimos 6 meses)
    hist = df_filtrado.groupby('MES_ANO')[valor_coluna].sum().reset_index()
    hist = hist.tail(6)
    hist["Tipo"] = "Real"
    hist.rename(columns={valor_coluna: "Produção"}, inplace=True)
    hist['MES_ANO'] = pd.to_datetime(hist['MES_ANO'] + "-01")

    # Combinar histórico + projeção
    combined = pd.concat([hist, pd.DataFrame(proj_data)], ignore_index=True)
    combined['MES_ANO'] = pd.to_datetime(combined['MES_ANO'])

    # Gráfico
    fig_sim = px.line(
        combined,
        x='MES_ANO',
        y='Produção',
        color='Tipo',
        markers=True,
        line_dash='Tipo',
        title="Digital Twin: Projeção Mensal com Parâmetros Personalizados",
        labels={'Produção': 'Quantidade', 'MES_ANO': 'Mês'},
        line_shape='spline'
    )
    fig_sim.update_layout(
        xaxis=dict(tickformat="%b %Y", dtick="M1"),
        hovermode='x unified',
        template="plotly_dark" if use_dark_mode else "plotly_white"
    )
    st.plotly_chart(fig_sim, use_container_width=True)

    # Tabela de projeção
    st.markdown("### 📋 Resumo da Projeção")
    proj_df = pd.DataFrame(proj_data)
    proj_df['Produção'] = proj_df['Produção'].map('{:,.0f}'.format)
    st.dataframe(proj_df[['MES_ANO', 'Produção', 'Turno']].rename(columns={
        "MES_ANO": "Mês",
        "Produção": "Produção Projetada",
        "Turno": "Turno"
    }))

else:
    st.info("Dados de capacidade não disponíveis. Preencha `updated_dataframe_log.csv`.")

# --- Tabela Detalhada ---
st.subheader("📋 Dados Detalhados")
if not df_filtrado.empty:
    cols_show = ['OS', 'PRODUTO', 'QTD', 'QTD_PONDERADA', 'DATA_DE_ENTREGA', 'EQUIPE', 'RESPONSAVEL', 'CANAL', 'FAMILIA']
    st.dataframe(df_filtrado[cols_show].sort_values('DATA_DE_ENTREGA', ascending=False), use_container_width=True)
else:
    st.info("Nenhum dado corresponde aos filtros selecionados.")

# --- Diagnóstico Final ---
st.markdown("---")
st.write("### 🔍 Diagnóstico do DataFrame")
st.write(f"**Número de linhas:** {len(df)}")
st.write(f"**Número de colunas:** {len(df.columns)}")
st.write(f"**Colunas:** {list(df.columns)}")

st.caption("📊 Dashboard científico de produção. Atualizado com base nos arquivos `updated_dataframe.csv` e `updated_dataframe_log.csv`.")