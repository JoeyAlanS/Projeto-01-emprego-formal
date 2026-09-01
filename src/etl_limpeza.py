"""ETL reproduzível da camada raw para a camada processed.

Projeto 1 - Economia e emprego formal no Ceará.
Autores: Joey Alan e Paulo Henrico.

"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "dados" / "raw"
PROCESSED_DIR = ROOT / "dados" / "processed"

ARQUIVOS = {
    "cempre_2022": RAW_DIR / "t9509_cempre_economia_emprego_2022_ce_br.csv",
    "pib_estrutura_2021": RAW_DIR / "t5938_pib_estrutura_economica_2021_ce_br.csv",
    "pib_total_2022": RAW_DIR / "t5938_pib_2022_ce_br.csv",
    "censo_pop_2022": RAW_DIR / "t4709_populacao_censo_2022_ce_br.csv",
}

SIMBOLOS_INDISPONIVEIS = ["-", "X", "..", "..."]
SIMBOLOS_SIDRA = ["-", "0", "X", "..", "..."]


def carregar_raw(caminho: Path) -> pd.DataFrame:
    """Carrega um CSV SIDRA sem transformar a camada raw."""
    return pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig",
        dtype={
            "nivel_territorial_codigo": "string",
            "territorio_codigo": "string",
            "ano_codigo": "string",
            "variavel_codigo": "string",
        },
        keep_default_na=False,
    )


def diagnosticar_e_limpar(caminho: Path) -> tuple[pd.DataFrame, dict]:
    """Tipa os dados e retorna a tabela tratada junto do diagnóstico."""
    df = carregar_raw(caminho)
    chave = ["territorio_codigo", "ano_codigo", "variavel_codigo"]
    valores = df["valor"].astype("string").str.strip()
    contagem_simbolos = {simbolo: int(valores.eq(simbolo).sum()) for simbolo in SIMBOLOS_SIDRA}

    # Zero é informação válida; apenas os demais símbolos especiais viram NA.
    valor_para_numero = valores.where(~valores.isin(SIMBOLOS_INDISPONIVEIS))
    df["valor_numerico"] = pd.to_numeric(valor_para_numero, errors="coerce")
    df["status_valor"] = "disponivel"
    df.loc[valores.eq("0"), "status_valor"] = "zero_informado"
    df.loc[valores.isin(SIMBOLOS_INDISPONIVEIS), "status_valor"] = "indisponivel_sidra"
    df.loc[valor_para_numero.eq(""), "status_valor"] = "ausente"

    municipal = df[df["nivel_territorial_codigo"].eq("N6")]
    diagnostico = {
        "arquivo_raw": str(caminho.relative_to(ROOT)).replace("\\", "/"),
        "linhas": int(len(df)),
        "colunas": int(len(df.columns) - 2),
        "periodos": sorted(df["ano_codigo"].dropna().unique().tolist()),
        "unidades": sorted(df["unidade"].dropna().unique().tolist()),
        "niveis": {str(k): int(v) for k, v in df["nivel_territorial_codigo"].value_counts().items()},
        "municipios": int(municipal["territorio_codigo"].nunique()),
        "duplicatas_chave": int(df.duplicated(chave).sum()),
        "simbolos_sidra": contagem_simbolos,
        "valores_numericos_na": int(df["valor_numerico"].isna().sum()),
        "regra_tratamento": "-, X, .. e ... foram tipados como NA; 0 foi preservado como zero válido.",
    }
    return df, diagnostico


def executar_pipeline_etl() -> dict[str, dict]:
    """Gera os CSVs processados e o inventário de qualidade."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    diagnosticos: dict[str, dict] = {}
    for nome, caminho in ARQUIVOS.items():
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo raw não encontrado: {caminho}")
        tratado, diagnostico = diagnosticar_e_limpar(caminho)
        tratado.to_csv(PROCESSED_DIR / f"{nome}.csv", index=False, sep=";", encoding="utf-8-sig")
        diagnosticos[nome] = diagnostico

    (PROCESSED_DIR / "diagnostico_qualidade.json").write_text(
        json.dumps(diagnosticos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame(diagnosticos).T.reset_index(names="base").to_csv(
        PROCESSED_DIR / "diagnostico_qualidade.csv", index=False, sep=";", encoding="utf-8-sig"
    )
    return diagnosticos


if __name__ == "__main__":
    resultado = executar_pipeline_etl()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
