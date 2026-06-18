"""
Selo de integridade e código de verificação do laudo (protótipo).

ATENÇÃO: isto é um SELO DE INTEGRIDADE tamper-evident, NÃO uma assinatura legal.
Em produção, a assinatura oficial deve usar certificado ICP-Brasil (carimbo do tempo)
ou a Assinatura Eletrônica gov.br — substituindo a chave HMAC demo por um HSM/cert real.

O que faz:
  - calcula o hash SHA-256 do conteúdo canônico do laudo (tamper-evidence)
  - deriva um código de verificação curto via HMAC (autenticidade com chave do CETAB)
  - permite VERIFICAR depois se o laudo foi alterado
"""
from __future__ import annotations

import hashlib
import hmac

# Em produção: chave em cofre/HSM, nunca no código. Aqui é só demonstração.
CHAVE_DEMO = b"CETAB-PROTOTIPO-CHAVE-NAO-USAR-EM-PRODUCAO"


def selar(conteudo_canonico: str, chave: bytes = CHAVE_DEMO) -> tuple[str, str]:
    """Retorna (hash_sha256, codigo_verificacao)."""
    h = hashlib.sha256(conteudo_canonico.encode("utf-8")).hexdigest()
    assinatura = hmac.new(chave, conteudo_canonico.encode("utf-8"), hashlib.sha256).hexdigest()
    codigo = assinatura[:12].upper()
    return h, codigo


def verificar(conteudo_canonico: str, hash_esperado: str) -> bool:
    """True se o conteúdo não foi alterado (hash confere)."""
    h = hashlib.sha256(conteudo_canonico.encode("utf-8")).hexdigest()
    return hmac.compare_digest(h, hash_esperado)
