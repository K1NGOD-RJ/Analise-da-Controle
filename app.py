import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Análise da Produção",
    page_icon="📊",
    layout="wide",
)

# --- Definição das colunas (CSV não tem cabeçalho) ---
col_names = [
    "Ordem", "OS", "OS UNICA", "FINAL", "EQUIPE", "RESPONSAVEL", "CANAL", "STATUS",
    "CODIGO/CLIENTE", "PRODUTO", "QTD", "DATA DE ENTREGA", "SEMANA NO ANO", "MES ENTREGA",
    "ANO ENTREGA", "MES_ANO", "CATEGORIA CONVERSOR", "QUANTIDADE PONDERADA"
]

# --- Carregamento dos dados ---
try:
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

    # Remove linhas com dados inválidos
    df = df.dropna(subset=['QTD', 'MES ENTREGA', 'ANO ENTREGA', 'RESPONSAVEL', 'EQUIPE'])

    # Garante que MES_ANO está como string
    df['MES_ANO'] = df['MES_ANO'].astype(str).str.strip()

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

# --- Conteúdo Principal ---
st.title("🎲 Dashboard de Análise da Produção Cicero")
st.markdown("Explore os dados da produção nos últimos anos. Utilize os filtros à esquerda para refinar sua análise.")

# --- Métricas Principais (KPIs) ---
st.subheader("Métricas Gerais")

if not df_filtrado.empty:
    quantidade_media = df_filtrado['QTD'].mean()
    quantidade_maxima = df_filtrado['QTD'].max()
    total_registros = len(df_filtrado)
    categoria_mais_frequente = df_filtrado["CATEGORIA CONVERSOR"].mode()
    categoria_mais_frequente = categoria_mais_frequente.iloc[0] if len(categoria_mais_frequente) > 0 else "N/A"
else:
    quantidade_media = 0
    quantidade_maxima = 0
    total_registros = 0
    categoria_mais_frequente = "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Quantidade Média", f"{quantidade_media:,.0f}")
col2.metric("Quantidade Máxima", f"{quantidade_maxima:,.0f}")
col3.metric("Total de Registros", f"{total_registros:,}")
col4.metric("Categoria Mais Frequente", categoria_mais_frequente)

# --- Totais por Equipe ---
st.subheader("📊 Total por Equipe")

if not df_filtrado.empty:
    total_por_equipe = df_filtrado.groupby('EQUIPE')['QTD'].sum().reset_index()
    total_por_equipe = total_por_equipe.sort_values('QTD', ascending=False)

    fig_equipe = px.bar(
        total_por_equipe,
        x='EQUIPE',
        y='QTD',
        title="Produção Total por Equipe",
        labels={'QTD': 'Quantidade', 'EQUIPE': 'Equipe'},
        text='QTD'
    )
    fig_equipe.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_equipe.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', title_x=0.1)
    st.plotly_chart(fig_equipe, use_container_width=True)
else:
    st.info("Nenhum dado disponível para exibir o total por equipe.")

# --- Destaque dos Melhores Desempenhos (Top Performers) ---
st.subheader("🏆 Melhores Desempenhos")

if not df_filtrado.empty:
    top_responsaveis = df_filtrado.groupby('RESPONSAVEL')['QTD'].sum().nlargest(5).reset_index()
    top_responsaveis = top_responsaveis.sort_values('QTD', ascending=True)

    fig_top = px.bar(
        top_responsaveis,
        x='QTD',
        y='RESPONSAVEL',
        orientation='h',
        title="Top 5 Responsáveis por Produção Total",
        labels={'QTD': 'Quantidade Total', 'RESPONSAVEL': 'Responsável'},
        text='QTD'
    )
    fig_top.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_top.update_layout(title_x=0.1)
    st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("Nenhum dado disponível para exibir os melhores desempenhos.")

# --- Análises Visuais com Plotly ---
st.subheader("Análise Detalhada")

col_graf3, col_graf4 = st.columns(2)

# Gráfico 3: Linha - Evolução mensal por RESPONSAVEL
with col_graf3:
    if not df_filtrado.empty:
        # Cria uma coluna de ordenação temporal
        df_temp = df_filtrado.copy()
        df_temp['ANO_MES_NUM'] = df_temp['ANO ENTREGA'] * 100 + df_temp['MES ENTREGA']
        df_temp = df_temp.sort_values('ANO_MES_NUM')

        evolucao = df_temp.groupby(['MES_ANO', 'RESPONSAVEL'])['QTD'].sum().reset_index()

        fig3 = px.line(
            evolucao,
            x='MES_ANO',
            y='QTD',
            color='RESPONSAVEL',
            title="Evolução da Produção por Responsável",
            labels={'QTD': 'Quantidade', 'MES_ANO': 'Mês-Ano', 'RESPONSAVEL': 'Responsável'},
            markers=True
        )
        fig3.update_layout(title_x=0.1, xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para exibir a evolução por responsável.")

# Gráfico 4: Histograma da distribuição de QTD
with col_graf4:
    if not df_filtrado.empty:
        fig4 = px.histogram(
            df_filtrado,
            x='QTD',
            nbins=30,
            title="Distribuição da Quantidade (QTD)",
            labels={'QTD': 'Quantidade', 'count': 'Frequência'},
            marginal="box"
        )
        fig4.update_layout(title_x=0.1)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para exibir a distribuição de QTD.")

# --- Tabela de Dados Detalhados ---
st.subheader("Dados Detalhados")
if not df_filtrado.empty:
    st.dataframe(df_filtrado)
else:
    st.info("Nenhum dado corresponde aos filtros selecionados.")
