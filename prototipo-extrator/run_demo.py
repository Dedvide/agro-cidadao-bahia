"""
Demonstração ponta a ponta do extrator.

Para cada laudo de exemplo (em formatos DIFERENTES de propósito):
  1. extrai dado estruturado com IA
  2. interpreta contra as faixas de referência
  3. imprime relatório legível + sinaliza itens para revisão humana
  4. salva o JSON canônico em saida/

Rode:  python run_demo.py
Requer: ANTHROPIC_API_KEY no ambiente.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import consultar
from extrator import carregar_texto, extrair
from interpretar import interpretar_laudo
from persistencia import conectar, salvar

PASTA = Path(__file__).parent
EXEMPLOS = sorted((PASTA / "exemplos").glob("laudo_*"))
SAIDA = PASTA / "saida"


def processar(caminho: Path, conn) -> None:
    print("=" * 70)
    print(f"ARQUIVO: {caminho.name}  (formato: {caminho.suffix})")
    print("=" * 70)

    texto = carregar_texto(caminho)
    laudo = extrair(texto)

    # Cabeçalho
    print(f"  Laudo:       {laudo.laudo_id}")
    print(f"  Categoria:   {laudo.categoria_analise}")
    print(f"  Amostra:     {laudo.tipo_amostra.value}")
    print(f"  Município:   {laudo.municipio}")
    print(f"  Solicitante: {laudo.solicitante_nome} ({laudo.solicitante_tipo})")
    print(f"  Coleta:      {laudo.data_coleta}   Análise: {laudo.data_analise}")
    print(f"  Confiança:   {laudo.confianca_geral:.2f}")

    # Resultados interpretados (qualquer um dos 3 tipos)
    print("\n  RESULTADOS INTERPRETADOS")
    for it in interpretar_laudo(laudo):
        flag = "⚠" if it.alerta else " "
        classe = it.classe or "—"
        rec = f"  → {it.recomendacao}" if it.recomendacao else ""
        print(f"   {flag} {it.rotulo:22} {it.valor_exibicao:20} [{classe}]{rec}")

    # Human-in-the-loop / auditoria
    if laudo.campos_incertos or laudo.confianca_geral < 0.7:
        print("\n  ⚠ REVISÃO HUMANA NECESSÁRIA")
        if laudo.campos_incertos:
            print(f"    Campos incertos: {', '.join(laudo.campos_incertos)}")
        if laudo.observacoes_extracao:
            print(f"    Obs: {laudo.observacoes_extracao}")

    # Persiste JSON canônico + grava no Data Lake
    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / f"{caminho.stem}.json"
    destino.write_text(laudo.model_dump_json(indent=2), encoding="utf-8")
    salvar(conn, laudo)
    print(f"\n  JSON salvo em {destino.relative_to(PASTA)} · gravado no Data Lake\n")


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERRO: defina ANTHROPIC_API_KEY.\n"
            "PowerShell:  $env:ANTHROPIC_API_KEY = 'sua-chave'"
        )
        return 1
    if not EXEMPLOS:
        print("Nenhum laudo de exemplo encontrado em exemplos/.")
        return 1

    SAIDA.mkdir(exist_ok=True)
    conn = conectar(SAIDA / "datalake.sqlite")
    for caminho in EXEMPLOS:
        processar(caminho, conn)

    # Consolidação final — o que vira número para a ENAP
    r = consultar.resumo(conn)
    print("=" * 70)
    print("DATA LAKE CONSOLIDADO")
    print("=" * 70)
    print(f"  Laudos: {r['total_laudos']} · Municípios: {r['municipios_cobertos']} "
          f"· Aguardando revisão humana: {r['aguardando_revisao_humana']}")
    print("  Distribuição de fósforo no solo:")
    for classe, n in consultar.distribuicao_classe(conn, "fosforo"):
        print(f"    {classe:14} {n}")
    n_pts = consultar.exportar_geojson(conn, SAIDA / "amostras.geojson")
    print(f"  Mapa: {n_pts} pontos exportados -> saida/amostras.geojson")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
