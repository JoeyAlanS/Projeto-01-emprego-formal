"""Extração de Dados e Coordenadas para o Relatório LaTeX

Equipe: Joey Alan e Paulo Henrico
"""

import pandas as pd

df = pd.read_csv(
    "dados/analytical/base_analitica_pib_pop_2022.csv",
    sep=";",
    dtype={"territorio_codigo": "string"},
)

# 1. Top 5 PIB per capita para o Gráfico de Barras
top5 = df.sort_values(by="pib_per_capita", ascending=False).head(5)
print("=== COORDENADAS: TOP 5 PIB PER CAPITA (GRÁFICO 1) ===")
for _, row in top5.iterrows():
  nome_resumido = (
      row["territorio_nome"].split(" - ")[0].replace("São ", "S. ")
  )
  print(f"({nome_resumido}, {int(row['pib_per_capita'])})")

# 2. Amostra de dispersão (População em milhares x PIB em bilhões)
amostra = df.sample(10, random_state=42)
print("\n=== COORDENADAS: DISPERSÃO POP x PIB (GRÁFICO 2) ===")
for _, row in amostra.iterrows():
  pop_milhares = row["populacao_residente"] / 1000
  pib_bilhoes = (row["pib_mil_reais"] * 1000) / 1e9
  print(f"({pop_milhares:.1f}, {pib_bilhoes:.2f})")