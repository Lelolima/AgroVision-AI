@echo off
REM AgroVision AI - Setup Script para Windows
REM Executar: .\scripts\setup.bat

echo ============================================================
echo          AgroVision AI - Setup Inicial
echo ============================================================
echo.

REM Verificar Python
echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao instalado ou nao no PATH
    echo Faca o download em https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Criar ambiente virtual
echo [2/5] Criando ambiente virtual...
if not exist "venv" (
    python -m venv venv
    echo Ambiente virtual criado com sucesso!
) else (
    echo Ambiente virtual ja existe.
)
echo.

REM Ativar ambiente virtual
echo [3/5] Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo.

REM Instalar dependencias
echo [4/5] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Baixar modelos
echo [5/5] Baixando modelos...
python scripts\download_models.py
echo.

REM Copy .env
if not exist ".env" (
    echo Copiando .env.example para .env...
    copy .env.example .env
    echo Edite .env conforme necessario.
) else (
    echo Arquivo .env ja existe.
)
echo.

echo ============================================================
echo          Setup concluido com sucesso!
echo ============================================================
echo.
echo Para iniciar o servidor:
echo   1. Ative o ambiente: venv\Scripts\activate
echo   2. Execute: python -m agrovision.api.app
echo   3. Acesse: http://localhost:8000
echo.
echo Para executar a demo:
echo   python demo.py
echo.
pause