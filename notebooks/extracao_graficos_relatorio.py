"""Gera as duas visualizações preliminares e os números do acompanhamento."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "dados" / "analytical" / "base_analitica_municipios.csv"
FIG_DIR = ROOT / "docs" / "figuras"


def moeda(valor: float) -> str:
    return f"R\\$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_figuras_e_macros() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(BASE, sep=";", encoding="utf-8-sig", dtype={"territorio_codigo": "string"})
    plt.style.use("seaborn-v0_8-whitegrid")
    azul = "#087E8B"
    coral = "#F25F5C"

    top = df.nlargest(10, "pib_per_capita_reais_2022").sort_values("pib_per_capita_reais_2022")
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.barh(top["territorio_nome"].str.replace(" - CE", "", regex=False), top["pib_per_capita_reais_2022"], color=azul)
    ax.set_xlabel("PIB per capita em 2022 (R$)")
    ax.set_title("Os 10 maiores PIBs per capita do Ceará")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f} mil"))
    fig.tight_layout()
    fig.savefig(FIG_DIR / "top10_pib_per_capita.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    for quadrante, grupo in df.groupby("quadrante_economico"):
        ax.scatter(grupo["pib_per_capita_reais_2022"], grupo["intensidade_ocupacao_formal_por_mil_hab_2022"], s=24, alpha=.75, label=quadrante)
    ax.axvline(df["pib_per_capita_reais_2022"].median(), color="#777", linestyle="--", linewidth=1)
    ax.axhline(df["intensidade_ocupacao_formal_por_mil_hab_2022"].median(), color="#777", linestyle="--", linewidth=1)
    ax.set_xlabel("PIB per capita em 2022 (R$)")
    ax.set_ylabel("Intensidade de ocupação formal\n(pessoal ocupado por mil habitantes)")
    ax.set_title("Cruzamento exploratório entre riqueza e ocupação formal")
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "pib_intensidade_formal.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    top_row = top.iloc[-1]
    low_row = top.iloc[0]
    corr = df[["pib_per_capita_reais_2022", "intensidade_ocupacao_formal_por_mil_hab_2022"]].corr().iloc[0, 1]
    macros = f"""% Gerado por notebooks/extracao_graficos_relatorio.py - nao editar manualmente.
\\newcommand{{\\Municipios}}{{{len(df)}}}
\\newcommand{{\\TopMunicipio}}{{{top_row['territorio_nome'].replace(' - CE', '')}}}
\\newcommand{{\\TopPib}}{{{moeda(top_row['pib_per_capita_reais_2022'])}}}
\\newcommand{{\\MenorTopMunicipio}}{{{low_row['territorio_nome'].replace(' - CE', '')}}}
\\newcommand{{\\MedianaPib}}{{{moeda(df['pib_per_capita_reais_2022'].median())}}}
\\newcommand{{\\MedianaIntensidade}}{{{df['intensidade_ocupacao_formal_por_mil_hab_2022'].median():.1f}}}
\\newcommand{{\\CorrelacaoPibIntensidade}}{{{corr:.2f}}}
\\newcommand{{\\Correspondencias}}{{184}}
\\newcommand{{\\NaoCorrespondencias}}{{0}}
"""
    (ROOT / "docs" / "dados_relatorio.tex").write_text(macros, encoding="utf-8")
    print(macros)


if __name__ == "__main__":
    gerar_figuras_e_macros()
