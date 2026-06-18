"""Teste offline: importa um export de instrumento (qPCR) para o esquema canônico."""
from pathlib import Path

import instrumentos
from interpretar import interpretar_resultado

AQUI = Path(__file__).parent
arquivo = AQUI / "exemplos" / "instrumento_qpcr.csv"

resultados = instrumentos.importar("qpcr_csv", arquivo)
print(f"Importados {len(resultados)} resultados do instrumento (qPCR):")
print("-" * 60)
for r in resultados:
    it = interpretar_resultado("diagnostico_molecular", r)
    flag = "!" if it.alerta else " "
    print(f" {flag} {it.rotulo:10} {it.valor_exibicao:18} [{it.classe}]"
          + (f" -> {it.recomendacao}" if it.recomendacao else ""))
print("-" * 60)
assert resultados[0].alvo == "hlb" and resultados[0].ct == 27.4
print("Adaptador de instrumento (qPCR -> esquema canônico): OK")
