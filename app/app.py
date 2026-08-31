"""Aplicação Interativa - Streamlit

Execução: streamlit run app/app.py
Equipe: Joey Alan e Paulo Henrico
"""

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Monitor de Economia e Emprego - CE",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def carregar_dados():
  df = pd.read_csv(
      "dados/analytical/base_analitica_pib_pop_2022.csv",
      sep=";",
      dtype={"territorio_codigo": "string"},
  )
  malha = gpd.read_file(
      "dados/raw/dados_comuns/malha_municipal_ce_2022.geojson"
  )
  malha["codarea"] = malha["codarea"].astype("string")
  return df, malha


df_analitica, malha_ce = carregar_dados()

# Sidebar
st.sidebar.header("Filtros Globais")
municipios = ["Todos"] + sorted(df_analitica["territorio_nome"].unique().tolist())
mun_selecionado = st.sidebar.selectbox("Selecione o Município:", municipios)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Fonte dos Dados: IBGE / SIDRA (Tabelas 9509, 5938 e 4709). Arquivos"
    " estáticos locais."
)

# Conteúdo Principal
st.title("Monitor da Economia e Emprego Formal - Ceará")
st.markdown(
    "Análise integrada de indicadores municipais do IBGE baseada no Censo 2022,"
    " PIB e CEMPRE."
)
st.divider()

# KPIs
col1, col2, col3 = st.columns(3)
top_pib = df_analitica.loc[df_analitica["pib_per_capita"].idxmax()]
media_pop = df_analitica["populacao_residente"].mean()

with col1:
  st.metric(
      label="Maior PIB per capita",
      value=f"R$ {top_pib['pib_per_capita']:,.2f}",
      delta=top_pib["territorio_nome"].split(" - ")[0],
  )
with col2:
  st.metric(
      label="População Média dos Municípios", value=f"{media_pop:,.0f} hab."
  )
with col3:
  st.metric(
      label="Municípios Cobertos",
      value=len(df_analitica),
      delta="100% dos municípios",
  )

st.divider()

# Gráficos
col_mapa, col_graf = st.columns(2)

with col_mapa:
  st.subheader("Distribuição do PIB per Capita")
  mapa_dados = malha_ce.merge(
      df_analitica, left_on="codarea", right_on="territorio_codigo"
  )
  fig_map = px.choropleth(
      mapa_dados,
      geojson=mapa_dados.geometry,
      locations=mapa_dados.index,
      color="pib_per_capita",
      hover_name="territorio_nome",
      color_continuous_scale="Blues",
      labels={"pib_per_capita": "PIB per capita (R$)"},
  )
  fig_map.update_geos(fitbounds="locations", visible=False)
  fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
  st.plotly_chart(fig_map, use_container_width=True)

with col_graf:
  st.subheader("População Residente vs PIB Total")
  fig_scatter = px.scatter(
      df_analitica,
      x="populacao_residente",
      y="pib_mil_reais",
      hover_name="territorio_nome",
      labels={
          "populacao_residente": "População Residente (Censo 2022)",
          "pib_mil_reais": "PIB Total (Mil R$)",
      },
      trendline="ols",
  )
  st.plotly_chart(fig_scatter, use_container_width=True)