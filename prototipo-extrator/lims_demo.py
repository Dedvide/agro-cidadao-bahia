"""
Demonstração do LIMS (sem API): ciclo completo coleta → laudo oficial emitido.
Imprime a cadeia de custódia e gera o laudo HTML.

Rode:  python lims_demo.py
"""
from pathlib import Path

import lims
from persistencia import conectar
from schema import Laudo, Resultado, TipoAmostra, TipoResultado, TipoSolicitante

AQUI = Path(__file__).parent
DB = AQUI / "saida" / "lims_demo.sqlite"
LAUDOS_DIR = AQUI / "saida" / "laudos"
DB.parent.mkdir(exist_ok=True)
if DB.exists():
    DB.unlink()

conn = conectar(DB)

# 1) Cadastro da amostra (abre a cadeia de custódia)
amostra_id, protocolo = lims.cadastrar_amostra(
    conn, categoria_analise="fertilidade_solo", tipo_amostra="solo",
    municipio="Cruz das Almas", propriedade="Sítio Boa Esperança",
    solicitante_nome="João Pereira dos Santos", solicitante_tipo="agricultura_familiar",
    coletor="Téc. Ana Lima", data_coleta="2026-05-04",
)
print(f"Amostra cadastrada: {protocolo}")

# 2) Trânsito físico da amostra (cada passo registra quem/quando)
lims.avancar_status(conn, amostra_id, "coletada", "Téc. Ana Lima")
lims.avancar_status(conn, amostra_id, "recebida", "Recepção CETAB")
lims.avancar_status(conn, amostra_id, "em_analise", "Lab. de Solos")

# 3) Resultado da análise (o que o extrator IA produziria) → vincula à amostra
laudo = Laudo(
    laudo_id=protocolo, categoria_analise="fertilidade_solo", tipo_amostra=TipoAmostra.solo,
    municipio="Cruz das Almas", solicitante_nome="João Pereira dos Santos",
    solicitante_tipo=TipoSolicitante.agricultura_familiar, data_coleta="2026-05-04",
    laboratorio="CETAB - Lab. de Solos",
    resultados=[
        Resultado(tipo=TipoResultado.quantitativo, analito="ph", valor=5.2),
        Resultado(tipo=TipoResultado.quantitativo, analito="fosforo", valor=8, unidade="mg/dm3"),
        Resultado(tipo=TipoResultado.quantitativo, analito="potassio", valor=35, unidade="mg/dm3"),
    ],
    confianca_geral=0.95,
)
laudo_pk = lims.vincular_laudo(conn, amostra_id, laudo)
print("Resultado lançado e vinculado à amostra.")

# 4) Validação técnica (aprovação pelo responsável)
lims.validar_laudo(conn, laudo_pk, "Dra. Marta Souza (CRQ 12345)")

# 5) Emissão do laudo oficial (com selo de integridade)
numero, caminho = lims.emitir_laudo(conn, laudo_pk, LAUDOS_DIR)
codigo = conn.execute("SELECT codigo_verificacao FROM laudo WHERE id=?", (laudo_pk,)).fetchone()[0]
print(f"Laudo oficial emitido: {numero}  (cód. verificação: {codigo})")
print(f"  documento: {caminho.relative_to(AQUI)}")
print(f"  integridade confere: {lims.verificar_laudo(conn, laudo_pk)}")

# 6) Entrega ao solicitante
lims.entregar(conn, amostra_id, "Portal do Produtor", canal="portal")

# Cadeia de custódia completa
print("\n=== CADEIA DE CUSTÓDIA ===")
for e in lims.custodia(conn, amostra_id):
    obs = f" — {e['observacao']}" if e["observacao"] else ""
    print(f"  {e['data']}  [{e['evento']:14}] {e['responsavel']}{obs}")

status = conn.execute("SELECT status FROM amostra WHERE id=?", (amostra_id,)).fetchone()[0]
print(f"\nStatus final da amostra: {status}")
print("Ciclo coleta → laudo oficial: OK")
conn.close()
