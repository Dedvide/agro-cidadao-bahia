import os
import base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .chat import responder_texto, responder_imagem
from .log import init_db, registrar, stats
from . import whatsapp as _whatsapp

app = FastAPI(title="Agro Cidadão Bahia", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PAINEL_DIR = Path(__file__).parent.parent / "painel"

app.mount("/static", StaticFiles(directory=str(PAINEL_DIR)), name="static")

init_db()


@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = PAINEL_DIR / "cidadao.html"
    return html_path.read_text(encoding="utf-8")


@app.post("/chat")
async def chat(
    pergunta: str = Form(...),
    municipio: str = Form(default=""),
    imagem: UploadFile = File(default=None),
):
    try:
        if imagem and imagem.filename:
            conteudo = await imagem.read()
            imagem_b64 = base64.b64encode(conteudo).decode()
            resultado = await responder_imagem(imagem_b64, pergunta, municipio)
        else:
            resultado = await responder_texto(pergunta, municipio)

        registrar("web", municipio, pergunta, resultado["resposta"], resultado["tipo"])
        return JSONResponse(resultado)

    except Exception as e:
        return JSONResponse(
            {"resposta": "Ocorreu um erro. Tente novamente.", "tipo": "erro", "detalhe": str(e)},
            status_code=500,
        )


@app.post("/whatsapp")
async def whatsapp(
    Body: str = Form(default=""),
    From: str = Form(default=""),
    NumMedia: str = Form(default="0"),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
    To: str = Form(default=""),
):
    return await _whatsapp.webhook(
        Body=Body,
        From=From,
        NumMedia=NumMedia,
        MediaUrl0=MediaUrl0,
        MediaContentType0=MediaContentType0,
        To=To,
    )


@app.get("/stats")
async def estatisticas():
    return JSONResponse(stats())


@app.get("/biblioteca", response_class=HTMLResponse)
async def biblioteca():
    html_path = PAINEL_DIR / "biblioteca.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {"status": "ok", "servico": "Agro Cidadão Bahia"}
