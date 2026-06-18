"""
Camada 2 — Data Fabric.

Integra fontes heterogêneas na ontologia por meio de CONECTORES, registrando a
LINHAGEM (de qual sistema veio cada entidade, via `origin_system`).

Conectores incluídos:
  - CETABLaudosConnector : laudos do SIPA (SQLite) → Propriedade + AnaliseLaboratorial
                           (+ EventoSanitario para diagnósticos moleculares positivos)
  - resolução de Município pelo código IBGE (âncora canônica)
"""
from __future__ import annotations

import sqlite3
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from typing import Protocol

from .base import EventStatus
from .ciencia import AnaliseLaboratorial
from .eventos import EventoSanitario
from .infraestrutura import FonteDados
from .linker import laudo_sipa_para_analise, resolver_municipio
from .registry import Ontology
from .territorio import Propriedade


def _norm(s: str) -> str:
    nf = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in nf if not unicodedata.combining(c))


class Connector(Protocol):
    name: str
    origin_system: str
    def run(self, ontology: Ontology) -> None: ...


class CETABLaudosConnector:
    """Lê laudos do SIPA (SQLite) e materializa Propriedade + Análise + Evento."""
    name = "CETAB-LIMS"
    origin_system = "CETAB-SIPA"

    def __init__(self, sqlite_path, ibge_map: dict[str, str]):
        self.sqlite_path = str(sqlite_path)
        self.ibge_map = ibge_map  # normalize(nome) -> codigo IBGE

    def run(self, ontology: Ontology) -> None:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        prop_por_municipio = {}

        laudos = conn.execute(
            "SELECT id, laudo_id, municipio, categoria_analise, data_coleta, laboratorio FROM laudo").fetchall()
        for l in laudos:
            ibge = self.ibge_map.get(_norm(l["municipio"]))
            if not ibge:
                continue  # município não resolvido no IBGE
            mun = resolver_municipio(ontology, ibge, l["municipio"])
            # uma "propriedade" representativa por município
            if mun.id not in prop_por_municipio:
                prop = Propriedade(name=f"Amostras — {l['municipio']}", municipio_id=mun.id,
                                   origin_system="CETAB-SIPA")
                ontology.add(prop)
                prop_por_municipio[mun.id] = prop.id
            resultados = conn.execute(
                "SELECT rotulo, valor, valor_exibicao FROM resultado WHERE laudo_fk = ?", (l["id"],)).fetchall()
            laudo_dict = {
                "laudo_id": l["laudo_id"], "categoria_analise": l["categoria_analise"],
                "data_coleta": l["data_coleta"], "laboratorio": l["laboratorio"],
                "resultados": [{"rotulo": r["rotulo"], "valor": r["valor"],
                                "valor_exibicao": r["valor_exibicao"]} for r in resultados],
            }
            ontology.add(laudo_sipa_para_analise(laudo_dict, prop_por_municipio[mun.id]))

        # diagnósticos moleculares positivos → Evento Sanitário
        positivos = conn.execute(
            """SELECT l.municipio mun, r.alvo alvo FROM resultado r JOIN laudo l ON l.id=r.laudo_fk
               WHERE r.alvo IS NOT NULL AND r.resultado_diagnostico='positivo'""").fetchall()
        for p in positivos:
            ibge = self.ibge_map.get(_norm(p["mun"]))
            if not ibge:
                continue
            mun = resolver_municipio(ontology, ibge, p["mun"])
            ontology.add(EventoSanitario(
                event_type=f"foco_{p['alvo']}", occurred_at=datetime.now(timezone.utc),
                municipio_id=mun.id, status=EventStatus.confirmado, origin_system="CETAB-SIPA"))
        conn.close()


class DataFabric:
    """Orquestra os conectores sobre uma ontologia, registrando linhagem."""

    def __init__(self):
        self.ontology = Ontology()
        self.connectors: list[Connector] = []

    def register(self, connector: Connector) -> "DataFabric":
        self.connectors.append(connector)
        # cada conector é, ele próprio, uma Fonte de Dados
        self.ontology.add(FonteDados(name=connector.name, origin_system=connector.origin_system,
                                     data_type="múltiplos", frequency="sob demanda"))
        return self

    def run(self) -> Ontology:
        for c in self.connectors:
            c.run(self.ontology)
        return self.ontology

    def lineage(self) -> list[tuple[str, int]]:
        """Contagem de entidades por sistema de origem (origin_system)."""
        cont = Counter(e.origin_system for e in self.ontology._by_id.values())
        return cont.most_common()
