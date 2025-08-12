import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF

# --- Configuração da Página ---
st.set_page_config(
    page_title="🏭 Dashboard Científico de Produção",
    page_icon="📊",
    layout="wide",
)

# --- Definição das colunas ---
col_names = [
    "ID", "OS", "OS UNICA", "FINAL", "EQUIPE", "RESPONSAVEL", "CANAL", "STATUS",
    "CODIGO/CLIENTE", "PRODUTO", "QTD", "DATA DE ENTREGA", "SEMANA NO ANO", "MES ENTREGA",
    "ANO ENTREGA", "MES_ANO", "CATEGORIA CONVERSOR", "QUANTIDADE PONDERADA"
]

# --- Carregamento dos dados ---
try:
    # 🔥 CRITICAL: Remove extra space in URL
    df = pd.read_csv(
        "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/refs/heads/main/controle_limpo.csv",
        sep=',',
        decimal=',',
        thousands='.',
        header=None,
        names=col_names,
        on_bad_lines='skip',
        engine='python'
    )

    # --- Conversão de tipos ---
    df['QTD'] = pd.to_numeric(df['QTD'], errors='coerce')
    df['MES ENTREGA'] = pd.to_numeric(df['MES ENTREGA'], errors='coerce')
    df['ANO ENTREGA'] = pd.to_numeric(df['ANO ENTREGA'], errors='coerce')
    df['DATA DE ENTREGA'] = pd.to_datetime(df['DATA DE ENTREGA'], format='%d/%m/%Y', errors='coerce')

    # Remove linhas com dados inválidos
    df = df.dropna(subset=['QTD', 'MES ENTREGA', 'ANO ENTREGA', 'RESPONSAVEL', 'EQUIPE'])
    df = df[df['QTD'] > 0]

    # Garante que MES_ANO está como string
    df['MES_ANO'] = df['MES_ANO'].astype(str).str.strip()

    # Cria coluna de ordenação temporal
    df['DATA_ORD'] = df['ANO ENTREGA'] * 12 + df['MES ENTREGA']

except Exception as e:
    st.error(f"❌ Erro ao carregar o arquivo CSV: {e}")
    st.stop()

# --- Barra Lateral (Filtros) ---
st.sidebar.header("🔍 Filtros")

# Filtro de Ano
anos_disponiveis = sorted(df['ANO ENTREGA'].unique().astype(int))
anos_selecionados = st.sidebar.multiselect("Ano", anos_disponiveis, default=anos_disponiveis)

# Filtro de Mês-Ano
mes_ano_disponiveis = sorted(df['MES_ANO'].unique())
mes_ano_selecionados = st.sidebar.multiselect("Mês-Ano", mes_ano_disponiveis, default=mes_ano_disponiveis)

# Filtro de Categoria
categorias_disponiveis = sorted(df['CATEGORIA CONVERSOR'].dropna().unique())
categorias_selecionadas = st.sidebar.multiselect("Categoria", categorias_disponiveis, default=categorias_disponiveis)

# Filtro por Responsável
responsavel_disponiveis = sorted(df['RESPONSAVEL'].dropna().unique())
responsavel_selecionados = st.sidebar.multiselect("Responsável", responsavel_disponiveis, default=responsavel_disponiveis)

# Filtro por Equipe
equipes_disponiveis = sorted(df['EQUIPE'].dropna().unique())
equipes_selecionados = st.sidebar.multiselect("Equipe", equipes_disponiveis, default=equipes_disponiveis)

# --- Filtragem do DataFrame ---
df_filtrado = df[
    (df['ANO ENTREGA'].isin(anos_selecionados)) &
    (df['MES_ANO'].isin(mes_ano_selecionados)) &
    (df['CATEGORIA CONVERSOR'].isin(categorias_selecionadas)) &
    (df['RESPONSAVEL'].isin(responsavel_selecionados)) &
    (df['EQUIPE'].isin(equipes_selecionados))
]

# --- Título ---
st.title("🏭 Dashboard Científico de Produção")
st.markdown("Análise avançada da linha de produção com métricas de desempenho, tendências e eficiência.")

# --- Métricas Gerais ---
st.subheader("📈 Métricas Gerais")

if not df_filtrado.empty:
    total_qtd = df_filtrado['QTD'].sum()
    media_qtd = df_filtrado['QTD'].mean()
    num_os = len(df_filtrado)
    categoria_top = df_filtrado['CATEGORIA CONVERSOR'].mode().iloc[0] if not df_filtrado['CATEGORIA CONVERSOR'].mode().empty else "N/A"
else:
    total_qtd = media_qtd = num_os = 0
    categoria_top = "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Produção Total (QTD)", f"{total_qtd:,.0f}")
col2.metric("Média por OS", f"{media_qtd:,.0f}")
col3.metric("Total de OS", f"{num_os:,}")
col4.metric("Categoria Dominante", categoria_top)

st.markdown("---")

# --- Layout de Gráficos ---
st.subheader("📊 Análise Científica")

