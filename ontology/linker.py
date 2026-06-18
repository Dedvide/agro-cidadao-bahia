"""
Linker — liga os dados que o SIPA já produz à ontologia.

Hoje o SIPA gera laudos com `municipio` como string. Aqui convertemos um laudo
do SIPA em uma `AnaliseLaboratorial` da ontologia, resolvendo o Município pelo
código IBGE (a mesma âncora usada no mapa da Bahia).

Decoupled de propósito: recebe dicionários, não importa o schema do SIPA.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from .ciencia import AnaliseLaboratorial
from .territorio import Municipio


def _parse_date(s: Optional[str]) -> datetime:
    """AAAA-MM-DD → datetime UTC; ausente → agora."""
    if s:
        try:
            return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def resolver_municipio(ontology, ibge_code: str, name: str, origin_system: str = "IBGE") -> Municipio:
    """Acha o Município pelo código IBGE no registry; cria se não existir."""
    for m in ontology.all(Municipio):
        if m.ibge_code == ibge_code:
            return m
    mun = Municipio(ibge_code=ibge_code, name=name, origin_system=origin_system)
    ontology.add(mun)
    return mun


def laudo_sipa_para_analise(laudo: dict, propriedade_id: uuid.UUID) -> AnaliseLaboratorial:
    """
    Converte um laudo do SIPA (dict) em AnaliseLaboratorial.
    Espera chaves: laudo_id, categoria_analise, data_coleta, laboratorio, resultados[].
    Cada resultado: {rotulo, valor/valor_exibicao}.
    """
    result = {}
    for r in laudo.get("resultados", []):
        chave = r.get("rotulo") or r.get("analito")
        if chave:
            result[chave] = r.get("valor", r.get("valor_exibicao"))
    return AnaliseLaboratorial(
        analysis_type=laudo.get("categoria_analise", "desconhecida"),
        collected_at=_parse_date(laudo.get("data_coleta")),
        result=result,
        laboratory=laudo.get("laboratorio", "CETAB"),
        propriedade_id=propriedade_id,
        external_ref=laudo.get("laudo_id"),
        origin_system="CETAB-SIPA",
        source=f"laudo {laudo.get('laudo_id', '?')}",
    )
