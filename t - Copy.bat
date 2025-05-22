@echo off
REM -------------------------------------------------
REM scaffold.bat
REM Crea estructura exportador-multiia con carpetas y
REM archivos vacíos.
REM -------------------------------------------------

REM 1) Carpeta raíz del proyecto
SET "ROOT=%~dp0exportador-multiia"
IF NOT EXIST "%ROOT%" (
    mkdir "%ROOT%"
)

REM 2) Carpetas internas
mkdir "%ROOT%\src"
mkdir "%ROOT%\src\core"
mkdir "%ROOT%\src\gui"
mkdir "%ROOT%\src\ia"

REM 3) Archivos vacíos (se crean solo si no existen)
REM    Utilizamos type nul > fichero
REM    Después podrás pegar el contenido real.

type nul > "%ROOT%\src\main.py"

REM --- core ---
type nul > "%ROOT%\src\core\__init__.py"
type nul > "%ROOT%\src\core\detectors.py"
type nul > "%ROOT%\src\core\exporter.py"
type nul > "%ROOT%\src\core\tokenizer.py"

REM --- gui ---
type nul > "%ROOT%\src\gui\__init__.py"
type nul > "%ROOT%\src\gui\main_window.py"

REM --- ia ---
type nul > "%ROOT%\src\ia\__init__.py"
type nul > "%ROOT%\src\ia\base.py"
type nul > "%ROOT%\src\ia\openai_client.py"
type nul > "%ROOT%\src\ia\claude_client.py"
type nul > "%ROOT%\src\ia\gemini_client.py"
type nul > "%ROOT%\src\ia\ollama_client.py"

REM 4) Otros archivos raíz
type nul > "%ROOT%\README.md"
echo PySide6>=6.5>> "%ROOT%\requirements.txt"
echo openai>=1.2>>   "%ROOT%\requirements.txt"

REM 5) Fin
echo.
echo Estructura creada en: %ROOT%
cd /d "%ROOT%"
dir /b /s
echo.
pause
