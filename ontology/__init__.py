"""
Ontologia Agropecuária — Camada 1 do Bahia Agro Foundry / SIPA-Bahia AI.

Modela as entidades do mundo real do agronegócio baiano e suas relações,
para que dados de fontes diferentes (CETAB, ADAB, INEMA, IBGE, INMET, Embrapa)
sejam cruzados de forma coerente. Agnóstico de banco — Pydantic puro.
"""
from .atores import Pesquisador, Produtor
from .base import (
    BaseEntity, CultureCycle, EventStatus, Fertility, Geometry,
    PointGeometry, PolygonGeometry, ProducerType, RiskLevel, now_utc,
)
from .ciencia import (
    AnaliseLaboratorial, Cultura, PragaDoenca, ProjetoPesquisa, Solo,
)
from .eventos import EventoSanitario
from .infraestrutura import FonteDados
from .registry import Ontology
from .territorio import Municipio, Propriedade

__all__ = [
    "BaseEntity", "now_utc", "PointGeometry", "PolygonGeometry", "Geometry",
    "RiskLevel", "ProducerType", "CultureCycle", "Fertility", "EventStatus",
    "Municipio", "Propriedade", "Produtor", "Pesquisador",
    "Cultura", "Solo", "PragaDoenca", "AnaliseLaboratorial", "ProjetoPesquisa",
    "EventoSanitario", "FonteDados", "Ontology",
]
