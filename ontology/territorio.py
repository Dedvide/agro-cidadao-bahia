"""
Domínio TERRITÓRIO — Município e Propriedade.
"""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import Field

from .base import BaseEntity, Geometry


class Municipio(BaseEntity):
    """Município baiano, ancorado no código IBGE (chave de cruzamento entre fontes)."""
    ibge_code: str = Field(description="Código IBGE de 7 dígitos (chave canônica).")
    name: str = Field(description="Nome do município.")
    region: Optional[str] = Field(default=None, description="Região (ex.: Recôncavo, Oeste, Litoral Sul).")
    area_km2: Optional[float] = Field(default=None)
    geometry: Optional[Geometry] = Field(default=None, description="Limite/centroide em GeoJSON.")


class Propriedade(BaseEntity):
    """Propriedade rural — relaciona-se a um Município, um Produtor e um Solo."""
    name: str = Field(description="Nome da propriedade/fazenda/sítio.")
    municipio_id: uuid.UUID = Field(description="Relação obrigatória → Município.")
    produtor_id: Optional[uuid.UUID] = Field(default=None, description="Relação → Produtor.")
    soil_id: Optional[uuid.UUID] = Field(default=None, description="Relação → Solo (1:1).")
    culture_ids: list[uuid.UUID] = Field(default_factory=list, description="Culturas cultivadas (N:N).")
    location: Optional[Geometry] = Field(default=None, description="Geolocalização (GeoJSON Point).")
    area_ha: Optional[float] = Field(default=None)
    land_use: Optional[str] = Field(default=None, description="Tipo de uso do solo.")
