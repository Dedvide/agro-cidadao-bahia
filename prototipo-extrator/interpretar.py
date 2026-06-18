"""
Camada de interpretação multi-eixo: transforma cada resultado bruto em algo
que o gestor e o produtor entendem — com explicabilidade e flag de alerta.

Uma `Interpretacao` é uniforme para os 3 tipos, então painel e banco a consomem
sem saber o eixo:
    rotulo          -> o que foi medido (analito / patógeno / espécie)
    valor_exibicao  -> "8.0 mg/dm3" | "positivo (Ct 28)" | "12 adulto"
    classe          -> baixo/alto/positivo/infestacao_alta/...
    detalhe         -> faixa aplicada / explicação (explicabilidade)
    recomendacao    -> ação sugerida
    alerta          -> True se contribui para o status "requer atenção"
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import limites_referencia as ref
from schema import Laudo, Resultado, TipoResultado

# classes "ruins" que disparam alerta no tipo quantitativo
_CLASSES_ALERTA = {"baixo", "muito baixo (acido)", "acima do lmr",
                   "acima do limite", "fora do padrao"}


@dataclass
class Interpretacao:
    tipo: str
    rotulo: str
    valor_exibicao: str
    classe: Optional[str]
    detalhe: Optional[str]
    recomendacao: Optional[str]
    alerta: bool


def _classificar_faixa(faixas, valor):
    for inferior, superior, classe in faixas:
        if inferior <= valor < superior:
            return classe, f"[{inferior}, {superior})"
    return None, None


def _interp_quantitativo(categoria: str, r: Resultado) -> Interpretacao:
    rotulo = r.analito or "?"
    unidade = r.unidade or ""
    exib = f"{r.valor} {unidade}".strip() if r.valor is not None else (r.valor_texto or "—")
    classe = detalhe = recomendacao = None

    if r.valor is not None and categoria in ref.LMR and r.analito in ref.LMR[categoria]:
        lmr = ref.LMR[categoria][r.analito]
        if r.valor <= lmr:
            classe, detalhe = "conforme", f"LMR = {lmr}"
        else:
            classe, detalhe = "acima do LMR", f"LMR = {lmr}"
            recomendacao = ref.RECOMENDACAO_NAO_CONFORME
    elif r.valor is not None:
        faixas = ref.FAIXAS.get(categoria, {}).get(r.analito)
        if faixas:
            classe, detalhe = _classificar_faixa(faixas, r.valor)
            recomendacao = ref.RECOMENDACOES_QUANT.get((categoria, r.analito, classe))
            if recomendacao is None and classe in _CLASSES_ALERTA:
                recomendacao = ref.RECOMENDACAO_NAO_CONFORME

    alerta = bool(classe) and classe.lower() in _CLASSES_ALERTA
    return Interpretacao("quantitativo", rotulo, exib, classe, detalhe, recomendacao, alerta)


def _interp_diagnostico(r: Resultado) -> Interpretacao:
    rotulo = (r.alvo or "?").upper()
    res = (r.resultado_diagnostico or "—").lower()
    exib = res + (f" (Ct {r.ct})" if r.ct is not None else "")
    positivo = res == "positivo"
    recomendacao = None
    if positivo:
        recomendacao = ref.DIAGNOSTICO_RECOMENDACAO.get(
            (r.alvo or "").lower(), ref.DIAGNOSTICO_RECOMENDACAO["_default"]
        )
    detalhe = "qPCR" if r.ct is not None else None
    return Interpretacao("diagnostico", rotulo, exib, res, detalhe, recomendacao, positivo)


def _interp_identificacao(r: Resultado) -> Interpretacao:
    rotulo = r.taxon or "?"
    estagio = r.estagio or "indivíduos"
    exib = f"{r.contagem} {estagio}" if r.contagem is not None else "—"
    classe = detalhe = recomendacao = None
    alerta = False
    if r.contagem is not None:
        classe, detalhe = _classificar_faixa(ref.NIVEIS_CONTAGEM["default"], r.contagem)
        recomendacao = ref.RECOMENDACAO_INFESTACAO.get(classe)
        alerta = classe == "alto"
    return Interpretacao("identificacao", rotulo, exib, classe, detalhe, recomendacao, alerta)


def interpretar_resultado(categoria: str, r: Resultado) -> Interpretacao:
    if r.tipo == TipoResultado.diagnostico:
        return _interp_diagnostico(r)
    if r.tipo == TipoResultado.identificacao:
        return _interp_identificacao(r)
    return _interp_quantitativo(categoria, r)


def interpretar_laudo(laudo: Laudo) -> list[Interpretacao]:
    return [interpretar_resultado(laudo.categoria_analise, r) for r in laudo.resultados]
