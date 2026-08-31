"""Script de Execução Geral do Pipeline

Executa ETL e Integração Analítica em sequência.
"""

from src.etl_limpeza import executar_pipeline_etl
from src.integracao_analytical import gerar_base_analitica

if __name__ == "__main__":
  print("=== ETAPA 1: Ingestão e Limpeza (Raw -> Processed) ===")
  executar_pipeline_etl()

  print("\n=== ETAPA 2: Integração Relacional (Processed -> Analytical) ===")
  gerar_base_analitica()

  print("\nPipeline finalizado com sucesso!")