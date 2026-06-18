"""
Fixtures / seeds de exemplo da ontologia.

Dados de demonstração com municípios baianos REAIS (código IBGE), culturas
relevantes (soja, cacau), pragas associadas e uma análise laboratorial.
Roda como demonstração:  python -m ontology.fixtures   (a partir da raiz IaCetab/)
"""
from __future__ import annotations

from datetime import datetime, timezone

from .atores import Pesquisador, Produtor
from .base import (CultureCycle, EventStatus, Fertility, PointGeometry, ProducerType, RiskLevel)
from .ciencia import (AnaliseLaboratorial, Cultura, PragaDoenca, ProjetoPesquisa, Solo)
from .eventos import EventoSanitario
from .infraestrutura import FonteDados
from .registry import Ontology
from .territorio import Municipio, Propriedade
from . import linker

UTC = timezone.utc


def build_ontology() -> Ontology:
    o = Ontology()

    # ── Municípios (IBGE real) ──
    cruz = o.add(Municipio(ibge_code="2909802", name="Cruz das Almas", region="Recôncavo",
                           area_km2=145.7, origin_system="IBGE"))
    barreiras = o.add(Municipio(ibge_code="2903201", name="Barreiras", region="Oeste",
                                area_km2=7859.2, origin_system="IBGE"))
    ilheus = o.add(Municipio(ibge_code="2913606", name="Ilhéus", region="Litoral Sul",
                             area_km2=1760.1, origin_system="IBGE"))

    # ── Culturas ──
    soja = o.add(Cultura(scientific_name="Glycine max", common_name="soja",
                         cycle=CultureCycle.anual, origin_system="Embrapa"))
    cacau = o.add(Cultura(scientific_name="Theobroma cacao", common_name="cacau",
                          cycle=CultureCycle.perene, origin_system="Embrapa"))

    # ── Pragas/Doenças (uma por cultura) ──
    o.add(PragaDoenca(name="Ferrugem asiática", kind="doenca", host_culture_ids=[soja.id],
                      risk_level=RiskLevel.alto, origin_system="Embrapa"))
    vassoura = o.add(PragaDoenca(name="Vassoura-de-bruxa", kind="doenca", host_culture_ids=[cacau.id],
                                 risk_level=RiskLevel.alto, origin_system="Embrapa"))
    ferrugem = o.all(PragaDoenca)[0]

    # ── Produtor + Propriedade (Barreiras, soja) ──
    produtor = o.add(Produtor(document="123.456.789-00", name="José da Silva",
                              producer_type=ProducerType.medio, municipio_id=barreiras.id,
                              origin_system="CETAB"))
    prop = o.add(Propriedade(name="Fazenda Boa Vista", municipio_id=barreiras.id,
                             produtor_id=produtor.id, culture_ids=[soja.id],
                             location=PointGeometry(coordinates=[-44.99, -12.15]),
                             area_ha=320.0, land_use="grãos", origin_system="CETAB"))

    # ── Análise laboratorial + Solo ──
    analise = o.add(AnaliseLaboratorial(
        analysis_type="fertilidade_solo", collected_at=datetime(2026, 4, 10, tzinfo=UTC),
        result={"ph": 5.4, "fosforo": 12, "potassio": 48, "materia_organica": 2.1},
        laboratory="CETAB - Lab. de Solos", propriedade_id=prop.id,
        external_ref="2026/0457", origin_system="CETAB-SIPA", source="laudo 2026/0457"))
    solo = o.add(Solo(soil_type="Latossolo", ph=5.4, fertility=Fertility.media,
                      analysis_id=analise.id, origin_system="CETAB-SIPA"))
    prop.soil_id = solo.id
    prop.touch()

    # ── Pesquisa ──
    pesq = o.add(Pesquisador(name="Dra. Marta Souza", institution="CETAB/UFRB",
                             research_area="Fitopatologia", orcid="0000-0002-1234-5678",
                             origin_system="Lattes"))
    o.add(ProjetoPesquisa(title="Manejo de doenças em soja e cacau no Oeste e Sul da Bahia",
                          researcher_ids=[pesq.id], culture_ids=[soja.id, cacau.id],
                          start_date=datetime(2026, 1, 1, tzinfo=UTC), funder="FAPESB",
                          origin_system="CETAB"))

    # ── Evento sanitário (foco de ferrugem em Barreiras) ──
    o.add(EventoSanitario(event_type="foco_ferrugem", occurred_at=datetime(2026, 5, 2, tzinfo=UTC),
                          municipio_id=barreiras.id, culture_id=soja.id, praga_id=ferrugem.id,
                          status=EventStatus.confirmado, origin_system="ADAB"))

    # ── Fonte de dados ──
    o.add(FonteDados(name="CETAB-LIMS", data_type="laudos laboratoriais", frequency="diária",
                     origin_system="CETAB"))
    return o


def _demo():
    o = build_ontology()
    print(f"=== ONTOLOGIA AGROPECUÁRIA (Camada 1) ===")
    print(f"  Entidades carregadas: {o.count()}")
    print(f"  Municípios: {[m.name for m in o.all(Municipio)]}")
    print(f"  Culturas:   {[c.common_name for c in o.all(Cultura)]}")
    print(f"  Pragas:     {[p.name for p in o.all(PragaDoenca)]}")

    barreiras = next(m for m in o.all(Municipio) if m.name == "Barreiras")
    ficha = o.municipio_360(barreiras.id)
    print(f"\n--- FICHA 360 · {ficha['municipio'].name} (IBGE {ficha['municipio'].ibge_code}) ---")
    print(f"  Produtores: {len(ficha['produtores'])} · Propriedades: {len(ficha['propriedades'])} "
          f"· Análises: {len(ficha['analises'])} · Eventos sanitários: {len(ficha['eventos_sanitarios'])}")
    for e in ficha["eventos_sanitarios"]:
        print(f"    evento: {e.event_type} [{e.status.value}] (fonte: {e.origin_system})")

    # Linker: um laudo do SIPA vira AnaliseLaboratorial da ontologia
    laudo = {"laudo_id": "2026/0461", "categoria_analise": "fertilidade_solo",
             "data_coleta": "2026-05-04", "laboratorio": "CETAB",
             "resultados": [{"rotulo": "ph", "valor": 4.8}, {"rotulo": "fosforo", "valor": 6}]}
    prop = o.all(Propriedade)[0]
    nova = linker.laudo_sipa_para_analise(laudo, prop.id)
    o.add(nova)
    print(f"\n--- LINKER (laudo SIPA → ontologia) ---")
    print(f"  {nova.external_ref} → AnaliseLaboratorial {nova.id}")
    print(f"  result={nova.result} · origin_system={nova.origin_system}")
    print("\nOntologia: OK")


if __name__ == "__main__":
    _demo()
