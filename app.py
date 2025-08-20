import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# --- Configuração da Página ---
st.set_page_config(
    page_title="🏭 Dashboard Científico de Produção",
    page_icon="📊",
    layout="wide",
)

# --- URLs dos CSVs ---
url_data = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_dataframe.csv"
url_log = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_dataframe_log.csv"
url_pcp = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_pcp_kpiv1.csv"
url_pre = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_PRE_kpiv1.csv"
url_mod = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_MOD_kpiv1.csv"
url_almx = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_ALMX_kpiv1.csv"

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
    if 'SDOR' not in log.columns:
        log['SDOR'] = log['PPDTPP'] / log['ShiftFactor']
except Exception as e:
    st.warning("⚠️ Dados de capacidade não carregados.")
    log = None

# --- Carregar dados dos setores (PCP, PRE, MOD, ALMX) ---
def load_sector_data(url, name):
    try:
        df_sec = pd.read_csv(url, header=None, encoding='utf-8')
        df_sec = df_sec.set_index(0).T
        months = [
            '2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06',
            '2023-07', '2023-08', '2023-09', '2023-10', '2023-11', '2023-12',
            '2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06',
            '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12',
            '2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06', '2025-07'
        ]
        df_sec.index = months[:len(df_sec)]
        df_sec.index.name = 'MES_ANO'
        return df_sec
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar {name}: {e}")
        return None

pcp = load_sector_data(url_pcp, "PCP")
pre = load_sector_data(url_pre, "Pré-Produção")
mod = load_sector_data(url_mod, "MOD")
almx = load_sector_data(url_almx, "Almoxarifado")

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

# Filtro por Canal
canal_disponiveis = sorted(df['CANAL'].dropna().unique())
canal_filtro_ativo = st.sidebar.checkbox("Filtrar por Canal", value=False)
canais_selecionados = canal_disponiveis if not canal_filtro_ativo else st.sidebar.multiselect(
    "Canal", canal_disponiveis, default=canal_disponiveis, key="canal")

# --- Filtragem do DataFrame ---
mask = (
    (df['ANO_ENTREGA'].isin(anos_selecionados)) &
    (df['MES_ENTREGA'].isin(meses_selecionados)) &
    (df['RESPONSAVEL'].isin(responsavel_selecionados)) &
    (df['EQUIPE'].isin(equipes_selecionados)) &
    (df['CANAL'].isin(canais_selecionados))
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

# --- Mostrar Métrica Ativa ---
st.markdown(f"### 📌 Métrica Ativa: **{label_metrica}**")
st.markdown("---")

# --- Título ---
st.title("🏭 Dashboard Científico de Produção")
st.markdown("Análise avançada da linha de produção com métricas de desempenho, tendências e eficiência.")
st.markdown("---")

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

# --- Criar Abas ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Produção Diária",
    "👥 Líderes & Equipes",
    "📦 Produtos & Categorias",
    "📈 Análise Avançada",
    "💰 Digital Twin & Custos",
    "📅 Comparativo Anual (2024 vs 2025)"
])

# ====================
# ABAS DO DASHBOARD
# ====================

# --- Aba 1: Produção Diária ---
with tab1:
    # --- Produção Diária ---
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
            hovermode='x unified'
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir a produção diária.")

    # --- Distribuição do Tamanho dos Lotes ---
    info_tooltip(
        f"### 4. Distribuição do Tamanho dos Lotes ({label_metrica})",
        "Histograma que mostra como os tamanhos dos lotes estão distribuídos. "
        "Boxplot acima mostra outliers (valores extremos)."
    )
    if not df_filtrado.empty:
        fig4 = px.histogram(df_filtrado, x=valor_coluna, nbins=30, marginal="box", title=f"Distribuição do Tamanho dos Lotes de Produção ({label_metrica})")
        fig4.update_layout(template="plotly_white")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir a distribuição de lotes.")

