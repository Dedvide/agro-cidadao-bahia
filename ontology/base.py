"""
Base da Ontologia Agropecuária (Camada 1).

Define a entidade-base (identidade por UUID + auditoria + origem multi-fonte),
os tipos GeoJSON e os enums comuns. Agnóstico de banco de dados — Pydantic puro.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


def now_utc() -> datetime:
    """Timestamp atual em UTC (sempre com timezone)."""
    return datetime.now(timezone.utc)


# ─────────────────────────── GeoJSON ───────────────────────────

class PointGeometry(BaseModel):
    """Ponto GeoJSON. coordinates = [longitude, latitude]."""
    type: Literal["Point"] = "Point"
    coordinates: list[float]


class PolygonGeometry(BaseModel):
    """Polígono GeoJSON (anéis de coordenadas)."""
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[list[float]]]


Geometry = Union[PointGeometry, PolygonGeometry]


# ─────────────────────────── Enums comuns ───────────────────────────

class RiskLevel(str, Enum):
    baixo = "baixo"
    medio = "medio"
    alto = "alto"


class ProducerType(str, Enum):
    agricultura_familiar = "agricultura_familiar"
    pequeno = "pequeno"
    medio = "medio"
    grande = "grande"
    cooperativa = "cooperativa"
    outro = "outro"


class CultureCycle(str, Enum):
    anual = "anual"
    semiperene = "semiperene"
    perene = "perene"


class Fertility(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"


class EventStatus(str, Enum):
    suspeito = "suspeito"
    confirmado = "confirmado"
    em_controle = "em_controle"
    erradicado = "erradicado"


# ─────────────────────────── Entidade-base ───────────────────────────

class BaseEntity(BaseModel):
    """
    Toda entidade da ontologia herda daqui:
    - `id`: identidade única (UUID) — exigência de design;
    - auditoria: `created_at`, `updated_at` (UTC), `source`;
    - `origin_system`: sistema de origem do dado (suporte a múltiplas fontes).
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Identificador único da entidade.")
    created_at: datetime = Field(default_factory=now_utc, description="Criação (UTC).")
    updated_at: datetime = Field(default_factory=now_utc, description="Última atualização (UTC).")
    source: Optional[str] = Field(default=None, description="Rótulo da fonte do dado (ex.: 'laudo 2026/0457').")
    origin_system: str = Field(description="Sistema de origem: CETAB, ADAB, IBGE, INMET, Embrapa, INEMA...")

    def touch(self) -> None:
        """Marca atualização (UTC)."""
        self.updated_at = now_utc()
