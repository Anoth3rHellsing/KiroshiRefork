@echo off
REM ======================================================================
REM  Kiroshi Documentation System — All-In-One Installer
REM ======================================================================
setlocal EnableExtensions EnableDelayedExpansion

:: ---------------------------- Elevate to Admin ----------------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: ------------------------------- Variables --------------------------------
set "CURRENT_VERSION=RC-141025-AIO"
set "SRC=%~dp0"
set "DEST=C:\ProgramData\Kiroshi Documentation"
set "VENV=%DEST%\.venv"
set "PYTHON_EXE=%VENV%\Scripts\python.exe"
set "LAUNCH_BASE=Kiroshi Documentation System"
set "DESKTOP_USER=%USERPROFILE%\Desktop"
set "DESKTOP_PUBLIC=%Public%\Desktop"
set "START_MENU_USER=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "START_MENU_ALL=%ProgramData%\Microsoft\Windows\Start Menu\Programs"

echo Kiroshi All-In-One Installer
echo ============================

:: ------------------------ Check Installation State ------------------------
set "INSTALLED_VERSION="
if exist "%DEST%\version.txt" (
    set /p INSTALLED_VERSION=<"%DEST%\version.txt"
) else if exist "%DEST%" (
    set "INSTALLED_VERSION=UNKNOWN"
)

if "!INSTALLED_VERSION!"=="%CURRENT_VERSION%" (
    echo Kiroshi v%CURRENT_VERSION% is already installed.
    echo [1] Repair installation
    echo [2] Uninstall everything ^(including dependencies^)
    echo [3] Exit
    choice /c 123 /n /m "Choose an option: "
    if !errorlevel!==1 goto :Install
    if !errorlevel!==2 goto :Uninstall
    if !errorlevel!==3 exit /b 0
)

if not "!INSTALLED_VERSION!"=="" (
    if not "!INSTALLED_VERSION!"=="%CURRENT_VERSION%" (
        echo Previous version !INSTALLED_VERSION! detected. Upgrading to %CURRENT_VERSION%...
        goto :Upgrade
    )
)

goto :Install

:Upgrade
echo Backing up JSON files...
set "TEMP_JSON_BACKUP=%TEMP%\Kiroshi_JSON_Backup"
if exist "!TEMP_JSON_BACKUP!" rmdir /s /q "!TEMP_JSON_BACKUP!"
mkdir "!TEMP_JSON_BACKUP!"
xcopy "%DEST%\*.json" "!TEMP_JSON_BACKUP!\" /S /Y >nul 2>&1

echo Removing previous installation...
rmdir /s /q "%DEST%"

goto :InstallFiles

:Uninstall
echo Uninstalling Kiroshi Documentation System...
taskkill /IM streamlit.exe /F >nul 2>&1

if exist "%DEST%" rmdir /s /q "%DEST%"
del "%DESKTOP_USER%\%LAUNCH_BASE%.cmd" >nul 2>&1
del "%DESKTOP_PUBLIC%\%LAUNCH_BASE%.cmd" >nul 2>&1
del "%START_MENU_USER%\%LAUNCH_BASE%.cmd" >nul 2>&1
del "%START_MENU_ALL%\%LAUNCH_BASE%.cmd" >nul 2>&1
echo Uninstallation complete.
pause
exit /b 0

:Install
:InstallFiles

:: ----------------------- Ensure Python 64-bit -----------------------------
echo Checking for Python 64-bit ^(required for pyarrow / Streamlit^)...
set "PYTHON_GLOBAL="
for /f "delims=" %%I in ('powershell -NoProfile -Command "(Get-Command python -ErrorAction SilentlyContinue).Path"') do set "PYTHON_GLOBAL=%%I"

