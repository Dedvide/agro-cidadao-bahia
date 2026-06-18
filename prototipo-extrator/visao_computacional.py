"""
Visão Computacional — identificação de doenças/pragas por imagem.

SCAFFOLD: define a interface do classificador, um MODELO PLACEHOLDER (determinístico,
para a demo rodar sem pesos), e a integração com o esquema canônico (vira um Resultado).
Em produção, plugar YOLO / Vision Transformers / Segment Anything treinados com imagens
rotuladas do CETAB — a interface não muda.

Roda OFFLINE (placeholder não requer imagem de verdade nem bibliotecas pesadas).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from schema import Resultado, TipoResultado

# catálogo de alvos que o modelo (real) reconheceria
CLASSES = ["ferrugem", "sigatoka", "mosaico", "vassoura_de_bruxa", "antracnose", "saudavel"]


class ClassificadorImagem(Protocol):
    def classificar(self, caminho: str) -> tuple[str, float]: ...


class ModeloPlaceholder:
    """Determinístico: deriva a classe do nome do arquivo. NÃO é um modelo real."""
    def classificar(self, caminho: str) -> tuple[str, float]:
        h = int(hashlib.sha256(Path(caminho).name.encode()).hexdigest(), 16)
        classe = CLASSES[h % len(CLASSES)]
        conf = 0.70 + (h % 30) / 100  # 0.70–0.99
        return classe, round(conf, 3)


class ModeloYOLO:
    """STUB. Carregar pesos YOLO/Ultralytics e rodar inferência real."""
    def classificar(self, caminho: str) -> tuple[str, float]:
        raise NotImplementedError("Modelo YOLO real — treinar com imagens rotuladas do CETAB (Fase 3).")


def classificar_imagem(caminho: str, modelo: ClassificadorImagem | None = None) -> dict:
    modelo = modelo or ModeloPlaceholder()
    classe, conf = modelo.classificar(caminho)
    # mapeia para o esquema canônico (diagnóstico por imagem)
    resultado = Resultado(
        tipo=TipoResultado.diagnostico,
        alvo=classe,
        resultado_diagnostico="negativo" if classe == "saudavel" else "suspeito",
        metodo="visao_computacional",
    )
    return {"arquivo": Path(caminho).name, "classe": classe, "confianca": conf, "resultado": resultado}


def _demo():
    print("=== VISÃO COMPUTACIONAL (scaffold + modelo placeholder) ===")
    for img in ["folha_citros_001.jpg", "fruto_manga_044.jpg", "microscopia_fungo_007.png"]:
        r = classificar_imagem(img)
        print(f"  {r['arquivo']}: {r['classe']} ({r['confianca']:.0%}) "
              f"-> {r['resultado'].resultado_diagnostico}")
    print("  [placeholder — em produção: YOLO/ViT/SAM com imagens rotuladas do CETAB]")
    print("Visão computacional: OK")


if __name__ == "__main__":
    _demo()