# Gráfico 1: Produção Diária com Média Móvel
st.markdown("### 1. Produção Diária com Média Móvel (7 dias)")
if not df_filtrado.empty:
    daily = df_filtrado.groupby('DATA DE ENTREGA')['QTD'].sum().reset_index()
    daily = daily.sort_values('DATA DE ENTREGA')
    daily['Média Móvel'] = daily['QTD'].rolling(window=7).mean()

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=daily['DATA DE ENTREGA'], y=daily['QTD'], mode='lines', name='QTD Diária', line=dict(color='blue')))
    fig1.add_trace(go.Scatter(x=daily['DATA DE ENTREGA'], y=daily['Média Móvel'], mode='lines', name='Média Móvel (7 dias)', line=dict(color='red', width=3)))
    fig1.update_layout(title="Produção Diária com Tendência", xaxis_title="Data", yaxis_title="Quantidade", title_x=0.1)
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a produção diária.")

# Gráfico 2: Produção por Equipe e Categoria (Heatmap)
st.markdown("### 2. Produção por Equipe e Categoria")
if not df_filtrado.empty:
    heat = df_filtrado.groupby(['EQUIPE', 'CATEGORIA CONVERSOR'])['QTD'].sum().unstack(fill_value=0)
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

# Gráfico 3: Top 5 Responsáveis por Volume
st.markdown("### 3. Top 5 Responsáveis por Volume")
if not df_filtrado.empty:
    top_resp = df_filtrado.groupby('RESPONSAVEL')['QTD'].sum().nlargest(5).reset_index()
    top_resp = top_resp.sort_values('QTD', ascending=True)

    fig3 = px.bar(
        top_resp,
        x='QTD',
        y='RESPONSAVEL',
        orientation='h',
        title="Top 5 Líderes por Volume Total",
        labels={'QTD': 'Quantidade Total', 'RESPONSAVEL': 'Líder'},
        text='QTD'
    )
    fig3.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig3.update_layout(title_x=0.1)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Nenhum dado para exibir os líderes.")

# Gráfico 4: Distribuição do Tamanho dos Lotes (QTD)
st.markdown("### 4. Distribuição do Tamanho dos Lotes (QTD)")
if not df_filtrado.empty:
    fig4 = px.histogram(
        df_filtrado,
        x='QTD',
        nbins=30,
        title="Distribuição do Tamanho dos Lotes de Produção",
        labels={'QTD': 'Quantidade por OS', 'count': 'Frequência'},
        marginal="box"
    )
    fig4.update_layout(title_x=0.1)
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a distribuição de lotes.")

# Gráfico 5: Evolução Mensal por Líder
st.markdown("### 5. Evolução Mensal por Líder")
if not df_filtrado.empty:
    evolucao = df_filtrado.groupby(['MES_ANO', 'RESPONSAVEL'])['QTD'].sum().reset_index()
    evolucao = evolucao.sort_values('MES_ANO')

    fig5 = px.line(
        evolucao,
        x='MES_ANO',
        y='QTD',
        color='RESPONSAVEL',
        title="Evolução da Produção por Líder",
        labels={'QTD': 'Quantidade', 'MES_ANO': 'Mês-Ano', 'RESPONSAVEL': 'Líder'},
        markers=True
    )
    fig5.update_layout(title_x=0.1, xaxis_tickangle=-45)
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Nenhum dado para exibir a evolução por líder.")

# Gráfico 6: Produção por Canal de Venda
st.markdown("### 6. Produção por Canal de Venda")
if not df_filtrado.empty:
    canal = df_filtrado.groupby('CANAL')['QTD'].sum().reset_index()
    fig6 = px.pie(
        canal,
        names='CANAL',
        values='QTD',
        title="Distribuição da Produção por Canal de Venda",
        hole=0.4
    )
    fig6.update_traces(textinfo='percent+label')
    fig6.update_layout(title_x=0.1)
    st.plotly_chart(fig6, use_container_width=True)
else:
    st.info("Nenhum dado para exibir por canal.")

