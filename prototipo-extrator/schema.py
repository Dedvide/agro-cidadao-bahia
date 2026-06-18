"""
Esquema canônico de dados do CETAB — Fase 2 (extrator), versão multi-eixo.

ESTRUTURA ÚNICA para a qual TODO laudo, de qualquer formato e de qualquer um dos
5 eixos do CETAB, é normalizado.

Há TRÊS naturezas de resultado, cobrindo todos os eixos:
  - quantitativo   → química (solo, água, foliar, resíduos, metais, alimentos)
  - diagnostico    → biologia molecular / sanidade (HLB, CVC, viroses) — pos/neg + Ct
  - identificacao  → entomologia / pragas (moscas-das-frutas, fungos) — espécie + contagem

Pydantic v2.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TipoAmostra(str, Enum):
    solo = "solo"
    agua = "agua"
    foliar = "foliar"
    tecido_vegetal = "tecido_vegetal"
    fruto = "fruto"
    mel = "mel"
    bebida = "bebida"
    inseto = "inseto"
    planta = "planta"
    outro = "outro"


class TipoSolicitante(str, Enum):
    produtor_rural = "produtor_rural"
    agricultura_familiar = "agricultura_familiar"
    prefeitura = "prefeitura"
    cooperativa = "cooperativa"
    interno = "interno"
    outro = "outro"


class TipoResultado(str, Enum):
    quantitativo = "quantitativo"
    diagnostico = "diagnostico"
    identificacao = "identificacao"


class Resultado(BaseModel):
    """Um item medido/observado no laudo. Os campos usados dependem de `tipo`."""

    tipo: TipoResultado = Field(
        default=TipoResultado.quantitativo,
        description="quantitativo (número+unidade) | diagnostico (pos/neg+Ct) | identificacao (espécie+contagem).",
    )

    # --- tipo = quantitativo ---
    analito: Optional[str] = Field(
        default=None,
        description="Parâmetro medido, minúsculo sem acento. Ex: 'ph','fosforo','chumbo','acidez'.",
    )
    valor: Optional[float] = Field(
        default=None, description="Valor numérico (vírgula→ponto). null se ilegível."
    )
    valor_texto: Optional[str] = Field(
        default=None, description="Valor original não-numérico (ex: '<0,01')."
    )
    unidade: Optional[str] = Field(default=None, description="Ex: 'mg/dm3','mg/kg','%'.")

    # --- tipo = diagnostico ---
    alvo: Optional[str] = Field(
        default=None,
        description="Patógeno/doença pesquisado, minúsculo. Ex: 'hlb','cvc','cabmv','viroide'.",
    )
    resultado_diagnostico: Optional[str] = Field(
        default=None, description="'positivo' | 'negativo' | 'inconclusivo'."
    )
    ct: Optional[float] = Field(default=None, description="Cycle threshold (qPCR), se houver.")

    # --- tipo = identificacao ---
    taxon: Optional[str] = Field(
        default=None, description="Espécie/táxon identificado. Ex: 'ceratitis capitata'."
    )
    contagem: Optional[int] = Field(default=None, description="Nº de indivíduos/colônias.")
    estagio: Optional[str] = Field(default=None, description="Ex: 'adulto','larva','ovo'.")

    # --- comum ---
    metodo: Optional[str] = Field(default=None, description="Método analítico, se informado.")


class Laudo(BaseModel):
    """Um laudo de análise do CETAB normalizado para o esquema canônico."""

    laudo_id: Optional[str] = Field(default=None, description="Número/identificador do laudo.")
    categoria_analise: str = Field(
        default="nao_classificada",
        description="Eixo/tipo da análise, minúsculo. Ex: 'fertilidade_solo','analise_agua',"
        "'residuos_agrotoxicos','metais_pesados','qualidade_alimentos','diagnostico_molecular',"
        "'monitoramento_pragas','fitopatologia'.",
    )
    tipo_amostra: TipoAmostra = Field(description="Tipo de material analisado.")
    data_coleta: Optional[str] = Field(default=None, description="AAAA-MM-DD se disponível.")
    data_analise: Optional[str] = Field(default=None, description="AAAA-MM-DD se disponível.")

    solicitante_nome: Optional[str] = Field(default=None)
    solicitante_tipo: Optional[TipoSolicitante] = Field(default=None)
    municipio: Optional[str] = Field(default=None, description="Município da amostra (Bahia).")
    propriedade: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)

    laboratorio: Optional[str] = Field(default=None)
    resultados: list[Resultado] = Field(description="Todos os itens medidos/observados no laudo.")

    # Human-in-the-loop / trilha de auditoria (exigência do edital ENAP)
    confianca_geral: float = Field(
        description="Confiança da extração, 0.0 a 1.0. Use < 0.7 quando houver ambiguidade."
    )
    campos_incertos: list[str] = Field(default_factory=list)
    observacoes_extracao: Optional[str] = Field(default=None)


LAUDO_JSON_SCHEMA = Laudo.model_json_schema()
