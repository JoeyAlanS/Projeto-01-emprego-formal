"""Integração das tabelas SIDRA por código IBGE municipal.

Projeto 1 - Economia e emprego formal no Ceará.
Autores: Joey Alan e Paulo Henrico.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .etl_limpeza import PROCESSED_DIR, ROOT, executar_pipeline_etl


ANALYTICAL_DIR = ROOT / "dados" / "analytical"


def _municipal_wide(nome_arquivo: str) -> pd.DataFrame:
    caminho = PROCESSED_DIR / nome_arquivo
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig",
        dtype={"territorio_codigo": "string", "variavel_codigo": "string"},
    )
    municipal = df[df["nivel_territorial_codigo"].eq("N6")].copy()
    return municipal.pivot_table(
        index=["territorio_codigo", "territorio_nome"],
        columns="variavel_codigo",
        values="valor_numerico",
        aggfunc="first",
    ).reset_index()


def _selecionar(df: pd.DataFrame, variaveis: dict[str, str]) -> pd.DataFrame:
    colunas = ["territorio_codigo", "territorio_nome", *variaveis.keys()]
    selecionado = df[colunas].rename(columns=variaveis).copy()
    return selecionado


def gerar_base_analitica() -> tuple[pd.DataFrame, dict]:
    """Integra CEMPRE, PIB 2021/2022 e Censo 2022 numa base 1:1 municipal."""
    ANALYTICAL_DIR.mkdir(parents=True, exist_ok=True)

    bases = {
        "cempre_2022": _municipal_wide("cempre_2022.csv"),
        "pib_estrutura_2021": _municipal_wide("pib_estrutura_2021.csv"),
        "pib_total_2022": _municipal_wide("pib_total_2022.csv"),
        "censo_pop_2022": _municipal_wide("censo_pop_2022.csv"),
    }
    selecionadas = {
        "cempre_2022": _selecionar(
            bases["cempre_2022"],
            {
                "706": "unidades_locais_2022",
                "367": "empresas_atuantes_2022",
                "707": "pessoal_ocupado_total_2022",
                "708": "pessoal_ocupado_assalariado_2022",
                "662": "salarios_mil_reais_2022",
                "10143": "salario_medio_mensal_reais_2022",
            },
        ),
        "pib_estrutura_2021": _selecionar(
            bases["pib_estrutura_2021"],
            {
                "516": "participacao_agropecuaria_pct_2021",
                "520": "participacao_industria_pct_2021",
                "6574": "participacao_servicos_pct_2021",
                "528": "participacao_administracao_pct_2021",
            },
        ),
        "pib_total_2022": _selecionar(bases["pib_total_2022"], {"37": "pib_mil_reais_2022"}),
        "censo_pop_2022": _selecionar(
            bases["censo_pop_2022"],
            {"93": "populacao_residente_2022", "5936": "variacao_populacao_2010_2022", "10605": "crescimento_populacional_pct_2010_2022"},
        ),
    }

    # Auditoria da cardinalidade antes da junção.
    relatorio = {
        "chave": "territorio_codigo (código IBGE de sete dígitos)",
        "granularidade_saida": "um registro por município do Ceará",
        "cardinalidade_esperada": "1:1 após filtrar N6 e variáveis selecionadas",
        "bases": {},
    }
    for nome, df in selecionadas.items():
        relatorio["bases"][nome] = {
            "municipios": int(df["territorio_codigo"].nunique()),
            "duplicatas_chave": int(df.duplicated("territorio_codigo").sum()),
        }

    resultado = selecionadas["pib_total_2022"]
    for nome in ["censo_pop_2022", "cempre_2022", "pib_estrutura_2021"]:
        direita = selecionadas[nome].drop(columns=["territorio_nome"])
        resultado = resultado.merge(
            direita,
            on="territorio_codigo",
            how="outer",
            indicator=f"_merge_{nome}",
            validate="one_to_one",
        )
        indicador = f"_merge_{nome}"
        relatorio["bases"][nome]["correspondencias_com_acumulado"] = int(resultado[indicador].eq("both").sum())
        relatorio["bases"][nome]["nao_correspondencias_esquerda"] = int(resultado[indicador].eq("left_only").sum())
        relatorio["bases"][nome]["nao_correspondencias_direita"] = int(resultado[indicador].eq("right_only").sum())
        resultado = resultado.drop(columns=indicador)

    # Indicadores derivados: escala do PIB é Mil Reais, convertida para Reais.
    resultado["pib_per_capita_reais_2022"] = resultado["pib_mil_reais_2022"] * 1000 / resultado["populacao_residente_2022"]
    resultado["unidades_locais_por_mil_hab_2022"] = resultado["unidades_locais_2022"] / resultado["populacao_residente_2022"] * 1000
    resultado["intensidade_ocupacao_formal_por_mil_hab_2022"] = resultado["pessoal_ocupado_total_2022"] / resultado["populacao_residente_2022"] * 1000
    resultado["proporcao_assalariados_pct_2022"] = resultado["pessoal_ocupado_assalariado_2022"] / resultado["pessoal_ocupado_total_2022"] * 100
    mediana_pib = resultado["pib_per_capita_reais_2022"].median()
    mediana_intensidade = resultado["intensidade_ocupacao_formal_por_mil_hab_2022"].median()
    resultado["quadrante_economico"] = "baixo PIB per capita / baixa intensidade"
    resultado.loc[(resultado["pib_per_capita_reais_2022"] >= mediana_pib) & (resultado["intensidade_ocupacao_formal_por_mil_hab_2022"] < mediana_intensidade), "quadrante_economico"] = "alto PIB per capita / baixa intensidade"
    resultado.loc[(resultado["pib_per_capita_reais_2022"] < mediana_pib) & (resultado["intensidade_ocupacao_formal_por_mil_hab_2022"] >= mediana_intensidade), "quadrante_economico"] = "baixo PIB per capita / alta intensidade"
    resultado.loc[(resultado["pib_per_capita_reais_2022"] >= mediana_pib) & (resultado["intensidade_ocupacao_formal_por_mil_hab_2022"] >= mediana_intensidade), "quadrante_economico"] = "alto PIB per capita / alta intensidade"
    relatorio["resultado_final"] = {
        "municipios": int(len(resultado)),
        "correspondencias_totais": int(resultado.notna().all(axis=1).sum()),
        "mediana_pib_per_capita_reais": float(mediana_pib),
        "mediana_intensidade_ocupacao_formal_por_mil_hab": float(mediana_intensidade),
    }
    resultado.to_csv(ANALYTICAL_DIR / "base_analitica_municipios.csv", index=False, sep=";", encoding="utf-8-sig")
    (ANALYTICAL_DIR / "relatorio_integracao.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(
        [{"base": k, **v} for k, v in relatorio["bases"].items()]
    ).to_csv(ANALYTICAL_DIR / "relatorio_integracao.csv", index=False, sep=";", encoding="utf-8-sig")
    return resultado, relatorio


if __name__ == "__main__":
    if not (PROCESSED_DIR / "pib_total_2022.csv").exists():
        executar_pipeline_etl()
    base, relatorio = gerar_base_analitica()
    print(f"Base analítica gerada: {len(base)} municípios")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
