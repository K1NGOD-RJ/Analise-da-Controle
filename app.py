import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# --- Configuração da Página ---
st.set_page_config(
    page_title="🏭 Dashboard Científico de Produção",
    page_icon="📊",
    layout="wide",
)

# --- URL do CSV ---
url = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_dataframe.csv"

# --- Carregamento dos dados ---
try:
    df = pd.read_csv(
        url.strip(),
        sep=',',
        on_bad_lines='warn',
        encoding='utf-8',
        low_memory=False  # Usa o engine padrão 'c'
    )

    # --- Renomear colunas para padronizar ---
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

    # --- Conversão de tipos ---
    df['QTD'] = pd.to_numeric(df['QTD'], errors='coerce')
    df['QTD_PONDERADA'] = pd.to_numeric(df['QTD_PONDERADA'], errors='coerce')
    df['MES_ENTREGA'] = pd.to_numeric(df['MES_ENTREGA'], errors='coerce')
    df['ANO_ENTREGA'] = pd.to_numeric(df['ANO_ENTREGA'], errors='coerce')
    df['DATA_DE_ENTREGA'] = pd.to_datetime(df['DATA_DE_ENTREGA'], format='%d/%m/%Y', errors='coerce', dayfirst=True)

       # Limpeza
    df = df.dropna(subset=['QTD', 'MES_ENTREGA', 'ANO_ENTREGA', 'RESPONSAVEL', 'EQUIPE', 'DATA_DE_ENTREGA'])
    df = df[df['QTD'] > 0]
    df['MES_ANO'] = df['MES_ANO'].astype(str).str.strip()

    # Padronização de texto: Converter FAMILIA para maiúsculas
    df['FAMILIA'] = df['FAMILIA'].str.upper()

except Exception as e:
    st.error(f"❌ Erro ao carregar o arquivo CSV: {e}")
    st.stop()

