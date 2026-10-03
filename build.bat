@echo off
REM Script para gerar o executavel do PDV usando PyInstaller
REM ANTES de rodar pela primeira vez execute: pip install -r requirements.txt

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
  --collect-all darkdetect ^
  --hidden-import win32print ^
  --hidden-import win32ui ^
  --hidden-import pywintypes ^
  --hidden-import packaging ^
  main.py

echo.
if %ERRORLEVEL% == 0 (
    echo ============================================
    echo Executavel gerado com SUCESSO em: dist\PDV-Simples.exe
    echo ============================================
) else (
    echo ============================================
    echo FALHA ao gerar o executavel. Verifique os erros acima.
    echo ============================================
)
pause
