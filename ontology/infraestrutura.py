"""
Domínio INFRAESTRUTURA — Fonte de Dados.
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from .base import BaseEntity


class FonteDados(BaseEntity):
    """
    Fonte de dados que alimenta a ontologia (Análises, Eventos Sanitários...).
    O sistema de origem fica em `origin_system` (herdado da base).
    """
    name: str = Field(description="Nome da fonte (ex.: 'CETAB-LIMS', 'ADAB-SIDAB', 'IBGE-Localidades').")
    data_type: Optional[str] = Field(default=None, description="Tipo de dado fornecido (laudos, focos, malha...).")
    frequency: Optional[str] = Field(default=None, description="Frequência de atualização (diária, eventual...).")