# --- ✅ Debug: Totais Reais no CSV ---
st.write("### ✅ Totais Reais no CSV (Verificação)")
total_geral_qtd = df['QTD'].sum()
total_geral_pond = df['QTD_PONDERADA'].sum()
total_2024_qtd = df[df['ANO_ENTREGA'] == 2024]['QTD'].sum()
total_2025_qtd = df[df['ANO_ENTREGA'] == 2025]['QTD'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Geral (QTD)", f"{total_geral_qtd:,.0f}")
col2.metric("Total Ponderado", f"{total_geral_pond:,.0f}")
col3.metric("2024 (QTD)", f"{total_2024_qtd:,.0f}")
col4.metric("2025 (QTD)", f"{total_2025_qtd:,.0f}")

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

# Filtro de Categoria
categorias_disponiveis = sorted(df['CATEGORIA_CONVERSOR'].dropna().unique())
categoria_filtro_ativo = st.sidebar.checkbox("Filtrar por Categoria", value=False)
categorias_selecionadas = categorias_disponiveis if not categoria_filtro_ativo else st.sidebar.multiselect(
    "Categoria", categorias_disponiveis, default=categorias_disponiveis, key="categoria")

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

# --- Métrica: QTD vs QTD_PONDERADA ---
st.sidebar.markdown("### 📊 Métrica de Produção")
use_ponderada = st.sidebar.checkbox("Usar Quantidade Ponderada", value=False)
valor_coluna = 'QTD_PONDERADA' if use_ponderada else 'QTD'
label_metrica = 'Quantidade Ponderada' if use_ponderada else 'Quantidade Bruta (QTD)'

# --- Filtragem do DataFrame ---
mask = (
    (df['ANO_ENTREGA'].isin(anos_selecionados)) &
    (df['MES_ENTREGA'].isin(meses_selecionados)) &
    (df['CATEGORIA_CONVERSOR'].isin(categorias_selecionadas)) &
    (df['RESPONSAVEL'].isin(responsavel_selecionados)) &
    (df['EQUIPE'].isin(equipes_selecionados))
)
df_filtrado = df[mask].copy()

# --- Mostrar Métrica Ativa ---
st.markdown(f"### 📌 Métrica Ativa: **{label_metrica}**")
st.markdown("---")

# --- Comparação 2024 vs 2025 ---
st.subheader("📅 Comparação 2024 vs 2025")
anos_para_comparar = [2024, 2025]
if all(ano in anos_selecionados for ano in anos_para_comparar):
    df_2024 = df[(df['ANO_ENTREGA'] == 2024) & (df['MES_ENTREGA'].isin(meses_selecionados))]
    df_2025 = df[(df['ANO_ENTREGA'] == 2025) & (df['MES_ENTREGA'].isin(meses_selecionados))]

    total_2024 = df_2024[valor_coluna].sum()
    total_2025 = df_2025[valor_coluna].sum()
    media_2024 = df_2024[valor_coluna].mean()
    media_2025 = df_2025[valor_coluna].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Produção 2024", f"{total_2024:,.0f}")
    col2.metric("Produção 2025", f"{total_2025:,.0f}",
                delta=f"{((total_2025/total_2024)-1)*100:+.1f}%" if total_2024 > 0 else "Nova")
    col3.metric("Média por OS (2024)", f"{media_2024:,.0f}")
    col4.metric("Média por OS (2025)", f"{media_2025:,.0f}",
                delta=f"{((media_2025/media_2024)-1)*100:+.1f}%" if media_2024 > 0 else "Nova")

    # Gráfico de Comparação Mensal
    mensal_2024 = df_2024.groupby('MES_ENTREGA')[valor_coluna].sum().reset_index()
    mensal_2025 = df_2025.groupby('MES_ENTREGA')[valor_coluna].sum().reset_index()
    mensal_2024['ANO'] = '2024'
    mensal_2025['ANO'] = '2025'
    comp = pd.concat([mensal_2024, mensal_2025])

    fig_comp = px.line(
        comp,
        x='MES_ENTREGA',
        y=valor_coluna,
        color='ANO',
        markers=True,
        title=f"Comparação Mensal: 2024 vs 2025 ({label_metrica})",
        labels={valor_coluna: 'Quantidade', 'MES_ENTREGA': 'Mês'},
        line_shape='spline'
    )
    fig_comp.update_layout(title_x=0.1)
    st.plotly_chart(fig_comp, use_container_width=True)
else:
    st.info("Para comparar 2024 e 2025, selecione ambos os anos nos filtros.")

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
st.markdown(f"### 🔥 Representatividade por Família ({label_metrica})")
if not df_filtrado.empty:
    fam = df_filtrado.groupby('FAMILIA')[valor_coluna].sum().reset_index().sort_values(valor_coluna, ascending=False)

    # Pie Chart
    fig_fam_pie = px.pie(
        fam,
        names='FAMILIA',
        values=valor_coluna,
        title="Distribuição por Família",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_fam_pie.update_traces(textinfo='percent+label', textposition='inside')
    fig_fam_pie.update_layout(title_x=0.1)
    st.plotly_chart(fig_fam_pie, use_container_width=True)

    # Bar Chart
    fig_fam_bar = px.bar(
        fam,
        x=valor_coluna,
        y='FAMILIA',
        orientation='h',
        title="Produção por Família",
        labels={valor_coluna: label_metrica, 'FAMILIA': 'Família'},
        text=valor_coluna
    )
    fig_fam_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_fam_bar.update_layout(title_x=0.1, height=400)
    st.plotly_chart(fig_fam_bar, use_container_width=True)
else:
    st.info("Nenhum dado para exibir por família.")

# --- Gráfico 1: Produção Diária ---
st.markdown(f"### 1. Produção Diária com Média Móvel (7 dias) - {label_metrica}")
if not df_filtrado.empty:
    daily = df_filtrado.groupby('DATA_DE_ENTREGA')[valor_coluna].sum().reset_index()
    daily = daily.sort_values('DATA_DE_ENTREGA')
    daily['Média Móvel'] = daily[valor_coluna].rolling(window=7).mean()

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=daily['DATA_DE_ENTREGA'], y=daily[valor_coluna], mode='lines+markers', name=label_metrica, line=dict(color='blue')))
    fig1.add_trace(go.Scatter(x=daily['DATA_DE_ENTREGA'], y=daily['Média Móvel'], mode='lines', name='Média Móvel (7 dias)', line=dict(color='red', width=3)))
    fig1.update_layout(title="Produção Diária", xaxis_title="Data", yaxis_title="Quantidade", title_x=0.1, hovermode='x unified')
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a produção diária.")

# --- Gráfico 2: Heatmap Equipe x Categoria ---
st.markdown(f"### 2. Produção por Equipe e Categoria - {label_metrica}")
if not df_filtrado.empty:
    heat = df_filtrado.groupby(['EQUIPE', 'CATEGORIA_CONVERSOR'])[valor_coluna].sum().unstack(fill_value=0)
    fig2 = px.imshow(
        heat,
        labels=dict(x="Categoria", y="Equipe", color="Quantidade"),
        x=heat.columns,
        y=heat.index,
        color_continuous_scale="Blues"
    )
    fig2.update_layout(title="Matriz de Especialização por Equipe", title_x=0.1)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a matriz de especialização.")

