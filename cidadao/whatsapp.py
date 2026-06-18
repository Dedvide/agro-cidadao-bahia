import os
from fastapi import Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

from .chat import responder_texto, responder_imagem_url
from .log import registrar

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

BOAS_VINDAS = (
    "Olá! Sou o *Agro Cidadão Bahia* 🌱\n\n"
    "Estou aqui para ajudar agricultores familiares com dúvidas sobre plantio, pragas, "
    "solo, irrigação e mais — de forma gratuita.\n\n"
    "Pode me enviar:\n"
    "• Uma *pergunta* (ex: 'Como combater a mosca-das-frutas?')\n"
    "• Uma *foto* da planta ou lavoura com uma breve descrição\n\n"
    "Como posso ajudar hoje?"
)

PALAVRAS_BOAS_VINDAS = {"oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hello", "hi", "inicio", "início"}


async def webhook(
    Body: str = Form(default=""),
    From: str = Form(default=""),
    NumMedia: str = Form(default="0"),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
    To: str = Form(default=""),
):
    texto = Body.strip()
    municipio = ""

    # detectar se o agricultor informou o município
    # formato esperado: "municipio: Cruz das Almas" ou "estou em Cruz das Almas"
    for prefixo in ["municipio:", "município:", "estou em", "sou de", "moro em"]:
        if prefixo in texto.lower():
            partes = texto.lower().split(prefixo, 1)
            if len(partes) > 1:
                municipio = partes[1].strip().split("\n")[0].strip().title()
                break

    twiml = MessagingResponse()

    # boas-vindas
    if texto.lower() in PALAVRAS_BOAS_VINDAS or not texto:
        twiml.message(BOAS_VINDAS)
        return Response(content=str(twiml), media_type="application/xml")

    try:
        auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None

        if NumMedia and int(NumMedia) > 0 and MediaUrl0:
            resultado = await responder_imagem_url(
                url=MediaUrl0,
                descricao=texto,
                municipio=municipio,
                twilio_auth=auth,
            )
        else:
            resultado = await responder_texto(texto, municipio)

        resposta = resultado["resposta"]
        tipo = resultado["tipo"]

    except Exception as e:
        resposta = (
            "Desculpe, tive um problema técnico momentâneo. "
            "Tente novamente em alguns instantes ou envie sua dúvida de outra forma."
        )
        tipo = "erro"

    registrar("whatsapp", municipio, texto, resposta, tipo)
    twiml.message(resposta)
    return Response(content=str(twiml), media_type="application/xml")
