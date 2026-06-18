"""
Bioinformática — apoio a sequenciamento/genômica.

Núcleo FUNCIONAL: parser FASTA + estatísticas de sequência (comprimento, %GC, composição).
STUBS para o ferramental especializado (BLAST, Galaxy, Nextflow, GATK), que exige
infraestrutura e bases externas.

Roda OFFLINE.
"""
from __future__ import annotations

from pathlib import Path


def parse_fasta(texto: str) -> list[tuple[str, str]]:
    """Lê FASTA (texto) -> lista de (cabeçalho, sequência)."""
    registros, cab, seq = [], None, []
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if linha.startswith(">"):
            if cab is not None:
                registros.append((cab, "".join(seq)))
            cab, seq = linha[1:], []
        else:
            seq.append(linha.upper())
    if cab is not None:
        registros.append((cab, "".join(seq)))
    return registros


def gc_content(seq: str) -> float:
    seq = seq.upper()
    if not seq:
        return 0.0
    return round(100 * (seq.count("G") + seq.count("C")) / len(seq), 1)


def estatisticas(seq: str) -> dict:
    return {
        "comprimento": len(seq),
        "gc_percent": gc_content(seq),
        "composicao": {b: seq.upper().count(b) for b in "ACGT"},
    }


# ───────── STUBS: ferramental especializado (Fase 3) ─────────

def blast(seq: str, base="nt"):
    """STUB. Alinhamento BLAST contra base de referência (NCBI/local)."""
    raise NotImplementedError("BLAST — integrar via biopython/serviço (Fase 3).")


def pipeline_nextflow(amostras):
    """STUB. Pipeline reprodutível (Nextflow/Galaxy) p/ NGS; variantes via GATK."""
    raise NotImplementedError("Pipeline NGS — Fase 3.")


def _demo():
    fasta = (">amostra_citros_HLB parcial 16S\n"
             "ATGCGTACGTTAGCCGTAGCTAGGCTAGCTAGCTAGGCGCGCGTATATAT\n"
             ">controle_negativo\n"
             "ATATATATATGCGCGCGCATATATGCGCGCATATATATATGCGC\n")
    print("=== BIOINFORMÁTICA ===")
    for cab, seq in parse_fasta(fasta):
        st = estatisticas(seq)
        print(f"  {cab[:30]:30} len={st['comprimento']:>4}  GC={st['gc_percent']}%  {st['composicao']}")
    print("  [BLAST/Galaxy/Nextflow/GATK como stubs — Fase 3]")
    print("Bioinformática: OK")


if __name__ == "__main__":
    _demo()
