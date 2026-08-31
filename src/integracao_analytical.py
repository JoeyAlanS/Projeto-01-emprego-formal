"""Módulo de Integração Relacional (Processed -> Analytical)

Equipe: Joey Alan e Paulo Henrico
"""

import os
import pandas as pd


def gerar_base_analitica() -> pd.DataFrame:
  os.makedirs("dados/analytical", exist_ok=True)

  # 1. Carregamento dos dados tratados
  df_pib22 = pd.read_csv(
      "dados/processed/pib_total_2022.csv",
      sep=";",
      dtype={"territorio_codigo": "string"},
  )
  df_pop22 = pd.read_csv(
      "dados/processed/censo_pop_2022.csv",
      sep=";",
      dtype={"territorio_codigo": "string", "variavel_codigo": "string"},
  )

  # 2. Filtro estrito de nível municipal (N6) e variáveis específicas
  pib_mun = df_pib22[df_pib22["nivel_territorial_codigo"] == "N6"][
      ["territorio_codigo", "territorio_nome", "valor_numerico"]
  ].rename(columns={"valor_numerico": "pib_mil_reais"})

  pop_mun = df_pop22[
      (df_pop22["nivel_territorial_codigo"] == "N6")
      & (df_pop22["variavel_codigo"] == "93")
  ][["territorio_codigo", "valor_numerico"]].rename(
      columns={"valor_numerico": "populacao_residente"}
  )

  # 3. Join relacional 1:1 com validação
  df_merge = pd.merge(
      pib_mun, pop_mun, on="territorio_codigo", how="outer", indicator=True
  )

  matches = (df_merge["_merge"] == "both").sum()
  left_only = (df_merge["_merge"] == "left_only").sum()
  right_only = (df_merge["_merge"] == "right_only").sum()

  print("\n=== Relatório de Integração ===")
  print(f"Correspondências exatas (both): {matches} ({matches/184*100:.1f}%)")
  print(f"Não correspondências à esquerda: {left_only}")
  print(f"Não correspondências à direita: {right_only}")

  df_analitica = df_merge[df_merge["_merge"] == "both"].drop(
      columns=["_merge"]
  )

  # 4. Derivação do PIB per capita corrigindo escala (Mil R$ -> R$)
  df_analitica["pib_per_capita"] = (
      df_analitica["pib_mil_reais"] * 1000
  ) / df_analitica["populacao_residente"]

  caminho_saida = "dados/analytical/base_analitica_pib_pop_2022.csv"
  df_analitica.to_csv(caminho_saida, index=False, sep=";")
  print(f"Base analítica salva com sucesso em: {caminho_saida}")

  return df_analitica


if __name__ == "__main__":
  gerar_base_analitica()