# --- Gráfico 3: Top 5 Líderes ---
st.markdown(f"### 3. Top 5 Líderes por Volume - {label_metrica}")
if not df_filtrado.empty:
    top_resp = df_filtrado.groupby('RESPONSAVEL')[valor_coluna].sum().nlargest(5).reset_index()
    top_resp = top_resp.sort_values(valor_coluna, ascending=True)
    fig3 = px.bar(
        top_resp,
        x=valor_coluna,
        y='RESPONSAVEL',
        orientation='h',
        title="Top 5 Líderes por Volume",
        labels={valor_coluna: label_metrica, 'RESPONSAVEL': 'Líder'},
        text=valor_coluna
    )
    fig3.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig3.update_layout(title_x=0.1)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Nenhum dado para exibir os líderes.")

# --- Gráfico 4: Distribuição do Tamanho dos Lotes ---
st.markdown(f"### 4. Distribuição do Tamanho dos Lotes ({label_metrica})")
if not df_filtrado.empty:
    fig4 = px.histogram(
        df_filtrado,
        x=valor_coluna,
        nbins=30,
        title=f"Distribuição do Tamanho dos Lotes de Produção ({label_metrica})",
        labels={valor_coluna: 'Quantidade por OS', 'count': 'Frequência'},
        marginal="box"
    )
    fig4.update_layout(title_x=0.1)
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a distribuição de lotes.")

# --- Gráfico 5: Evolução Mensal por Líder ---
st.markdown(f"### 5. Evolução Mensal por Líder ({label_metrica})")
if not df_filtrado.empty:
    evolucao = df_filtrado.groupby(['MES_ENTREGA', 'RESPONSAVEL'])[valor_coluna].sum().reset_index()
    evolucao = evolucao.sort_values('MES_ENTREGA')
    fig5 = px.line(
        evolucao,
        x='MES_ENTREGA',
        y=valor_coluna,
        color='RESPONSAVEL',
        title="Evolução da Produção por Líder",
        labels={valor_coluna: 'Quantidade', 'MES_ENTREGA': 'Mês', 'RESPONSAVEL': 'Líder'},
        markers=True
    )
    fig5.update_layout(title_x=0.1, xaxis_tickangle=-45)
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a evolução por líder.")

# --- Gráfico 6: Produção por Canal de Venda ---
st.markdown(f"### 6. Produção por Canal de Venda ({label_metrica})")
if not df_filtrado.empty:
    canal = df_filtrado.groupby('CANAL')[valor_coluna].sum().reset_index()
    fig6 = px.pie(
        canal,
        names='CANAL',
        values=valor_coluna,
        title="Distribuição da Produção por Canal de Venda",
        hole=0.4
    )
    fig6.update_traces(textinfo='percent+label')
    fig6.update_layout(title_x=0.1)
    st.plotly_chart(fig6, use_container_width=True)
else:
    st.info("Nenhum dado para exibir por canal.")