# --- Aba 2: Líderes & Equipes ---
with tab2:
    # --- Top 5 Líderes ---
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
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir os líderes.")

    # --- Frequência de OS por Líder ---
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
        st.plotly_chart(fig9, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir frequência por líder.")

    # --- Leaderboard Mensal ---
    info_tooltip(
        "### 🏆 7. Leaderboard Mensal por Produção",
        "Mostra os 3 principais líderes por mês. Barras empilhadas mostram evolução do desempenho ao longo do tempo."
    )
    if not df_filtrado.empty:
        leaderboard = df_filtrado.groupby(['MES_ANO', 'RESPONSAVEL'])[valor_coluna].sum().reset_index()
        leaderboard = leaderboard.sort_values(['MES_ANO', valor_coluna], ascending=[True, False])
        top3 = leaderboard.groupby('MES_ANO').head(3)
        fig_lb = px.bar(top3, x=valor_coluna, y='MES_ANO', color='RESPONSAVEL', orientation='h', title="Top 3 Líderes por Mês")
        fig_lb.update_layout(barmode='stack')
        st.plotly_chart(fig_lb, use_container_width=True)
    else:
        st.info("Nenhum dado para leaderboard.")

# --- Aba 3: Produtos & Categorias ---
with tab3:
    # --- Representatividade por Família ---
    info_tooltip(
        f"### 🔥 Representatividade por Família ({label_metrica})",
        "Mostra a participação de cada família de produtos na produção total. "
        "Ajuda a identificar quais famílias são mais relevantes e merecem foco."
    )
    if not df_filtrado.empty:
        fam = df_filtrado.groupby('FAMILIA')[valor_coluna].sum().reset_index().sort_values(valor_coluna, ascending=False)
        fig_fam_pie = px.pie(fam, names='FAMILIA', values=valor_coluna, title="Distribuição por Família", hole=0.4)
        fig_fam_pie.update_traces(textinfo='percent+label', textposition='inside')
        st.plotly_chart(fig_fam_pie, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir por família.")

    # --- Produção por Canal de Venda ---
    info_tooltip(
        f"### 6. Produção por Canal de Venda ({label_metrica})",
        "Gráfico de pizza mostrando a participação de cada canal (Site, Atacado, etc). "
        "Ajuda a entender de onde vem a demanda."
    )
    if not df_filtrado.empty:
        canal = df_filtrado.groupby('CANAL')[valor_coluna].sum().reset_index()
        fig6 = px.pie(canal, names='CANAL', values=valor_coluna, title="Distribuição da Produção por Canal de Venda", hole=0.4)
        fig6.update_traces(textinfo='percent+label')
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir por canal.")

    # --- Tamanho Médio do Lote por Categoria ---
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
        st.plotly_chart(fig8, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir o tamanho médio por categoria.")

    # --- Boxplot da QTD por Categoria ---
    info_tooltip(
        f"### 12. Distribuição da {label_metrica} por Categoria (Boxplot)",
        "Boxplot mostra mediana, quartis e outliers por categoria. "
        "Ajuda a comparar variabilidade entre categorias."
    )
    if not df_filtrado.empty:
        fig12 = px.box(df_filtrado, x='CATEGORIA_CONVERSOR', y=valor_coluna, color='CATEGORIA_CONVERSOR', title="Distribuição da Quantidade por Categoria")
        fig12.update_layout(showlegend=False)
        st.plotly_chart(fig12, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir o boxplot.")

# --- Aba 4: Análise Avançada ---
with tab4:
    # --- CFD ---
    info_tooltip(
        "### 📈 1. Fluxo Cumulativo de Produção",
        "Mostra a produção total acumulada ao longo do tempo. "
        "A inclinação da linha indica a velocidade de produção: mais íngreme = mais produtivo. "
        "Ideal para identificar acelerações ou desacelerações."
    )
    if not df_filtrado.empty:
        cfd = df_filtrado.groupby('DATA_DE_ENTREGA')[valor_coluna].sum().reset_index()
        cfd = cfd.sort_values('DATA_DE_ENTREGA')
        cfd['Acumulado'] = cfd[valor_coluna].cumsum()
        fig_cfd = px.area(cfd, x='DATA_DE_ENTREGA', y='Acumulado', title="Fluxo Cumulativo de Produção ao Longo do Tempo")
        fig_cfd.update_layout(hovermode='x unified')
        st.plotly_chart(fig_cfd, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir o CFD.")

    # --- Pareto por Líder ---
    info_tooltip(
        "### 🎯 2. Análise de Pareto: 80/20 dos Líderes",
        "Os líderes são ordenados do maior para o menor produtor. "
        "A linha vermelha em 80% mostra onde os principais 20% dos líderes terminam. "
        "Ajuda a identificar os maiores contribuidores e dependências."
    )
    if not df_filtrado.empty:
        pareto = df_filtrado.groupby('RESPONSAVEL')[valor_coluna].sum().sort_values(ascending=False).reset_index()
        pareto['cumsum'] = pareto[valor_coluna].cumsum() / pareto[valor_coluna].sum() * 100
        fig_pareto = px.line(pareto, x='RESPONSAVEL', y='cumsum', markers=True, title="Acumulado de Produção por Líder (Regra 80/20)")
        fig_pareto.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80%")
        st.plotly_chart(fig_pareto, use_container_width=True)
    else:
        st.info("Nenhum dado para análise de Pareto.")

    # --- Sazonalidade ---
    info_tooltip(
        "### 🌡️ 4. Sazonalidade: Produção por Mês e Ano",
        "Mapa de calor que mostra a produção em cada mês de cada ano. "
        "Células mais escuras indicam maior produção. Útil para identificar padrões sazonais."
    )
    if not df_filtrado.empty:
        season = df_filtrado.groupby(['ANO_ENTREGA', 'MES_ENTREGA'])[valor_coluna].sum().reset_index()
        season_pivot = season.pivot(index='ANO_ENTREGA', columns='MES_ENTREGA', values=valor_coluna).fillna(0)
        fig_season = px.imshow(season_pivot, color_continuous_scale="Reds", title="Calor da Produção por Mês e Ano")
        st.plotly_chart(fig_season, use_container_width=True)
    else:
        st.info("Nenhum dado para mapa de sazonalidade.")

# --- Aba 5: Digital Twin & Custos ---
with tab5:
    st.markdown("### 💡 Digital Twin: Projeção com Custo de Mão de Obra (MOD)")

    if log is not None and not df_filtrado.empty:
        sdor_base = log['SDOR'].tail(3).mean() if len(log) >= 3 else log['SDOR'].iloc[-1]
        st.markdown(f"**📊 Produtividade Base (SDOR):** {sdor_base:.1f} unidades por funcionário por dia")

        # Extrair custo unitário de MOD
        custo_unit_mod = 12.50
        if mod is not None and 'Custo Unitário Médio de Fabricação' in mod.columns:
            custo_unit_mod = pd.to_numeric(mod.loc[:, 'Custo Unitário Médio de Fabricação'], errors='coerce').tail(3).mean()
        st.markdown(f"**🧮 Custo Unitário de Mão de Obra (MOD):** R$ {custo_unit_mod:.2f}")
        st.markdown("---")

        last_date = df_filtrado['DATA_DE_ENTREGA'].max()
        next_months = pd.date_range(last_date, periods=4, freq='MS')[1:4]
        month_names = [date.strftime('%b/%Y') for date in next_months]

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
                proj_qtd = sdor_base * shift_factor * func * dias
                custo_total = proj_qtd * custo_unit_mod
                proj_data.append({
                    "MES_ANO": next_months[i].strftime('%Y-%m'),
                    "Produção": round(proj_qtd),
                    "Custo Mão de Obra (R$)": round(custo_total, 2),
                    "Tipo": "Projeção"
                })

        hist = df_filtrado.groupby('MES_ANO')[valor_coluna].sum().reset_index()
        hist = hist.tail(6)
        hist["Tipo"] = "Real"
        hist.rename(columns={valor_coluna: "Produção"}, inplace=True)
        hist['MES_ANO'] = pd.to_datetime(hist['MES_ANO'] + "-01")
        combined = pd.concat([hist, pd.DataFrame(proj_data)], ignore_index=True)
        combined['MES_ANO'] = pd.to_datetime(combined['MES_ANO'])

        fig_sim = px.line(
            combined,
            x='MES_ANO',
            y='Produção',
            color='Tipo',
            markers=True,
            line_dash='Tipo',
            title="Digital Twin: Projeção Mensal com Parâmetros Personalizados",
            line_shape='spline'
        )
        fig_sim.update_layout(
            xaxis=dict(tickformat="%b %Y", dtick="M1"),
            hovermode='x unified'
        )
        st.plotly_chart(fig_sim, use_container_width=True)

        st.markdown("### 📋 Resumo da Projeção")
        proj_df = pd.DataFrame(proj_data)
        proj_df['Produção'] = proj_df['Produção'].map('{:,.0f}'.format)
        proj_df['Custo Mão de Obra (R$)'] = proj_df['Custo Mão de Obra (R$)'].map('R$ {:,.2f}'.format)
        st.dataframe(proj_df[['MES_ANO', 'Produção', 'Custo Mão de Obra (R$)']].rename(columns={
            "MES_ANO": "Mês",
            "Produção": "Produção Projetada",
            "Custo Mão de Obra (R$)": "Custo MO"
        }))

        # --- Custo por Produto ---
        st.markdown("### 💰 Custo de Mão de Obra por Produto")
        if not df_filtrado.empty:
            labor_data = df_filtrado.groupby('PRODUTO').agg(
                QTD_Total=('QTD', 'sum'),
                FAMILIA=('FAMILIA', 'first')
            ).reset_index()
            labor_data['Custo Unitário (R$)'] = custo_unit_mod
            labor_data['Custo Total (R$)'] = labor_data['QTD_Total'] * custo_unit_mod
            labor_data = labor_data.sort_values('Custo Total (R$)', ascending=False)
            st.dataframe(
                labor_data.head(20)[['PRODUTO', 'FAMILIA', 'QTD_Total', 'Custo Unitário (R$)', 'Custo Total (R$)']].round(2),
                use_container_width=True
            )
    else:
        st.info("Dados insuficientes para executar o Digital Twin.")

# --- Aba 6: Comparativo Anual (2024 vs 2025) ---
with tab6:
    st.markdown("### 📅 Comparativo Anual: 2024 vs 2025")

    df_2024 = df_filtrado[df_filtrado['ANO_ENTREGA'] == 2024]
    df_2025 = df_filtrado[df_filtrado['ANO_ENTREGA'] == 2025]

    total_2024 = df_2024[valor_coluna].sum() if not df_2024.empty else 0
    total_2025 = df_2025[valor_coluna].sum() if not df_2025.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Produção Total 2024", f"{total_2024:,.0f}")
    col2.metric("Produção Total 2025", f"{total_2025:,.0f}")
    if total_2024 > 0:
        crescimento = ((total_2025 - total_2024) / total_2024) * 100
        col3.metric("Crescimento (%)", f"{crescimento:+.1f}%")
    else:
        col3.metric("Crescimento (%)", "N/A")

    # --- Produção Mensal por Ano ---
    mensal_2024 = df_2024.groupby('MES_ENTREGA')[valor_coluna].sum().reset_index()
    mensal_2024['ANO'] = 2024
    mensal_2025 = df_2025.groupby('MES_ENTREGA')[valor_coluna].sum().reset_index()
    mensal_2025['ANO'] = 2025
    combined = pd.concat([mensal_2024, mensal_2025], ignore_index=True)

    fig_yoy = px.line(
        combined,
        x='MES_ENTREGA',
        y=valor_coluna,
        color='ANO',
        markers=True,
        title="Produção Mensal: 2024 vs 2025",
        labels={'MES_ENTREGA': 'Mês', valor_coluna: 'Quantidade'}
    )
    fig_yoy.update_layout(hovermode='x unified')
    st.plotly_chart(fig_yoy, use_container_width=True)

    # --- Top 5 Produtos por Ano ---
    st.markdown("#### Top 5 Produtos por Ano")
    col1, col2 = st.columns(2)
    with col1:
        if not df_2024.empty:
            top2024 = df_2024.groupby('PRODUTO')[valor_coluna].sum().nlargest(5).reset_index()
            st.markdown("**2024**")
            st.dataframe(top2024)
    with col2:
        if not df_2025.empty:
            top2025 = df_2025.groupby('PRODUTO')[valor_coluna].sum().nlargest(5).reset_index()
            st.markdown("**2025**")
            st.dataframe(top2025)

# --- Diagnóstico Final ---
st.markdown("---")
st.write("### 🔍 Diagnóstico do DataFrame")
st.write(f"**Número de linhas:** {len(df)}")
st.write(f"**Número de colunas:** {len(df.columns)}")
st.write(f"**Colunas:** {list(df.columns)}")

st.caption("📊 Dashboard científico de produção. Atualizado com base nos arquivos `updated_dataframe.csv` e `updated_dataframe_log.csv`.")