# Gráfico 7: Heatmap de Produção por Mês e Equipe
st.markdown("### 7. Produção por Mês e Equipe (Heatmap)")
if not df_filtrado.empty:
    heat_month = df_filtrado.groupby(['MES_ANO', 'EQUIPE'])['QTD'].sum().unstack(fill_value=0)
    fig7 = px.imshow(
        heat_month,
        labels=dict(x="Equipe", y="Mês-Ano", color="Quantidade"),
        x=heat_month.columns,
        y=heat_month.index,
        color_continuous_scale="Greens"
    )
    fig7.update_layout(title="Desempenho Mensal por Equipe", title_x=0.1)
    st.plotly_chart(fig7, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o heatmap mensal.")

# Gráfico 8: Tamanho Médio do Lote por Categoria
st.markdown("### 8. Tamanho Médio do Lote por Categoria")
if not df_filtrado.empty:
    avg_qtd = df_filtrado.groupby('CATEGORIA CONVERSOR')['QTD'].mean().reset_index()
    avg_qtd = avg_qtd.sort_values('QTD', ascending=True)

    fig8 = px.bar(
        avg_qtd,
        x='QTD',
        y='CATEGORIA CONVERSOR',
        orientation='h',
        title="Tamanho Médio do Lote por Categoria",
        labels={'QTD': 'Quantidade Média', 'CATEGORIA CONVERSOR': 'Categoria'},
        text='QTD'
    )
    fig8.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig8.update_layout(title_x=0.1)
    st.plotly_chart(fig8, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o tamanho médio por categoria.")

# Gráfico 9: Frequência de OS por Líder
st.markdown("### 9. Frequência de OS por Líder")
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

# Gráfico 10: Scatter - Frequência vs. Tamanho do Lote
st.markdown("### 10. Frequência vs. Tamanho do Lote por Equipe")
if not df_filtrado.empty:
    scatter_data = df_filtrado.groupby('EQUIPE').agg(
        OS_Count=('OS', 'size'),
        Avg_QTD=('QTD', 'mean')
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

# Gráfico 11: Produção Acumulada por Equipe
st.markdown("### 11. Produção Acumulada por Equipe ao Longo do Tempo")
if not df_filtrado.empty:
    cumulativo = df_filtrado.groupby(['MES_ANO', 'EQUIPE'])['QTD'].sum().reset_index()
    cumulativo = cumulativo.sort_values(['EQUIPE', 'MES_ANO'])
    cumulativo['QTD Acumulada'] = cumulativo.groupby('EQUIPE')['QTD'].cumsum()

    fig11 = px.line(
        cumulativo,
        x='MES_ANO',
        y='QTD Acumulada',
        color='EQUIPE',
        title="Produção Acumulada por Equipe",
        labels={'QTD Acumulada': 'Produção Acumulada', 'MES_ANO': 'Mês-Ano'},
        markers=True
    )
    fig11.update_layout(title_x=0.1, xaxis_tickangle=-45)
    st.plotly_chart(fig11, use_container_width=True)
else:
    st.info("Nenhum dado para exibir produção acumulada.")

# Gráfico 12: Boxplot da QTD por Categoria
st.markdown("### 12. Distribuição da QTD por Categoria (Boxplot)")
if not df_filtrado.empty:
    fig12 = px.box(
        df_filtrado,
        x='CATEGORIA CONVERSOR',
        y='QTD',
        title="Distribuição da Quantidade por Categoria",
        labels={'QTD': 'Quantidade', 'CATEGORIA CONVERSOR': 'Categoria'},
        color='CATEGORIA CONVERSOR',
        category_orders={"CATEGORIA CONVERSOR": df_filtrado['CATEGORIA CONVERSOR'].value_counts().index.tolist()}
    )
    fig12.update_layout(title_x=0.1, showlegend=False)
    st.plotly_chart(fig12, use_container_width=True)
else:
    st.info("Nenhum dado para exibir o boxplot.")

# --- Tabela Detalhada ---
st.subheader("📋 Dados Detalhados")
if not df_filtrado.empty:
    st.dataframe(df_filtrado.sort_values('DATA DE ENTREGA', ascending=False))
else:
    st.info("Nenhum dado corresponde aos filtros selecionados.")

# --- Exportar Relatório PDF ---
st.subheader("🖨️ Exportar Relatório PDF")

if st.button("Gerar Relatório PDF"):
    if df_filtrado.empty:
        st.warning("Nenhum dado para gerar relatório.")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(0, 10, "Relatório de Produção", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.ln(10)

        # Métricas
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 10, "Métricas Gerais", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Produção Total: {total_qtd:,.0f}", ln=True)
        pdf.cell(0, 10, f"QTD Média por OS: {media_qtd:,.0f}", ln=True)
        pdf.cell(0, 10, f"Total de OS: {num_os:,}", ln=True)
        pdf.cell(0, 10, f"Categoria Dominante: {categoria_top}", ln=True)
        pdf.ln(10)

        # Top 5 Líderes
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 10, "Top 5 Líderes por Volume", ln=True)
        pdf.set_font("Arial", size=10)
        top_resp_pdf = df_filtrado.groupby('RESPONSAVEL')['QTD'].sum().nlargest(5).reset_index()
        pdf.cell(50, 10, "Líder", border=1)
        pdf.cell(50, 10, "Produção", border=1)
        pdf.ln(10)
        for _, row in top_resp_pdf.iterrows():
            pdf.cell(50, 10, str(row['RESPONSAVEL']), border=1)
            pdf.cell(50, 10, f"{row['QTD']:,.0f}", border=1)
            pdf.ln(10)

        # Salva e oferece download
        pdf_output = "relatorio_producao.pdf"
        pdf.output(pdf_output)

        with open(pdf_output, "rb") as f:
            st.download_button(
                label="📥 Baixar Relatório (PDF)",
                data=f,
                file_name="relatorio_producao.pdf",
                mime="application/pdf"
            )

# --- Rodapé ---
st.markdown("---")
st.caption("📊 Dashboard científico de produção. Atualizado em tempo real com filtros dinâmicos.")