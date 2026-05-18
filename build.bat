@echo off
REM Script para gerar o executavel do PDV usando PyInstaller
REM Execute uma unica vez: pip install -r requirements.txt

echo ============================================
echo Gerando executavel PDV Simples...
echo ============================================

pyinstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name "PDV-Simples" ^
  --collect-all customtkinter ^
  --collect-all reportlab ^
  --hidden-import win32print ^
  --hidden-import win32ui ^
  main.py

echo.
echo ============================================
echo Executavel gerado em: dist\PDV-Simples.exe
echo ============================================
pause
