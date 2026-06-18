@echo off
chcp 65001 > nul
title Agro Cidadão Bahia

echo.
echo  ===============================================
echo   AGRO CIDADÃO BAHIA — Assistente Rural com IA
echo  ===============================================
echo.

:: Verifica variável de ambiente
if "%ANTHROPIC_API_KEY%"=="" (
    echo  [AVISO] Variável ANTHROPIC_API_KEY não definida.
    echo  Defina ela antes de continuar:
    echo    set ANTHROPIC_API_KEY=sk-ant-...
    echo.
    pause
    exit /b 1
)

:: Instala dependências se necessário
if not exist ".venv_cidadao" (
    echo  [1/2] Criando ambiente virtual...
    python -m venv .venv_cidadao
    call .venv_cidadao\Scripts\activate.bat
    echo  [2/2] Instalando dependências...
    pip install -r cidadao\requirements.txt -q
) else (
    call .venv_cidadao\Scripts\activate.bat
)

echo.
echo  Servidor iniciando em: http://localhost:8001
echo  Painel:               http://localhost:8001/
echo  Stats:                http://localhost:8001/stats
echo  Health:               http://localhost:8001/health
echo.
echo  Pressione Ctrl+C para encerrar.
echo.

uvicorn cidadao.main:app --host 0.0.0.0 --port 8001 --reload
