@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  ============================================================
echo   SIPA-Bahia AI - servindo o painel em http://localhost:8000
echo   Deixe ESTA JANELA ABERTA durante a apresentacao.
echo   Para parar: feche a janela ou pressione Ctrl+C.
echo  ============================================================
echo.
start "" http://localhost:8000/apresentacao.html
python -m http.server 8000
