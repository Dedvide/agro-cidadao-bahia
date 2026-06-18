"""Popula o CRM com dados ABC+ (10 municípios reais) — propriedades, produtores, visitas."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "prototipo-extrator"))
from municipios_bioma import CULTURAS, todos, bioma_de  # noqa: E402

import crm_repo  # noqa: E402

if crm_repo.CRM_DB.exists():
    crm_repo.CRM_DB.unlink()

PROP_POR_MUNICIPIO = 6
TECNICO = "Téc. Ana Lima"
ids_por_municipio = {}

for mun, bioma in todos():
    prod = crm_repo.cadastrar_produtor({
        "documento": f"000.000.{abs(hash(mun)) % 1000:03d}-00", "nome": f"Cooperativa de {mun}",
        "tipo": "cooperativa", "municipio": mun, "telefone": "(00) 0000-0000"})
    culturas = CULTURAS[bioma]
    ids = []
    for k in range(PROP_POR_MUNICIPIO):
        p = crm_repo.cadastrar_propriedade({
            "nome": f"Propriedade {k+1} — {mun}", "produtor_id": prod["id"], "municipio": mun,
            "area_ha": 20 + k * 35, "cultura_principal": culturas[k % len(culturas)]})
        ids.append(p["id"])
    ids_por_municipio[mun] = ids

# Carteira do técnico Ana: visitas nas 2 primeiras propriedades de cada município (algumas pendentes)
for mun, ids in ids_por_municipio.items():
    for j, pid in enumerate(ids[:2]):
        crm_repo.registrar_atendimento({
            "propriedade_id": pid, "tecnico": TECNICO, "data": "2026-04-20", "tipo": "visita",
            "problema": "Diagnóstico inicial / coleta de solo", "orientacao": "Plano técnico ABC+",
            "retorno_previsto": "2026-06-20", "status": "concluido" if j == 0 else "aberto"})

# Prontuário rico: propriedade em Itabuna (tem diagnóstico molecular HLB no Data Lake)
itabuna = ids_por_municipio.get("Itabuna", [None])[0]
if itabuna:
    crm_repo.registrar_atendimento({"propriedade_id": itabuna, "tecnico": TECNICO, "data": "2026-04-15",
        "tipo": "coleta", "problema": "Suspeita de HLB (greening) no cacau/citros",
        "orientacao": "Coletar amostra para qPCR", "retorno_previsto": "2026-05-15", "status": "aberto"})
    crm_repo.abrir_ocorrencia({"propriedade_id": itabuna, "tipo": "foco_hlb",
        "descricao": "Diagnóstico molecular POSITIVO — notificar ADAB", "data": "2026-04-16", "status": "aberta"})

n_prop = len(crm_repo.listar_propriedades())
print(f"CRM ABC+ seed: {len(ids_por_municipio)} municípios · {n_prop} propriedades · "
      f"{len(crm_repo.listar_atendimentos())} atendimentos")
