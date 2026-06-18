"""
Núcleo Científico (C) — Painel Bibliométrico (núcleo).

Calcula indicadores de produção científica a partir de publicacoes_seed.json
(semeado com DOIs reais). A integração VIVA com ORCID/Crossref/OpenAlex substitui
o seed sem mudar o cálculo dos indicadores.

Roda OFFLINE. Gera indicadores_bibliometricos.json (para um futuro painel) e imprime resumo.

Uso:  python bibliometria.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).parent
SEED = AQUI / "publicacoes_seed.json"
SAIDA = AQUI / "indicadores_bibliometricos.json"


def carregar() -> list[dict]:
    return json.loads(SEED.read_text(encoding="utf-8"))["publicacoes"]


def indicadores(pubs: list[dict]) -> dict:
    com_doi = [p for p in pubs if p.get("doi")]
    citacoes = [p["citacoes"] for p in pubs if isinstance(p.get("citacoes"), int)]
    return {
        "total_publicacoes": len(pubs),
        "com_doi": len(com_doi),
        "por_ano": dict(sorted(Counter(p["ano"] for p in pubs if p.get("ano")).items())),
        "por_periodico": dict(Counter(p["periodico"] for p in pubs if p.get("periodico")).most_common()),
        "vinculo_validado": sum(1 for p in pubs if p.get("vinculo_cetab") == "validado"),
        "vinculo_a_validar": sum(1 for p in pubs if p.get("vinculo_cetab") == "a_validar"),
        "citacoes_conhecidas": sum(citacoes),
        "citacoes_pendentes": len(pubs) - len(citacoes),  # a buscar via Crossref/OpenAlex
    }


# ─────────── Integração viva (ESBOÇO — stubs a implementar na Fase 3) ───────────

def buscar_orcid(orcid_id: str) -> list[dict]:
    """STUB. ORCID tem API pública: GET https://pub.orcid.org/v3.0/{id}/works (Accept: json)."""
    raise NotImplementedError("Integração ORCID — Fase 3.")


def enriquecer_citacoes_crossref(doi: str) -> int:
    """STUB. Crossref: GET https://api.crossref.org/works/{doi} -> message.is-referenced-by-count.
    Alternativa: OpenAlex https://api.openalex.org/works/doi:{doi} -> cited_by_count."""
    raise NotImplementedError("Enriquecimento de citações — Fase 3.")


def main() -> int:
    pubs = carregar()
    ind = indicadores(pubs)
    SAIDA.write_text(json.dumps(ind, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== INDICADORES BIBLIOMÉTRICOS (seed) ===")
    print(f"  Publicações:        {ind['total_publicacoes']}  (com DOI: {ind['com_doi']})")
    print(f"  Por ano:            {ind['por_ano']}")
    print(f"  Periódicos:         {len(ind['por_periodico'])}")
    print(f"  Vínculo a validar:  {ind['vinculo_a_validar']}  (validado: {ind['vinculo_validado']})")
    print(f"  Citações conhecidas:{ind['citacoes_conhecidas']}  (pendentes p/ Crossref: {ind['citacoes_pendentes']})")
    print(f"\n  -> {SAIDA.name} gerado.")
    print("  Próximo: ligar ORCID/Crossref para reconstruir a base completa e as citações.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
