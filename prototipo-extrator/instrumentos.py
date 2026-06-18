"""
Integração com instrumentos de laboratório — captura automática do resultado bruto.

ESBOÇO com um adaptador funcional (CSV genérico / qPCR) + stubs documentados para os
formatos proprietários. O objetivo é eliminar a digitação: a máquina exporta → o sistema
lê → vira `Resultado` no esquema canônico → entra no fluxo LIMS.

Padrão: cada instrumento tem um ADAPTADOR (export → list[Resultado]). Novos instrumentos =
novo adaptador, sem mexer no resto. Em produção, uma "pasta-cofre" observada por um watcher
dispara o adaptador certo pelo tipo de arquivo.

Padrões abertos a mirar (preferir SEMPRE a exportação aberta, não reverter binário):
  - Cromatografia (HPLC/GC): ANDI/AIA -> netCDF (.cdf)
  - Espectrometria de massas: mzML (via ProteoWizard msconvert)
  - Comunicação analisador↔LIS: ASTM E1394 / HL7
"""
from __future__ import annotations

import csv
from pathlib import Path

from schema import Resultado, TipoResultado


# ───────────────────────── Adaptador FUNCIONAL: qPCR (CSV de Ct) ─────────────────────────

def parse_qpcr_csv(caminho: Path) -> list[Resultado]:
    """
    Lê o export de um termociclador qPCR e produz resultados de DIAGNÓSTICO.
    Colunas esperadas: alvo, resultado, ct  (separador ';' ou ',').
    """
    return [
        Resultado(
            tipo=TipoResultado.diagnostico,
            alvo=(linha.get("alvo") or "").strip().lower(),
            resultado_diagnostico=(linha.get("resultado") or "").strip().lower(),
            ct=float(linha["ct"].replace(",", ".")) if linha.get("ct") else None,
            metodo="qPCR",
        )
        for linha in _ler_csv(caminho)
    ]


# ───────────────────────── Adaptador FUNCIONAL: analisador quantitativo (CSV) ─────────────

def parse_quantitativo_csv(caminho: Path) -> list[Resultado]:
    """
    Lê export genérico de analisador (ex.: espectrômetro de solo/metais).
    Colunas esperadas: analito, valor, unidade.
    """
    res = []
    for linha in _ler_csv(caminho):
        valor = linha.get("valor")
        res.append(Resultado(
            tipo=TipoResultado.quantitativo,
            analito=(linha.get("analito") or "").strip().lower(),
            valor=float(valor.replace(",", ".")) if valor else None,
            unidade=(linha.get("unidade") or None),
        ))
    return res


def _ler_csv(caminho: Path) -> list[dict]:
    texto = Path(caminho).read_text(encoding="utf-8")
    sep = ";" if texto.splitlines()[0].count(";") >= texto.splitlines()[0].count(",") else ","
    return list(csv.DictReader(texto.splitlines(), delimiter=sep))


# ───────────────────────── STUBS: formatos proprietários / padrões (Fase 3) ─────────────

def parse_netcdf_cromatografia(caminho: Path) -> list[Resultado]:
    """STUB. Cromatografia em ANDI/AIA netCDF (.cdf). Libs: netCDF4/xarray para ler o sinal;
    integrar picos → concentrações. Preferir export netCDF do software do equipamento."""
    raise NotImplementedError("Adaptador netCDF (cromatografia) — Fase 3.")


def parse_mzml_massas(caminho: Path) -> list[Resultado]:
    """STUB. Espectrometria de massas em mzML (pymzml/pyteomics). Gerar mzML via
    ProteoWizard msconvert a partir do .raw proprietário."""
    raise NotImplementedError("Adaptador mzML (massas) — Fase 3.")


def parse_astm_lis(stream) -> list[Resultado]:
    """STUB. Mensageria analisador↔LIS no protocolo ASTM E1394 / HL7 (tempo real)."""
    raise NotImplementedError("Conector ASTM/HL7 — Fase 3.")


# Registro: extensão/tipo → adaptador. O watcher de produção usa isto para rotear.
ADAPTADORES = {
    "qpcr_csv": parse_qpcr_csv,
    "quantitativo_csv": parse_quantitativo_csv,
    "cdf": parse_netcdf_cromatografia,   # stub
    "mzml": parse_mzml_massas,           # stub
}


def importar(tipo: str, caminho: Path) -> list[Resultado]:
    """Roteia para o adaptador do tipo de instrumento."""
    if tipo not in ADAPTADORES:
        raise ValueError(f"Sem adaptador para '{tipo}'. Disponíveis: {list(ADAPTADORES)}")
    return ADAPTADORES[tipo](Path(caminho))
