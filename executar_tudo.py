"""Executa preparação, integração, evidências e figuras do projeto."""

from src.etl_limpeza import executar_pipeline_etl
from src.integracao_analytical import gerar_base_analitica


if __name__ == "__main__":
    print("=== ETAPA 1: raw -> processed ===")
    executar_pipeline_etl()
    print("=== ETAPA 2: processed -> analytical ===")
    base, relatorio = gerar_base_analitica()
    print(f"=== Concluído: {len(base)} municípios integrados ===")
    print(f"Correspondências após cada junção: {relatorio['bases']}")
