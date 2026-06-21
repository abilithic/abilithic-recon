@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   Abilithic Recon - Windows build
echo ============================================================
echo.

REM --- 1. Cek Python ---------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] "python" tidak ditemukan di PATH.
  echo         Install Python 3.11 atau 3.12 ^(64-bit^) dari:
  echo         https://www.python.org/downloads/windows/
  echo         dan CENTANG "Add python.exe to PATH" saat instalasi.
  goto :fail
)
for /f "delims=" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python terdeteksi: !PYVER!
python -c "import sys;print('Lokasi   :',sys.executable)"
python -c "import sys;sys.exit(0 if sys.maxsize>2**32 else 1)" || (echo [ERROR] Python kamu 32-bit. Butuh 64-bit. & goto :fail)
echo !PYVER! | find /i "WindowsApps" >nul && echo [WARN] Python tampak dari Microsoft Store ^(bisa bermasalah^). Disarankan install dari python.org.
echo.

REM --- 2. Virtual environment ----------------------------------------
if not exist ".venv" (
  echo [1/5] Membuat virtual environment...
  python -m venv .venv
  if errorlevel 1 ( echo [ERROR] Gagal membuat venv. & goto :fail )
)
call ".venv\Scripts\activate.bat"
if errorlevel 1 ( echo [ERROR] Gagal mengaktifkan venv. & goto :fail )

REM --- 3. Dependencies ----------------------------------------------
echo [2/5] Upgrade pip...
python -m pip install --upgrade pip
echo [3/5] Install dependencies ^(PySide6 dll - butuh internet, beberapa menit^)...
python -m pip install -r requirements-dev.txt
if errorlevel 1 ( echo [ERROR] Gagal install dependencies. Periksa koneksi internet. & goto :fail )

REM --- 4. Build -----------------------------------------------------
echo [4/5] Membangun .exe dengan PyInstaller...
python -m PyInstaller abilithic-recon.spec --noconfirm --clean
if errorlevel 1 ( echo [ERROR] PyInstaller gagal. Baca pesan error di atas. & goto :fail )

REM --- 5. Verifikasi -----------------------------------------------
echo [5/5] Verifikasi hasil...
if exist "dist\AbilithicRecon.exe" (
  echo.
  echo ============================================================
  echo   BERHASIL!  File ada di:  dist\AbilithicRecon.exe
  echo ============================================================
) else (
  echo [ERROR] Build selesai tapi dist\AbilithicRecon.exe TIDAK ditemukan.
  goto :fail
)
goto :end

:fail
echo.
echo *** BUILD GAGAL - baca baris [ERROR] di atas untuk tahu penyebabnya. ***

:end
echo.
pause
