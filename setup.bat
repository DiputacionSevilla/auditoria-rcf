@echo off
echo ======================================
echo Instalación Aplicación Auditoría RCF
echo ======================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Por favor instala Python 3.8 o superior.
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version
echo.

REM Crear entorno virtual
echo 📦 Creando entorno virtual...
python -m venv venv

REM Activar entorno virtual
echo ⚙️ Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo 🔄 Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo 📥 Instalando dependencias...
pip install -r requirements.txt

echo.
echo ======================================
echo ✅ Instalación completada con éxito!
echo ======================================
echo.
echo Para ejecutar la aplicación:
echo 1. venv\Scripts\activate
echo 2. streamlit run app.py
echo.
pause