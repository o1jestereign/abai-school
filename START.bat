@echo off
chcp 65001 >nul
title Абай мектебі — 2D Ішкі Навигация (Digital Twin)
cd /d "%~dp0"

echo.
echo ========================================================================
echo        АБАЙ АТЫНДАҒЫ МЕКТЕП — 2D НАВИГАЦИЯ ЖҮЙЕСІ (DIGITAL TWIN)
echo ========================================================================
echo.
echo  [1/2] Жүйе тексерілуде...

set "PYTHON_EXE="

:: 1. Флешканың өз ішіндегі дайын Portable Python-ды тексеру
if exist "%~dp0python_portable\python.exe" (
    set "PYTHON_EXE=%~dp0python_portable\python.exe"
    echo  [+] Флешкадағы дайын Portable Python табылды!
    goto :LAUNCH_PYTHON
)

:: 2. Компьютерде жүйелік Python бар-жоғын тексеру
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    echo  [+] Компьютердің жүйелік Python-ы табылды!
    goto :LAUNCH_PYTHON
)

:: 3. Егер Python табылмаса — интернеттен автоматты түрде өзі жүктеп алады (Auto-download)
echo  [!] Компьютерде Python табылмады.
echo  [!] Қажетті файлдарды автоматты түрде интернеттен жүктеу тексерілуде...
curl.exe --version >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo  [+] Python Portable пакеті жүктелуде (11 MB)...
    if not exist "%~dp0python_portable" mkdir "%~dp0python_portable"
    curl.exe -L -o "%~dp0python_portable.zip" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    if exist "%~dp0python_portable.zip" (
        echo  [+] Файлдар ашылуда...
        tar.exe -xf "%~dp0python_portable.zip" -C "%~dp0python_portable"
        del /f /q "%~dp0python_portable.zip"
        if exist "%~dp0python_portable\python.exe" (
            set "PYTHON_EXE=%~dp0python_portable\python.exe"
            echo  [+] Python сәтті жүктелді және орнатылды!
            goto :LAUNCH_PYTHON
        )
    )
)

:: 4. Егер интернет болмаса — Windows-тың кірістірілген жедел сервері арқылы қосылу (100% Offline)
echo  [+] Windows-тың кірістірілген жедел сервері арқылы қосылуда...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\server.ps1"
if %ERRORLEVEL% equ 0 goto :END

:: 5. Төтенше жағдайда: тікелей браузер арқылы ашу
echo  [+] Жүйе тікелей браузерде ашылуда...
start "" "%~dp0index.html"
goto :END

:LAUNCH_PYTHON
echo  [2/2] Веб-сервер іске қосылуда...
echo.
echo  ========================================================================
echo    СЕРВЕР ҚОСЫЛДЫ! БРАУЗЕР АВТОМАТТЫ ТҮРДЕ АШЫЛАДЫ.
echo    Мекенжай: http://localhost:8765/index.html
echo.
echo    Жұмысты аяқтау үшін осы терезені жапсаңыз болғаны.
echo  ========================================================================
echo.
timeout /t 2 /nobreak >nul
start "" "http://localhost:8765/index.html"
"%PYTHON_EXE%" -m http.server 8765

:END
pause
