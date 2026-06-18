"""
Domínio ATORES — Produtor e Pesquisador.
"""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import Field

from .base import BaseEntity, ProducerType


class Produtor(BaseEntity):
    """Produtor rural (pessoa física ou jurídica)."""
    document: str = Field(description="CPF ou CNPJ (obrigatório).")
    name: str = Field(description="Nome do produtor.")
    producer_type: Optional[ProducerType] = Field(default=None)
    municipio_id: Optional[uuid.UUID] = Field(default=None, description="Relação → Município.")


class Pesquisador(BaseEntity):
    """Pesquisador vinculado a uma instituição."""
    name: str = Field(description="Nome do pesquisador.")
    institution: Optional[str] = Field(default=None, description="Instituição (CETAB, UFRB, Embrapa...).")
    research_area: Optional[str] = Field(default=None)
    orcid: Optional[str] = Field(default=None)
