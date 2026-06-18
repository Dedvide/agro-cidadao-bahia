"""
Modelos do CRM Agro Governamental (Camada Operacional) — entrada de dados pelos técnicos.

São os formulários que o técnico preenche em campo: cadastro de produtor/propriedade,
registro de atendimento (visita = prontuário) e abertura de ocorrência (fiscalização/sanidade).
Pydantic → validação + documentação automática na API.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProdutorIn(BaseModel):
    documento: str = Field(description="CPF ou CNPJ.")
    nome: str
    tipo: Optional[str] = Field(default=None, description="agricultura_familiar, pequeno, medio, grande, cooperativa.")
    municipio: Optional[str] = None
    telefone: Optional[str] = None


class PropriedadeIn(BaseModel):
    nome: str
    produtor_id: int = Field(description="Produtor dono (relação).")
    municipio: Optional[str] = None
    area_ha: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cultura_principal: Optional[str] = None


class AtendimentoIn(BaseModel):
    """Visita/orientação técnica — vira o prontuário da propriedade."""
    propriedade_id: int
    tecnico: str
    data: str = Field(description="AAAA-MM-DD.")
    tipo: str = Field(default="visita", description="visita | orientacao | coleta | retorno.")
    problema: Optional[str] = Field(default=None, description="Problema identificado (ex.: lagarta-do-cartucho).")
    orientacao: Optional[str] = None
    retorno_previsto: Optional[str] = Field(default=None, description="AAAA-MM-DD.")
    status: str = Field(default="aberto", description="aberto | concluido.")


class OcorrenciaIn(BaseModel):
    """Ocorrência de fiscalização/sanidade (futura integração ADAB)."""
    propriedade_id: int
    tipo: str = Field(description="Ex.: foco_hlb, embargo, inspecao.")
    descricao: Optional[str] = None
    data: str = Field(description="AAAA-MM-DD.")
    status: str = Field(default="aberta", description="aberta | em_andamento | encerrada.")