set "PYTHON_ARCH="
if defined PYTHON_GLOBAL (
    for /f "delims=" %%A in ('powershell -NoProfile -Command "& { try { $arch = (& '%PYTHON_GLOBAL%' -c 'import struct; print(struct.calcsize(\"P\") * 8)') 2>$null; Write-Output $arch } catch { Write-Output 'error' } }"') do set "PYTHON_ARCH=%%A"
)

if "!PYTHON_ARCH!" neq "64" (
    echo Python 64-bit not found or current Python is not 64-bit.
    echo Downloading and installing Python 3.11 64-bit silently...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
    if exist "%TEMP%\python-installer.exe" (
        start /wait "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        del "%TEMP%\python-installer.exe"
    ) else (
        echo Failed to download Python.
    )

    :: Refresh Path for current session (basic approach)
    for /f "tokens=2*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "SYS_PATH=%%B"
    set "PATH=!SYS_PATH!;%PATH%"
) else (
    echo Python 64-bit is installed.
)

:: ----------------------- Ensure destination folder ------------------------
if not exist "%DEST%" (
    mkdir "%DEST%" || (echo Failed to create "%DEST%" & exit /b 1)
)

echo Copying project files...
set "PSCMD=$src=[IO.Path]::GetFullPath('%SRC%'); $dest='%DEST%'; Copy-Item -Path (Join-Path $src '*') -Destination $dest -Recurse -Force"
powershell -NoProfile -ExecutionPolicy Bypass -Command "%PSCMD%" >nul 2>&1

:: Restore JSONs if upgraded
if exist "!TEMP_JSON_BACKUP!" (
    echo Restoring JSON backups...
    xcopy "!TEMP_JSON_BACKUP!\*.json" "%DEST%\" /S /Y >nul 2>&1
    rmdir /s /q "!TEMP_JSON_BACKUP!"
)

echo %CURRENT_VERSION%>"%DEST%\version.txt"

:: ------------------------------ Create venv -------------------------------
set "PY3=python"
if not exist "%VENV%\Scripts\python.exe" (
    echo Creating virtual environment at "%VENV%" ...
    %PY3% -m venv "%VENV%"
)

:: ----------------------- Pip upgrade & requirements -----------------------
echo Upgrading pip and installing requirements to latest version...
"%PYTHON_EXE%" -m pip install --upgrade pip

:: Ensure required packages for screenshots are explicitly present (README fix)
echo Installing dependencies and screenshot packages (mss, pyautogui, pillow)...
if exist "%DEST%\requirements-latest.txt" (
    "%PYTHON_EXE%" -m pip install --upgrade -r "%DEST%\requirements-latest.txt" mss pyautogui pillow
) else if exist "%DEST%\requirements.txt" (
    "%PYTHON_EXE%" -m pip install --upgrade -r "%DEST%\requirements.txt" mss pyautogui pillow
) else (
    "%PYTHON_EXE%" -m pip install --upgrade streamlit mss pyautogui pillow
)

:: ------------------------- Create .CMD launchers --------------------------
echo Creating launchers...
set "PS1_FILE=%TEMP%\mk_kiroshi_cmd_launchers.ps1"
>"%PS1_FILE%" echo param(^[string]$Dest,^ [string]$Venv,^ [string[]]$Paths^)
>>"%PS1_FILE%" echo $content = @"
>>"%PS1_FILE%" echo @echo off
>>"%PS1_FILE%" echo cd /d ""$Dest""
>>"%PS1_FILE%" echo if exist ".venv\Scripts\streamlit.exe" ^(
>>"%PS1_FILE%" echo ^  start "" ".venv\Scripts\streamlit.exe" run case_documentation_app.py
>>"%PS1_FILE%" echo ^) else ^(
>>"%PS1_FILE%" echo ^  start "" ".venv\Scripts\python.exe" -m streamlit run case_documentation_app.py
>>"%PS1_FILE%" echo ^)
>>"%PS1_FILE%" echo "@
>>"%PS1_FILE%" echo foreach($p in $Paths){
>>"%PS1_FILE%" echo ^  try{
>>"%PS1_FILE%" echo ^    New-Item -ItemType Directory -Path (Split-Path $p) -Force ^| Out-Null
>>"%PS1_FILE%" echo ^    Set-Content -Path $p -Value $content -Encoding ASCII
>>"%PS1_FILE%" echo ^  } catch {}
>>"%PS1_FILE%" echo }

set "P1=%DESKTOP_USER%\%LAUNCH_BASE%.cmd"
set "P2=%DESKTOP_PUBLIC%\%LAUNCH_BASE%.cmd"
set "P3=%START_MENU_USER%\%LAUNCH_BASE%.cmd"
set "P4=%START_MENU_ALL%\%LAUNCH_BASE%.cmd"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1_FILE%" ^
  -Dest "%DEST%" ^
  -Venv "%VENV%" ^
  -Paths "%P1%","%P2%","%P3%","%P4%" >nul 2>&1

if exist "%PS1_FILE%" del "%PS1_FILE%" >nul 2>&1

echo.
echo Installation Complete!
echo You can run Kiroshi from the Desktop shortcut.
pause
exit /b 0