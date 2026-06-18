"""
Gera os dados do PAINEL LIMS (sem API): amostras em vários estágios do ciclo,
emite laudos para as concluídas e exporta painel/lims.json + painel/laudos/.

Rode:  python gerar_lims_demo.py
Depois:  cd ../painel ; python -m http.server 8000 ; abra http://localhost:8000/lims.html
"""
from pathlib import Path

import lims
from persistencia import conectar
from schema import Laudo, Resultado, TipoAmostra, TipoResultado, TipoSolicitante

AQUI = Path(__file__).parent
PAINEL = AQUI.parent / "painel"
LAUDOS_DIR = PAINEL / "laudos"
DB = AQUI / "saida" / "lims_painel.sqlite"
DB.parent.mkdir(exist_ok=True)
PAINEL.mkdir(exist_ok=True)
if DB.exists():
    DB.unlink()

Q = TipoResultado.quantitativo
D = TipoResultado.diagnostico
conn = conectar(DB)


def nova_amostra(cat, amostra, mun, nome, sol, coletor, data):
    return lims.cadastrar_amostra(
        conn, categoria_analise=cat, tipo_amostra=amostra, municipio=mun,
        solicitante_nome=nome, solicitante_tipo=sol, coletor=coletor, data_coleta=data,
    )


def laudo_solo(protocolo, mun, nome, sol, ph, p, k):
    return Laudo(
        laudo_id=protocolo, categoria_analise="fertilidade_solo", tipo_amostra=TipoAmostra.solo,
        municipio=mun, solicitante_nome=nome, solicitante_tipo=sol, data_coleta="2026-05-04",
        laboratorio="CETAB - Lab. de Solos",
        resultados=[
            Resultado(tipo=Q, analito="ph", valor=ph),
            Resultado(tipo=Q, analito="fosforo", valor=p, unidade="mg/dm3"),
            Resultado(tipo=Q, analito="potassio", valor=k, unidade="mg/dm3"),
        ],
        confianca_geral=0.95,
    )


# 1) CONCLUÍDA e entregue (laudo emitido) ──────────────────────────────
aid, prot = nova_amostra("fertilidade_solo", "solo", "Cruz das Almas",
                         "João Pereira", TipoSolicitante.agricultura_familiar, "Téc. Ana Lima", "2026-05-04")
for s in ["coletada", "recebida", "em_analise"]:
    lims.avancar_status(conn, aid, s, "Téc. Ana Lima")
pk = lims.vincular_laudo(conn, aid, laudo_solo(prot, "Cruz das Almas", "João Pereira",
                                               TipoSolicitante.agricultura_familiar, 5.2, 8, 35))
lims.validar_laudo(conn, pk, "Dra. Marta Souza (CRQ 12345)")
lims.emitir_laudo(conn, pk, LAUDOS_DIR)
lims.entregar(conn, aid, "Portal do Produtor")

# 2) APROVADA, aguardando emissão ──────────────────────────────────────
aid, prot = nova_amostra("diagnostico_molecular", "foliar", "Governador Mangabeira",
                         "Sítio Citrolândia", TipoSolicitante.produtor_rural, "Téc. Caio", "2026-05-10")
for s in ["coletada", "recebida", "em_analise"]:
    lims.avancar_status(conn, aid, s, "Téc. Caio")
laudo_hlb = Laudo(laudo_id=prot, categoria_analise="diagnostico_molecular", tipo_amostra=TipoAmostra.foliar,
                  municipio="Governador Mangabeira", solicitante_tipo=TipoSolicitante.produtor_rural,
                  data_coleta="2026-05-10", laboratorio="CETAB - Biologia Molecular",
                  resultados=[Resultado(tipo=D, alvo="hlb", resultado_diagnostico="positivo", ct=27.4, metodo="qPCR")],
                  confianca_geral=0.95)
pk = lims.vincular_laudo(conn, aid, laudo_hlb)
lims.validar_laudo(conn, pk, "Dr. Pedro Anjos")

# 3) AGUARDANDO VALIDAÇÃO (laudo lançado, não aprovado) ────────────────
aid, prot = nova_amostra("monitoramento_pragas", "inseto", "Sao Felix",
                         "Fazenda Goiabal", TipoSolicitante.produtor_rural, "Téc. Bia", "2026-05-15")
for s in ["coletada", "recebida", "em_analise"]:
    lims.avancar_status(conn, aid, s, "Téc. Bia")
laudo_mosca = Laudo(laudo_id=prot, categoria_analise="monitoramento_pragas", tipo_amostra=TipoAmostra.inseto,
                    municipio="Sao Felix", solicitante_tipo=TipoSolicitante.produtor_rural,
                    data_coleta="2026-05-15", laboratorio="CETAB - Ecologia Química",
                    resultados=[Resultado(tipo=TipoResultado.identificacao, taxon="Ceratitis capitata",
                                          contagem=14, estagio="adulto")],
                    confianca_geral=0.95)
lims.vincular_laudo(conn, aid, laudo_mosca)

# 4) EM ANÁLISE ────────────────────────────────────────────────────────
aid, prot = nova_amostra("analise_agua", "agua", "Cachoeira",
                         "Prefeitura de Cachoeira", TipoSolicitante.prefeitura, "Téc. Davi", "2026-05-20")
for s in ["coletada", "recebida", "em_analise"]:
    lims.avancar_status(conn, aid, s, "Téc. Davi")

# 5) RECEBIDA ──────────────────────────────────────────────────────────
aid, prot = nova_amostra("residuos_agrotoxicos", "fruto", "Muritiba",
                         "Coop. Recôncavo", TipoSolicitante.cooperativa, "Téc. Elis", "2026-05-22")
for s in ["coletada", "recebida"]:
    lims.avancar_status(conn, aid, s, "Téc. Elis")

# 6) CADASTRADA (recém-entrada) ────────────────────────────────────────
nova_amostra("qualidade_alimentos", "mel", "Cruz das Almas",
             "Coop. Apicultores", TipoSolicitante.cooperativa, "Téc. Ana Lima", "2026-05-25")


dados = lims.exportar_web(conn, PAINEL / "lims.json")
conn.close()

r = dados["resumo"]
print(f"Painel LIMS gerado em {PAINEL.name}/lims.json")
print(f"  {r['total']} amostras · fila de validação: {r['fila_validacao']} · "
      f"aguardando emissão: {r['aguardando_emissao']} · emitidos: {r['emitidos']} · entregues: {r['entregues']}")
print(f"  Por status: {r['por_status']}")
print("\nVisualizar:  cd ../painel ; python -m http.server 8000 ; abra http://localhost:8000/lims.html")
