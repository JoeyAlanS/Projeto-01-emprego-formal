"""Dashboard Streamlit do Projeto 1.

Execute a partir da raiz com: streamlit run app/app.py
Equipe: Joey Alan e Paulo Henrico.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "dados" / "analytical" / "base_analitica_municipios.csv"
MAP_PATH = ROOT / "dados" / "raw" / "dados_comuns" / "malha_municipal_ce_2022.geojson"

INDICADORES_MAPA = {
    "PIB per capita (2022)": {
        "coluna": "pib_per_capita_reais_2022",
        "legenda": "PIB per capita (R$)",
        "formato": "R$ {:,.0f}",
    },
    "Intensidade de ocupação formal (2022)": {
        "coluna": "intensidade_ocupacao_formal_por_mil_hab_2022",
        "legenda": "Ocupação formal por mil hab.",
        "formato": "{:,.1f} por mil hab.",
    },
    "Salário médio mensal (2022)": {
        "coluna": "salario_medio_mensal_reais_2022",
        "legenda": "Salário médio mensal (R$)",
        "formato": "R$ {:,.0f}",
    },
}

st.set_page_config(page_title="Economia e emprego formal - CE", page_icon="📊", layout="wide")


@st.cache_data
def carregar_dados() -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    """Carrega e valida a base tabular e sua correspondência com a malha."""
    df = pd.read_csv(BASE_PATH, sep=";", encoding="utf-8-sig", dtype={"territorio_codigo": "string"})
    malha = gpd.read_file(MAP_PATH)

    df["territorio_codigo"] = df["territorio_codigo"].str.strip().str.zfill(7)
    malha["codarea"] = malha["codarea"].astype("string").str.strip().str.zfill(7)
    if malha.crs is not None and malha.crs.to_epsg() != 4326:
        malha = malha.to_crs(epsg=4326)

    if df["territorio_codigo"].duplicated().any():
        raise ValueError("A base analítica contém códigos IBGE municipais duplicados.")
    if malha["codarea"].duplicated().any():
        raise ValueError("A malha contém códigos IBGE municipais duplicados.")

    mapa = malha.merge(
        df,
        left_on="codarea",
        right_on="territorio_codigo",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    sem_dados = mapa.loc[mapa["_merge"] != "both", "codarea"].tolist()
    codigos_sem_poligono = sorted(set(df["territorio_codigo"]) - set(malha["codarea"]))
    if sem_dados or codigos_sem_poligono:
        raise ValueError(
            "A correspondência entre a base e a malha municipal está incompleta "
            f"({len(sem_dados)} polígonos sem dados e {len(codigos_sem_poligono)} municípios sem polígono)."
        )

    mapa = mapa.drop(columns="_merge")
    df["municipio_exibicao"] = df["territorio_nome"].str.replace(" - CE", "", regex=False)
    mapa["municipio_exibicao"] = mapa["territorio_nome"].str.replace(" - CE", "", regex=False)
    return df, mapa


def limites_escala_robusta(valores: pd.Series) -> tuple[float, float]:
    """Evita que poucos valores extremos comprimam todas as cores do mapa."""
    valores_validos = pd.to_numeric(valores, errors="coerce").dropna()
    if valores_validos.empty:
        return 0.0, 1.0

    limite_inferior = float(valores_validos.quantile(0.05))
    limite_superior = float(valores_validos.quantile(0.95))
    if limite_inferior == limite_superior:
        limite_inferior = float(valores_validos.min())
        limite_superior = float(valores_validos.max())
    if limite_inferior == limite_superior:
        limite_superior = limite_inferior + 1.0
    return limite_inferior, limite_superior


def limpar_municipios() -> None:
    st.session_state["municipios_comparacao"] = []


st.title("Economia e emprego formal nos municípios do Ceará")
st.caption("Projeto 1 | IBGE/SIDRA | CEMPRE 2022, PIB 2021/2022 e Censo 2022")

if not BASE_PATH.exists():
    st.error("A base analítica ainda não foi gerada. Execute `python executar_tudo.py` na raiz do repositório.")
    st.stop()
if not MAP_PATH.exists():
    st.error("A malha municipal não foi encontrada em `dados/raw/dados_comuns`.")
    st.stop()

try:
    df, mapa_base = carregar_dados()
except (OSError, ValueError) as erro:
    st.error(f"Não foi possível preparar os dados do mapa: {erro}")
    st.stop()

with st.sidebar:
    st.header("Filtros e comparação")
    quadrantes = ["Todos"] + sorted(df["quadrante_economico"].dropna().unique().tolist())
    quadrante = st.selectbox("Quadrante econômico", quadrantes, key="quadrante_economico")

    recorte = df if quadrante == "Todos" else df[df["quadrante_economico"] == quadrante]
    municipios_disponiveis = sorted(recorte["territorio_nome"].dropna().unique().tolist())
    selecao_anterior = st.session_state.get("municipios_comparacao", [])
    selecao_valida = [nome for nome in selecao_anterior if nome in municipios_disponiveis]
    if selecao_anterior != selecao_valida:
        st.session_state["municipios_comparacao"] = selecao_valida

    municipios_selecionados = st.multiselect(
        "Municípios para comparar",
        municipios_disponiveis,
        key="municipios_comparacao",
        placeholder="Busque e selecione um ou mais municípios",
        help="Digite para buscar. Use o × de cada item para removê-lo individualmente.",
        max_selections=None,
        filter_mode="contains",
        wrap=False,
    )
    st.caption("Digite para buscar e use o × de cada item para removê-lo individualmente.")
    st.button(
        "Limpar municípios",
        icon=":material/clear_all:",
        on_click=limpar_municipios,
        disabled=not municipios_selecionados,
        width="stretch",
    )

    indicador_mapa = st.selectbox("Indicador exibido no mapa", list(INDICADORES_MAPA))
    st.caption(f"{len(municipios_selecionados)} município(s) selecionado(s) para comparação.")
    st.divider()
    st.markdown("**Como ler**")
    st.caption("Intensidade de ocupação formal = pessoal ocupado total no CEMPRE por mil habitantes. Não é taxa de emprego.")

comparacao_ativa = bool(municipios_selecionados)
comparacao = (
    recorte[recorte["territorio_nome"].isin(municipios_selecionados)].copy()
    if comparacao_ativa
    else recorte.copy()
)

if comparacao.empty:
    st.warning("Nenhum município atende aos filtros selecionados.")
    st.stop()

if comparacao_ativa:
    st.info(
        f"Comparação ativa com {len(comparacao)} município(s). "
        "O mapa mantém o recorte territorial completo e destaca os selecionados com contorno escuro.",
        icon=":material/compare_arrows:",
    )
else:
    st.caption("Selecione municípios na barra lateral para compará-los; sem seleção, os gráficos mostram o recorte completo.")

st.subheader("Visão geral")
rotulo_quantidade = "Municípios comparados" if comparacao_ativa else "Municípios no recorte"
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric(rotulo_quantidade, f"{len(comparacao):,}", border=True)
with k2:
    st.metric("PIB per capita mediano", f"R$ {comparacao['pib_per_capita_reais_2022'].median():,.0f}", border=True)
with k3:
    st.metric(
        "Intensidade formal mediana",
        f"{comparacao['intensidade_ocupacao_formal_por_mil_hab_2022'].median():,.1f}",
        help="Pessoas ocupadas formais por mil habitantes",
        border=True,
    )
with k4:
    st.metric("Salário médio mensal mediano", f"R$ {comparacao['salario_medio_mensal_reais_2022'].median():,.0f}", border=True)

st.divider()
left, right = st.columns(2)
with left:
    titulo_barras = "Comparação selecionada: PIB per capita" if comparacao_ativa else "Destaques: PIB per capita"
    st.subheader(titulo_barras)
    dados_barras = comparacao.copy() if comparacao_ativa else comparacao.nlargest(12, "pib_per_capita_reais_2022")
    dados_barras = dados_barras.sort_values("pib_per_capita_reais_2022")
    altura_barras = max(450, 26 * len(dados_barras) + 130)
    fig_barras = px.bar(
        dados_barras,
        x="pib_per_capita_reais_2022",
        y="municipio_exibicao",
        orientation="h",
        color="pib_per_capita_reais_2022",
        color_continuous_scale="Viridis",
        labels={
            "pib_per_capita_reais_2022": "PIB per capita (R$)",
            "municipio_exibicao": "Município",
        },
        height=altura_barras,
    )
    fig_barras.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(automargin=True),
    )
    if len(dados_barras) > 14:
        st.caption("Role dentro do gráfico para consultar todos os municípios selecionados.")
        with st.container(height=500, border=False):
            st.plotly_chart(fig_barras, width="stretch", key="grafico_pib_comparacao")
    else:
        st.plotly_chart(fig_barras, width="stretch", key="grafico_pib_comparacao")

with right:
    st.subheader("PIB per capita × intensidade formal")
    mostrar_rotulos = comparacao_ativa and len(comparacao) <= 12
    fig_cruzamento = px.scatter(
        comparacao,
        x="pib_per_capita_reais_2022",
        y="intensidade_ocupacao_formal_por_mil_hab_2022",
        size="populacao_residente_2022",
        color="quadrante_economico",
        text="municipio_exibicao" if mostrar_rotulos else None,
        hover_name="territorio_nome",
        labels={
            "pib_per_capita_reais_2022": "PIB per capita (R$)",
            "intensidade_ocupacao_formal_por_mil_hab_2022": "Ocupação formal por mil hab.",
            "quadrante_economico": "Quadrante",
            "populacao_residente_2022": "População",
        },
        size_max=42,
        height=450,
    )
    fig_cruzamento.update_traces(textposition="top center", marker_line_width=0.8, marker_line_color="white")
    fig_cruzamento.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    st.plotly_chart(fig_cruzamento, width="stretch", key="grafico_cruzamento")

st.subheader("Mapa de comparação")
metadados_indicador = INDICADORES_MAPA[indicador_mapa]
coluna_mapa = metadados_indicador["coluna"]
codigos_recorte = set(recorte["territorio_codigo"])
mapa_recorte = mapa_base[mapa_base["territorio_codigo"].isin(codigos_recorte)].copy()
geojson_malha = mapa_base[["codarea", "geometry"]].__geo_interface__
limite_inferior, limite_superior = limites_escala_robusta(mapa_recorte[coluna_mapa])

fig_mapa = px.choropleth(
    mapa_recorte,
    geojson=geojson_malha,
    locations="territorio_codigo",
    featureidkey="properties.codarea",
    color=coluna_mapa,
    hover_name="territorio_nome",
    hover_data={"territorio_codigo": False, "quadrante_economico": True},
    color_continuous_scale="Viridis",
    range_color=(limite_inferior, limite_superior),
    labels={
        coluna_mapa: metadados_indicador["legenda"],
        "quadrante_economico": "Quadrante",
    },
)
fig_mapa.update_traces(marker_line_width=0.45, marker_line_color="white")

if comparacao_ativa:
    codigos_selecionados = comparacao["territorio_codigo"].tolist()
    fig_mapa.add_trace(
        go.Choropleth(
            geojson=geojson_malha,
            locations=codigos_selecionados,
            featureidkey="properties.codarea",
            z=[1] * len(codigos_selecionados),
            zmin=0,
            zmax=1,
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False,
            hoverinfo="skip",
            marker_line_color="#111827",
            marker_line_width=2.4,
            name="Municípios selecionados",
        )
    )

fig_mapa.update_geos(fitbounds="locations", visible=False)
fig_mapa.update_coloraxes(colorbar=dict(title=metadados_indicador["legenda"], thickness=14, len=0.75))
fig_mapa.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=540)
st.plotly_chart(
    fig_mapa,
    width="stretch",
    key="mapa_municipios",
    config={"scrollZoom": False, "displaylogo": False},
)

texto_limite_inferior = metadados_indicador["formato"].format(limite_inferior)
texto_limite_superior = metadados_indicador["formato"].format(limite_superior)
nota_selecao = " Os municípios comparados têm contorno escuro." if comparacao_ativa else ""
st.caption(
    "A cor usa uma escala robusta entre os percentis 5 e 95 "
    f"({texto_limite_inferior} a {texto_limite_superior}); os valores extremos continuam exatos ao passar o mouse."
    f"{nota_selecao}"
)

st.subheader("Crescimento populacional × ocupação formal")
fig_crescimento = px.scatter(
    comparacao,
    x="crescimento_populacional_pct_2010_2022",
    y="intensidade_ocupacao_formal_por_mil_hab_2022",
    color="participacao_administracao_pct_2021",
    text="municipio_exibicao" if comparacao_ativa and len(comparacao) <= 12 else None,
    hover_name="territorio_nome",
    color_continuous_scale="Viridis",
    labels={
        "crescimento_populacional_pct_2010_2022": "Crescimento populacional 2010-2022 (%)",
        "intensidade_ocupacao_formal_por_mil_hab_2022": "Ocupação formal por mil hab.",
        "participacao_administracao_pct_2021": "Administração no VAB (2021, %)",
    },
    height=430,
)
fig_crescimento.update_traces(textposition="top center", marker_line_width=0.8, marker_line_color="white")
fig_crescimento.update_layout(margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig_crescimento, width="stretch", key="grafico_crescimento")

with st.expander("Fontes, metodologia e limitações"):
    st.markdown("""
    - **Fontes:** IBGE/SIDRA, tabelas 9509 (CEMPRE 2022), 5938 (PIB 2021 e PIB 2022) e 4709 (Censo 2022).
    - **Integração:** filtro municipal `N6` e junção 1:1 pelo código IBGE de sete dígitos `territorio_codigo`; nomes não são usados como chave.
    - **Mapa:** cada polígono é associado diretamente ao código `codarea` da malha. A escala entre os percentis 5 e 95 impede que poucos valores extremos escondam as diferenças entre a maioria dos municípios; o valor original permanece disponível no detalhe.
    - **Escala:** PIB em Mil Reais foi multiplicado por 1.000 para o PIB per capita. O salário médio é o indicador mensal oficial da tabela 9509.
    - **Limitações:** CEMPRE mede ocupação formal localizada nas organizações e não captura informalidade nem necessariamente residentes empregados. A estrutura setorial é de 2021 e os demais indicadores principais são de 2022; essa defasagem é uma associação exploratória, não causal.
    """)
