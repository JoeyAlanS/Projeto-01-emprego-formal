"""Pacote de Processamento e Integração de Dados - Projeto 1

Módulos:
    - etl_limpeza: Ingestão, auditoria e higienização (raw -> processed)
    - integracao_analytical: Cruzamentos relacionais (processed -> analytical)
"""

from .etl_limpeza import diagnosticar_e_limpar, executar_pipeline_etl
from .integracao_analytical import gerar_base_analitica

__all__ = [
    "diagnosticar_e_limpar",
    "executar_pipeline_etl",
    "gerar_base_analitica",
]