# --- Gráfico 7: Heatmap de Produção por Mês e Equipe ---
st.markdown(f"### 7. Produção por Mês e Equipe (Heatmap) - {label_metrica}")
if not df_filtrado.empty:
    heat_month = df_filtrado.groupby(['MES_ENTREGA', 'EQUIPE'])[valor_coluna].sum().unstack(fill_value=0)
    fig7 = px.imshow(
        heat_month,
        labels=dict(x="Equipe", y="Mês", color="Quantidade"),
        x=heat_month.columns,
        y=heat_month.index,
        color_continuous_scale="Greens"
    )
    fig7.update_layout(title="Desempenho Mensal por Equipe", title_x=0.1)
    st.plotly_chart(fig7, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o heatmap mensal.")

# --- Gráfico 8: Tamanho Médio do Lote por Categoria ---
st.markdown(f"### 8. Tamanho Médio do Lote por Categoria ({label_metrica})")
if not df_filtrado.empty:
    avg_qtd = df_filtrado.groupby('CATEGORIA_CONVERSOR')[valor_coluna].mean().reset_index()
    avg_qtd = avg_qtd.sort_values(valor_coluna, ascending=True)
    fig8 = px.bar(
        avg_qtd,
        x=valor_coluna,
        y='CATEGORIA_CONVERSOR',
        orientation='h',
        title="Tamanho Médio do Lote por Categoria",
        labels={valor_coluna: 'Quantidade Média', 'CATEGORIA_CONVERSOR': 'Categoria'},
        text=valor_coluna
    )
    fig8.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig8.update_layout(title_x=0.1)
    st.plotly_chart(fig8, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o tamanho médio por categoria.")

# --- Gráfico 9: Frequência de OS por Líder ---
st.markdown(f"### 9. Frequência de OS por Líder ({label_metrica})")
if not df_filtrado.empty:
    os_count = df_filtrado.groupby('RESPONSAVEL').size().reset_index(name='OS Count')
    os_count = os_count.sort_values('OS Count', ascending=True)
    fig9 = px.bar(
        os_count,
        x='OS Count',
        y='RESPONSAVEL',
        orientation='h',
        title="Número de OS por Líder (Frequência)",
        labels={'OS Count': 'Número de OS', 'RESPONSAVEL': 'Líder'},
        text='OS Count'
    )
    fig9.update_traces(texttemplate='%{text}', textposition='outside')
    fig9.update_layout(title_x=0.1)
    st.plotly_chart(fig9, use_container_width=True)
else:
    st.info("Nenhum dado para exibir frequência por líder.")

# --- Gráfico 10: Scatter - Frequência vs. Tamanho do Lote ---
st.markdown(f"### 10. Frequência vs. Tamanho do Lote por Equipe ({label_metrica})")
if not df_filtrado.empty:
    scatter_data = df_filtrado.groupby('EQUIPE').agg(
        OS_Count=('OS', 'size'),
        Avg_QTD=(valor_coluna, 'mean')
    ).reset_index()
    fig10 = px.scatter(
        scatter_data,
        x='OS_Count',
        y='Avg_QTD',
        size='OS_Count',
        color='EQUIPE',
        title="Frequência de OS vs. Tamanho Médio do Lote por Equipe",
        labels={'OS_Count': 'Número de OS', 'Avg_QTD': 'Tamanho Médio do Lote'},
        hover_data=['EQUIPE']
    )
    fig10.update_layout(title_x=0.1)
    st.plotly_chart(fig10, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o gráfico de dispersão.")

# --- Gráfico 11: Produção Acumulada por Equipe ---
st.markdown(f"### 11. Produção Acumulada por Equipe ao Longo do Tempo ({label_metrica})")
if not df_filtrado.empty:
    cumulativo = df_filtrado.groupby(['MES_ENTREGA', 'EQUIPE'])[valor_coluna].sum().reset_index()
    cumulativo = cumulativo.sort_values(['EQUIPE', 'MES_ENTREGA'])
    cumulativo['QTD Acumulada'] = cumulativo.groupby('EQUIPE')[valor_coluna].cumsum()
    fig11 = px.line(
        cumulativo,
        x='MES_ENTREGA',
        y='QTD Acumulada',
        color='EQUIPE',
        title="Produção Acumulada por Equipe",
        labels={'QTD Acumulada': 'Produção Acumulada', 'MES_ENTREGA': 'Mês'},
        markers=True
    )
    fig11.update_layout(title_x=0.1, xaxis_tickangle=-45)
    st.plotly_chart(fig11, use_container_width=True)
else:
    st.info("Nenhum dado para exibir produção acumulada.")

# --- Gráfico 12: Boxplot da QTD por Categoria ---
st.markdown(f"### 12. Distribuição da {label_metrica} por Categoria (Boxplot)")
if not df_filtrado.empty:
    fig12 = px.box(
        df_filtrado,
        x='CATEGORIA_CONVERSOR',
        y=valor_coluna,
        title="Distribuição da Quantidade por Categoria",
        labels={valor_coluna: 'Quantidade', 'CATEGORIA_CONVERSOR': 'Categoria'},
        color='CATEGORIA_CONVERSOR',
        category_orders={"CATEGORIA_CONVERSOR": df_filtrado['CATEGORIA_CONVERSOR'].value_counts().index.tolist()}
    )
    fig12.update_layout(title_x=0.1, showlegend=False)
    st.plotly_chart(fig12, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o boxplot.")

# --- Tabela Detalhada ---
st.subheader("📋 Dados Detalhados")
if not df_filtrado.empty:
    cols_to_show = ['OS', 'PRODUTO', 'QTD', 'QTD_PONDERADA', 'DATA_DE_ENTREGA', 'EQUIPE', 'RESPONSAVEL', 'CANAL', 'CATEGORIA_CONVERSOR', 'FAMILIA']
    st.dataframe(df_filtrado[cols_to_show].sort_values('DATA_DE_ENTREGA', ascending=False))
else:
    st.info("Nenhum dado corresponde aos filtros selecionados.")

# --- Diagnóstico Final ---
st.markdown("---")
st.write("### 🔍 Diagnóstico do DataFrame")
st.write(f"**Número de linhas:** {len(df)}")
st.write(f"**Número de colunas:** {len(df.columns)}")
st.write(f"**Colunas:** {list(df.columns)}")

st.caption("📊 Dashboard científico de produção. Atualizado com base no arquivo `updated_dataframe.csv`.")
