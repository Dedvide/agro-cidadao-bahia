"""
Materializa a ontologia a partir dos dados REAIS do SIPA (via Data Fabric) e
exporta para a web: painel/ontologia.json (fichas 360 por município + linhagem).

Rode (da raiz IaCetab/):  python -m ontology.materializar
Pré-requisito: ter rodado um gerador do SIPA (ex.: gerar_painel_demo.py) e o
download do IBGE (saida/ba-lista.json).
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from .data_fabric import CETABLaudosConnector, DataFabric
from .territorio import Municipio, Propriedade
from .ciencia import AnaliseLaboratorial
from .eventos import EventoSanitario

RAIZ = Path(__file__).parent.parent
SAIDA = RAIZ / "prototipo-extrator" / "saida"
PAINEL = RAIZ / "painel"


def _norm(s):
    nf = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in nf if not unicodedata.combining(c))


def _sqlite_sipa() -> Path | None:
    for nome in ("datalake_painel.sqlite", "demo_secretario.sqlite", "centro.sqlite"):
        p = SAIDA / nome
        if p.exists():
            return p
    return None


def main() -> int:
    db = _sqlite_sipa()
    lista = SAIDA / "ba-lista.json"
    if not db or not lista.exists():
        print("Faltam dados. Rode antes:")
        print("  cd ../prototipo-extrator ; python gerar_painel_demo.py")
        print("  (e garanta saida/ba-lista.json do IBGE)")
        return 1

    ibge_map = {_norm(m["nome"]): str(m["id"]) for m in json.loads(lista.read_text(encoding="utf-8"))}

    fabric = DataFabric().register(CETABLaudosConnector(db, ibge_map))
    o = fabric.run()

    # exporta fichas 360 por município
    municipios = sorted(o.all(Municipio), key=lambda m: m.name)
    fichas, resumo_mun = {}, []
    for m in municipios:
        f = o.municipio_360(m.id)
        fichas[m.ibge_code] = {
            "municipio": {"name": m.name, "ibge_code": m.ibge_code, "region": m.region},
            "propriedades": [{"name": p.name, "area_ha": p.area_ha} for p in f["propriedades"]],
            "analises": [{
                "analysis_type": a.analysis_type, "laboratory": a.laboratory,
                "collected_at": a.collected_at.date().isoformat() if a.collected_at else None,
                "result": a.result, "external_ref": a.external_ref, "origin_system": a.origin_system,
            } for a in f["analises"]],
            "eventos": [{"event_type": e.event_type, "status": e.status.value,
                         "occurred_at": e.occurred_at.date().isoformat(), "origin_system": e.origin_system}
                        for e in f["eventos_sanitarios"]],
        }
        resumo_mun.append({"ibge_code": m.ibge_code, "name": m.name, "region": m.region,
                           "n_analises": len(f["analises"]), "n_eventos": len(f["eventos_sanitarios"])})

    saida_json = {
        "resumo": {
            "entidades": o.count(),
            "municipios": len(municipios),
            "propriedades": len(o.all(Propriedade)),
            "analises": len(o.all(AnaliseLaboratorial)),
            "eventos": len(o.all(EventoSanitario)),
        },
        "lineage": [{"origin_system": s, "n": n} for s, n in fabric.lineage()],
        "municipios": resumo_mun,
        "fichas": fichas,
    }
    PAINEL.mkdir(exist_ok=True)
    (PAINEL / "ontologia.json").write_text(json.dumps(saida_json, ensure_ascii=False, indent=2), encoding="utf-8")

    r = saida_json["resumo"]
    print("Ontologia materializada a partir do SIPA:")
    print(f"  {r['entidades']} entidades · {r['municipios']} municípios · "
          f"{r['analises']} análises · {r['eventos']} eventos")
    print("  Linhagem (origin_system):")
    for s, n in fabric.lineage():
        print(f"    {s}: {n}")
    print(f"  -> painel/ontologia.json (fichas 360)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
