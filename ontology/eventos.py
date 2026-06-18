"""
Domínio EVENTOS — Evento Sanitário.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseEntity, EventStatus


class EventoSanitario(BaseEntity):
    """Ocorrência fitossanitária/zoossanitária em um município, afetando uma cultura."""
    event_type: str = Field(description="Tipo do evento (ex.: 'foco_hlb', 'surto_ferrugem').")
    occurred_at: datetime = Field(description="Data/hora da ocorrência (UTC).")
    municipio_id: uuid.UUID = Field(description="Relação obrigatória → Município.")
    culture_id: Optional[uuid.UUID] = Field(default=None, description="Relação → Cultura afetada.")
    praga_id: Optional[uuid.UUID] = Field(default=None, description="Relação → Praga/Doença.")
    status: EventStatus = Field(default=EventStatus.suspeito)
