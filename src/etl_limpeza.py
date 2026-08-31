"""Módulo de Ingestão e Higienização de Dados (Raw -> Processed)

Equipe: Joey Alan e Paulo Henrico
"""

import os
import pandas as pd


def diagnosticar_e_limpar(caminho_arquivo: str, nome_tabela: str) -> pd.DataFrame:
  """Carrega tabela raw, diagnostica duplicatas/nulos e trata símbolos SIDRA."""
  print(f"\n--- Processando: {nome_tabela} ---")

  df = pd.read_csv(
      caminho_arquivo,
      sep=";",
      encoding="utf-8-sig",
      dtype={
          "territorio_codigo": "string",
          "variavel_codigo": "string",
          "ano_codigo": "string",
          "nivel_territorial_codigo": "string",
      },
      keep_default_na=False,
  )

  # 1. Auditoria de duplicatas na chave composta
  duplicatas = df.duplicated(
      subset=["territorio_codigo", "ano_codigo", "variavel_codigo"]
  ).sum()
  print(f"Duplicatas na chave composta: {duplicatas}")

  # 2. Diagnóstico de símbolos especiais do SIDRA
  simbolos_sidra = ["-", "0", "X", "..", "..."]
  qtd_simbolos = df["valor"].isin(simbolos_sidra).sum()
  print(f"Ocorrências de símbolos especiais ({simbolos_sidra}): {qtd_simbolos}")

  # 3. Conversão numérica com coerção
  df["valor_numerico"] = pd.to_numeric(df["valor"], errors="coerce")
  nulos = df["valor_numerico"].isna().sum()
  print(f"Valores nulos gerados após conversão: {nulos}")

  return df


def executar_pipeline_etl():
  os.makedirs("dados/processed", exist_ok=True)

  arquivos = {
      "cempre_2022": (
          "dados/raw/t9509_cempre_economia_emprego_2022_ce_br.csv",
          "CEMPRE 2022",
      ),
      "pib_estrutura_2021": (
          "dados/raw/t5938_pib_estrutura_economica_2021_ce_br.csv",
          "PIB Estrutura 2021",
      ),
      "pib_total_2022": (
          "dados/raw/t5938_pib_2022_ce_br.csv",
          "PIB Total 2022",
      ),
      "censo_pop_2022": (
          "dados/raw/t4709_populacao_censo_2022_ce_br.csv",
          "Censo Demográfico 2022",
      ),
  }

  for chave, (caminho, nome) in arquivos.items():
    if os.path.exists(caminho):
      df_limpo = diagnosticar_e_limpar(caminho, nome)
      df_limpo.to_csv(f"dados/processed/{chave}.csv", index=False, sep=";")
      print(f"Salvo em: dados/processed/{chave}.csv")
    else:
      print(f"Aviso: Arquivo {caminho} não encontrado.")


if __name__ == "__main__":
  executar_pipeline_etl()

