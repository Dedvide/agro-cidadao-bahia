"""
Registry da ontologia — container em memória + consultas cruzadas (Ficha 360).

Demonstra o valor da Camada 1: com as relações tipadas, dá para responder
perguntas que cruzam domínios (ex.: "tudo sobre um município").
"""
from __future__ import annotations

import uuid
from typing import Type, TypeVar

from .atores import Produtor
from .base import BaseEntity
from .ciencia import AnaliseLaboratorial
from .eventos import EventoSanitario
from .territorio import Municipio, Propriedade

T = TypeVar("T", bound=BaseEntity)


class Ontology:
    """Armazena entidades por id e resolve relações."""

    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, BaseEntity] = {}

    def add(self, *entities: BaseEntity):
        """Adiciona uma ou mais entidades. Retorna a entidade (ou a tupla)."""
        for e in entities:
            self._by_id[e.id] = e
        return entities[0] if len(entities) == 1 else entities

    def get(self, entity_id: uuid.UUID) -> BaseEntity | None:
        return self._by_id.get(entity_id)

    def all(self, cls: Type[T]) -> list[T]:
        return [e for e in self._by_id.values() if isinstance(e, cls)]

    def count(self) -> int:
        return len(self._by_id)

    def municipio_360(self, municipio_id: uuid.UUID) -> dict:
        """Ficha 360: tudo que se conecta a um município (embrião do Digital Twin)."""
        propriedades = [p for p in self.all(Propriedade) if p.municipio_id == municipio_id]
        prop_ids = {p.id for p in propriedades}
        return {
            "municipio": self.get(municipio_id),
            "produtores": [x for x in self.all(Produtor) if x.municipio_id == municipio_id],
            "propriedades": propriedades,
            "analises": [a for a in self.all(AnaliseLaboratorial) if a.propriedade_id in prop_ids],
            "eventos_sanitarios": [e for e in self.all(EventoSanitario) if e.municipio_id == municipio_id],
        }
