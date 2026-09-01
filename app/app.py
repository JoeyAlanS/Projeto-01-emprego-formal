"""Dashboard Streamlit do Projeto 1.

Execute a partir da raiz com: streamlit run app/app.py
Equipe: Joey Alan e Paulo Henrico.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "dados" / "analytical" / "base_analitica_municipios.csv"
MAP_PATH = ROOT / "dados" / "raw" / "dados_comuns" / "malha_municipal_ce_2022.geojson"

st.set_page_config(page_title="Economia e emprego formal - CE", page_icon="📊", layout="wide")


@st.cache_data
def carregar_dados() -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    df = pd.read_csv(BASE_PATH, sep=";", encoding="utf-8-sig", dtype={"territorio_codigo": "string"})
    malha = gpd.read_file(MAP_PATH)
    malha["codarea"] = malha["codarea"].astype("string")
    return df, malha


st.title("Economia e emprego formal nos municípios do Ceará")
st.caption("Projeto 1 | IBGE/SIDRA | CEMPRE 2022, PIB 2021/2022 e Censo 2022")

if not BASE_PATH.exists():
    st.error("A base analítica ainda não foi gerada. Execute `python executar_tudo.py` na raiz do repositório.")
    st.stop()

df, malha = carregar_dados()

with st.sidebar:
    st.header("Filtros")
    quadrantes = ["Todos"] + sorted(df["quadrante_economico"].dropna().unique().tolist())
    quadrante = st.selectbox("Quadrante econômico", quadrantes)
    municipios = ["Todos"] + sorted(df["territorio_nome"].dropna().tolist())
    municipio = st.selectbox("Município", municipios)
    st.divider()
    st.markdown("**Como ler**")
    st.caption("Intensidade de ocupação formal = pessoal ocupado total no CEMPRE por mil habitantes. Não é taxa de emprego.")

filtrado = df.copy()
if quadrante != "Todos":
    filtrado = filtrado[filtrado["quadrante_economico"] == quadrante]
if municipio != "Todos":
    filtrado = filtrado[filtrado["territorio_nome"] == municipio]

if filtrado.empty:
    st.warning("Nenhum município atende aos filtros selecionados.")
    st.stop()

st.subheader("Visão geral")
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Municípios no recorte", f"{len(filtrado):,}")
with k2:
    st.metric("PIB per capita mediano", f"R$ {filtrado['pib_per_capita_reais_2022'].median():,.0f}")
with k3:
    st.metric("Intensidade formal mediana", f"{filtrado['intensidade_ocupacao_formal_por_mil_hab_2022'].median():,.1f}", help="Pessoas ocupadas formais por mil habitantes")
with k4:
    st.metric("Salário médio mensal mediano", f"R$ {filtrado['salario_medio_mensal_reais_2022'].median():,.0f}")

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Comparação territorial: PIB per capita")
    top = filtrado.nlargest(min(12, len(filtrado)), "pib_per_capita_reais_2022").sort_values("pib_per_capita_reais_2022")
    fig = px.bar(top, x="pib_per_capita_reais_2022", y="territorio_nome", orientation="h", color="pib_per_capita_reais_2022", color_continuous_scale="Tealgrn", labels={"pib_per_capita_reais_2022": "PIB per capita (R$)", "territorio_nome": "Município"})
    fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0), height=450)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Cruzamento: PIB per capita x intensidade formal")
    fig = px.scatter(filtrado, x="pib_per_capita_reais_2022", y="intensidade_ocupacao_formal_por_mil_hab_2022", size="populacao_residente_2022", color="quadrante_economico", hover_name="territorio_nome", labels={"pib_per_capita_reais_2022": "PIB per capita (R$)", "intensidade_ocupacao_formal_por_mil_hab_2022": "Ocupação formal por mil hab.", "quadrante_economico": "Quadrante"}, height=450)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Mapa de comparação")
mapa = malha.merge(df, left_on="codarea", right_on="territorio_codigo", how="left")
fig_map = px.choropleth(mapa, geojson=mapa.__geo_interface__, locations=mapa.index, featureidkey="id", color="pib_per_capita_reais_2022", hover_name="territorio_nome", color_continuous_scale="Tealgrn", labels={"pib_per_capita_reais_2022": "PIB per capita (R$)"})
fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=520)
st.plotly_chart(fig_map, use_container_width=True)

st.subheader("Cruzamento temporal: crescimento populacional e ocupação formal")
fig_growth = px.scatter(df, x="crescimento_populacional_pct_2010_2022", y="intensidade_ocupacao_formal_por_mil_hab_2022", color="participacao_administracao_pct_2021", hover_name="territorio_nome", color_continuous_scale="Viridis", labels={"crescimento_populacional_pct_2010_2022": "Crescimento populacional 2010-2022 (%)", "intensidade_ocupacao_formal_por_mil_hab_2022": "Ocupação formal por mil hab.", "participacao_administracao_pct_2021": "Administração no VAB (2021, %)"}, height=430)
st.plotly_chart(fig_growth, use_container_width=True)

with st.expander("Fontes, metodologia e limitações"):
    st.markdown("""
    - **Fontes:** IBGE/SIDRA, tabelas 9509 (CEMPRE 2022), 5938 (PIB 2021 e PIB 2022) e 4709 (Censo 2022).
    - **Integração:** filtro municipal `N6` e junção 1:1 pelo código IBGE de sete dígitos `territorio_codigo`; nomes não são usados como chave.
    - **Escala:** PIB em Mil Reais foi multiplicado por 1.000 para o PIB per capita. O salário médio é o indicador mensal oficial da tabela 9509.
    - **Limitações:** CEMPRE mede ocupação formal localizada nas organizações e não captura informalidade nem necessariamente residentes empregados. A estrutura setorial é de 2021 e os demais indicadores principais são de 2022; essa defasagem é uma associação exploratória, não causal.
    """)
