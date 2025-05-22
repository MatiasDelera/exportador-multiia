@echo off
REM ─────────────────────────────────────────────
REM  setup_run.bat
REM  • Sin argumentos ...... ⇒ instala deps y ejecuta GUI
REM  • build ................ ⇒ genera .exe con PyInstaller
REM ─────────────────────────────────────────────

SET PROJECT_DIR=%~dp0
SET VENV_DIR=%PROJECT_DIR%venv
SET REQ_FILE=%PROJECT_DIR%requirements.txt

REM 1) Crear entorno virtual si no existe
IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo [INFO] Creando entorno virtual...
    python -m venv "%VENV_DIR%"
)

REM 2) Activar entorno virtual
call "%VENV_DIR%\Scripts\activate.bat"

REM 3) Instalar / actualizar dependencias
IF EXIST "%REQ_FILE%" (
    echo [INFO] Instalando dependencias de requirements.txt...
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -r "%REQ_FILE%"
) ELSE (
    echo [WARN] No se encontró requirements.txt
)

REM 4) ¿Compilar o ejecutar?
IF /I "%1"=="build" (
    echo [INFO] Generando ejecutable...
    REM Limpieza previa
    if exist build rd /s /q build
    if exist dist rd /s /q dist
    if exist exportador-multiia.spec del exportador-multiia.spec
    pyinstaller --noconfirm --clean --onefile --windowed ^
        -n exportador-multiia "%PROJECT_DIR%src\main.py"

    IF EXIST "%PROJECT_DIR%dist\exportador-multiia.exe" (
        echo [OK] EXE generado en dist\exportador-multiia.exe
    ) ELSE (
        echo [ERR] La compilación falló. Revisa el log anterior.
    )
) ELSE (
    echo [INFO] Lanzando aplicación...
    python -m src.main
)

echo.
pause
