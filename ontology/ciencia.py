"""
Domínio CIÊNCIA — Cultura, Solo, Praga/Doença, Análise Laboratorial e Projeto de Pesquisa.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from .base import BaseEntity, CultureCycle, Fertility, RiskLevel


class Cultura(BaseEntity):
    """Cultura agrícola."""
    scientific_name: str = Field(description="Nome científico (ex.: 'Glycine max').")
    common_name: str = Field(description="Nome popular (ex.: 'soja').")
    cycle: Optional[CultureCycle] = Field(default=None)


class Solo(BaseEntity):
    """Solo de uma propriedade, com a análise que o caracterizou."""
    soil_type: Optional[str] = Field(default=None, description="Classe/tipo de solo.")
    ph: Optional[float] = Field(default=None)
    fertility: Optional[Fertility] = Field(default=None)
    analysis_id: Optional[uuid.UUID] = Field(default=None, description="Relação → Análise associada.")


class PragaDoenca(BaseEntity):
    """Praga ou doença e suas culturas hospedeiras."""
    name: str = Field(description="Nome da praga/doença.")
    kind: Optional[str] = Field(default=None, description="'praga' ou 'doenca'.")
    host_culture_ids: list[uuid.UUID] = Field(default_factory=list, description="Culturas hospedeiras (N:N).")
    risk_level: RiskLevel = Field(default=RiskLevel.medio)


class AnaliseLaboratorial(BaseEntity):
    """Análise laboratorial realizada sobre uma propriedade."""
    analysis_type: str = Field(description="Tipo (fertilidade_solo, residuos, diagnostico_molecular...).")
    collected_at: datetime = Field(description="Data/hora da coleta (UTC).")
    result: dict[str, Any] = Field(default_factory=dict, description="Resultados (analito→valor) ou estrutura livre.")
    laboratory: Optional[str] = Field(default=None)
    propriedade_id: uuid.UUID = Field(description="Relação obrigatória → Propriedade.")
    external_ref: Optional[str] = Field(default=None, description="Referência externa (ex.: nº do laudo no SIPA/LIMS).")


class ProjetoPesquisa(BaseEntity):
    """Projeto de pesquisa conduzido por pesquisadores e que estuda culturas."""
    title: str = Field(description="Título do projeto.")
    researcher_ids: list[uuid.UUID] = Field(default_factory=list, description="Relação → Pesquisadores (N:N).")
    culture_ids: list[uuid.UUID] = Field(default_factory=list, description="Relação → Culturas estudadas (N:N).")
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    funder: Optional[str] = Field(default=None, description="Financiador (CNPq, FAPESB...).")
